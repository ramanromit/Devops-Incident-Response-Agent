"""
Agent Triage Routes
Provides endpoints for executing agent triage interactively with full trace and SSE streaming.
"""

import json
import asyncio
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any

from scenarios.loader import load_scenario
from server.agent.agent import IncidentResponseAgent
from server.tools.telemetry_sandbox import TelemetrySandbox
from server.agent.llm_client import get_llm_client

router = APIRouter(prefix="/api/agent", tags=["Agent"])


class TriageRequest(BaseModel):
    scenario_id: str
    provider: Optional[str] = "mock"
    max_steps: Optional[int] = 8


@router.post("/triage")
def run_triage(request: TriageRequest):
    """
    Runs autonomous agent triage synchronously and returns full result and report.
    """
    try:
        scenario = load_scenario(request.scenario_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Scenario '{request.scenario_id}' not found")

    sandbox = TelemetrySandbox(scenario)
    client = get_llm_client(request.provider)
    agent = IncidentResponseAgent(scenario=scenario, sandbox=sandbox, llm_client=client)

    result = agent.run_investigation(max_steps=request.max_steps or 8)
    return result.model_dump()


@router.get("/triage/stream")
async def stream_triage(
    scenario_id: str = Query(..., description="Scenario ID to investigate"),
    provider: Optional[str] = Query("mock", description="LLM provider: mock, gemini, openai"),
):
    """
    Server-Sent Events (SSE) stream yielding step-by-step agent thoughts, tool calls, and final diagnosis in real time.
    """
    try:
        scenario = load_scenario(scenario_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Scenario not found")

    async def event_generator():
        sandbox = TelemetrySandbox(scenario)
        client = get_llm_client(provider)
        agent = IncidentResponseAgent(scenario=scenario, sandbox=sandbox, llm_client=client)

        step_queue = asyncio.Queue()

        def on_step_sync(step):
            step_queue.put_nowait(step)

        # Run agent in background thread or loop
        loop = asyncio.get_event_loop()
        agent_future = loop.run_in_executor(None, agent.run_investigation, 8, on_step_sync)

        # Stream steps as they arrive
        while not agent_future.done() or not step_queue.empty():
            try:
                step = await asyncio.wait_for(step_queue.get(), timeout=0.1)
                yield f"data: {json.dumps({'event': 'step', 'data': step.model_dump()})}\n\n"
            except asyncio.TimeoutError:
                continue

        result = await agent_future
        yield f"data: {json.dumps({'event': 'complete', 'data': result.model_dump()})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

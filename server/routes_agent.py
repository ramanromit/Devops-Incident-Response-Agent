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
from evaluation.trace_recorder import TraceRecorder
from evaluation.scorer import DeterministicScorer

router = APIRouter(prefix="/api/agent", tags=["Agent"])


class TriageRequest(BaseModel):
    scenario_id: str
    provider: Optional[str] = "mock"
    max_steps: Optional[int] = 8


@router.post("/triage")
def run_triage(request: TriageRequest):
    """
    Runs autonomous agent triage synchronously and returns full result, report, and evaluation scorecard.
    """
    try:
        scenario = load_scenario(request.scenario_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Scenario '{request.scenario_id}' not found")

    # Resolve LLM provider — surfaces explicit errors for misconfigured providers
    try:
        client = get_llm_client(request.provider)
    except (ValueError, ImportError) as e:
        raise HTTPException(status_code=400, detail=str(e))

    sandbox = TelemetrySandbox(scenario)
    recorder = TraceRecorder(
        scenario,
        provider=getattr(client, "provider_name", request.provider or "mock"),
        model_name=getattr(client, "model", getattr(client, "model_name", None)),
    )
    agent = IncidentResponseAgent(scenario=scenario, sandbox=sandbox, llm_client=client)

    def on_step_record(step):
        recorder.record_step(step.model_dump())

    try:
        result = agent.run_investigation(max_steps=request.max_steps or 8, step_callback=on_step_record)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Triage execution failed with provider '{request.provider}': {str(e)}")

    trace_path = recorder.finalize(result)
    eval_result = DeterministicScorer.grade_scenario(
        scenario=scenario,
        execution_result=result,
        trace_path=trace_path,
    )

    response_data = result.model_dump()
    response_data["provider"] = request.provider
    response_data["model_name"] = getattr(client, "model", getattr(client, "model_name", None))
    response_data["evaluation"] = eval_result.model_dump()
    return response_data


@router.get("/triage/stream")
async def stream_triage(
    scenario_id: str = Query(..., description="Scenario ID to investigate"),
    provider: Optional[str] = Query("mock", description="LLM provider: mock, gemini, groq, openai"),
):
    """
    Server-Sent Events (SSE) stream yielding step-by-step agent thoughts, tool calls, and final diagnosis in real time.
    """
    try:
        scenario = load_scenario(scenario_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Scenario not found")

    try:
        client = get_llm_client(provider)
    except (ValueError, ImportError) as e:
        raise HTTPException(status_code=400, detail=str(e))

    async def event_generator():
        sandbox = TelemetrySandbox(scenario)
        recorder = TraceRecorder(
            scenario,
            provider=getattr(client, "provider_name", provider or "mock"),
            model_name=getattr(client, "model", getattr(client, "model_name", None)),
        )
        agent = IncidentResponseAgent(scenario=scenario, sandbox=sandbox, llm_client=client)


        step_queue = asyncio.Queue()

        def on_step_sync(step):
            recorder.record_step(step.model_dump())
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

        try:
            result = await agent_future
            trace_path = recorder.finalize(result)
            eval_result = DeterministicScorer.grade_scenario(
                scenario=scenario,
                execution_result=result,
                trace_path=trace_path,
            )
            complete_data = result.model_dump()
            complete_data["provider"] = provider
            complete_data["model_name"] = getattr(client, "model", getattr(client, "model_name", None))
            complete_data["evaluation"] = eval_result.model_dump()
            yield f"data: {json.dumps({'event': 'complete', 'data': complete_data})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'event': 'error', 'data': {'error': str(e), 'provider': provider}})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

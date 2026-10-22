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
from server.tools.tool_definitions import SRE_TOOLS, LIVE_SRE_TOOLS
from server.tools.live_adapter import LiveOrderFlowAdapter, LiveTelemetrySandbox, create_live_scenario
from server.agent.llm_client import get_llm_client
from server.config import LIVE_DEMO_BASE_URL
from evaluation.trace_recorder import TraceRecorder
from evaluation.scorer import DeterministicScorer

router = APIRouter(prefix="/api/agent", tags=["Agent"])


class TriageRequest(BaseModel):
    scenario_id: str
    provider: Optional[str] = "mock"
    max_steps: Optional[int] = 8


class LiveTriageRequest(BaseModel):
    provider: Optional[str] = "mock"
    max_steps: Optional[int] = 8
    target_url: Optional[str] = None


@router.get("/live-target/status")
def get_live_target_status(target_url: Optional[str] = None):
    """
    Checks connection to the live OrderFlow target application.
    Returns status, active release version, and component health.
    """
    adapter = LiveOrderFlowAdapter(base_url=target_url or LIVE_DEMO_BASE_URL)
    health = adapter.check_health()
    is_connected = health.get("status") != "error"
    return {
        "connected": is_connected,
        "target_url": adapter.base_url,
        "health": health,
    }


@router.post("/live-target/fault/{action}")
def control_live_fault(action: str, target_url: Optional[str] = None, payload: Optional[Dict[str, Any]] = None):
    """
    Utility control proxy for OrderFlow fault injection and reset (for testing & demo convenience).
    Does NOT affect or bias agent reasoning.
    """
    base_url = (target_url or LIVE_DEMO_BASE_URL).rstrip("/")
    import httpx

    endpoint_map = {
        "database": "/api/control/inject/database",
        "latency": "/api/control/inject/latency",
        "faulty-release": "/api/control/inject/faulty-release",
        "reset": "/api/control/reset",
        "traffic-toggle": "/api/control/traffic/toggle",
    }
    rel_path = endpoint_map.get(action)
    if not rel_path:
        raise HTTPException(status_code=400, detail=f"Invalid action '{action}'. Options: {list(endpoint_map.keys())}")

    try:
        with httpx.Client(base_url=base_url, timeout=5.0) as client:
            res = client.post(rel_path, json=payload or {})
            return res.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to communicate with OrderFlow control endpoint: {str(e)}")


@router.post("/live-triage")
def run_live_triage(request: LiveTriageRequest):
    """
    Runs autonomous agent triage against the running OrderFlow target application.
    Executes live tool calling, records traces, and produces an evidence-backed diagnostic report.
    """
    adapter = LiveOrderFlowAdapter(base_url=request.target_url or LIVE_DEMO_BASE_URL)
    health = adapter.check_health()
    if health.get("status") == "error":
        raise HTTPException(
            status_code=503,
            detail=f"Cannot reach OrderFlow target: {health.get('message')}. Ensure OrderFlow backend is running on {adapter.base_url}."
        )

    scenario = create_live_scenario(health_data=health)

    try:
        client = get_llm_client(request.provider)
    except (ValueError, ImportError) as e:
        raise HTTPException(status_code=400, detail=str(e))

    sandbox = LiveTelemetrySandbox(scenario=scenario, adapter=adapter)
    recorder = TraceRecorder(
        scenario,
        provider=getattr(client, "provider_name", request.provider or "mock"),
        model_name=getattr(client, "model", getattr(client, "model_name", None)),
    )
    agent = IncidentResponseAgent(
        scenario=scenario,
        sandbox=sandbox,
        llm_client=client,
        available_tools=LIVE_SRE_TOOLS,
    )

    def on_step_record(step):
        recorder.record_step(step.model_dump())

    try:
        result = agent.run_investigation(max_steps=request.max_steps or 8, step_callback=on_step_record)
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Live triage execution failed with provider '{request.provider}': {str(e)}"
        )

    trace_path = recorder.finalize(result)
    eval_result = DeterministicScorer.grade_scenario(
        scenario=scenario,
        execution_result=result,
        trace_path=trace_path,
    )

    response_data = result.model_dump()
    response_data["provider"] = request.provider
    response_data["model_name"] = getattr(client, "model", getattr(client, "model_name", None))
    response_data["trace_path"] = trace_path
    response_data["evaluation"] = eval_result.model_dump()
    response_data["is_live"] = True
    response_data["target_url"] = adapter.base_url
    return response_data


@router.post("/triage")
def run_triage(request: TriageRequest):
    """
    Runs autonomous agent triage synchronously and returns full result, report, and evaluation scorecard.
    Also transparently routes scenario_id='live' to live triage.
    """
    if request.scenario_id in ("live", "live_orderflow_investigation"):
        return run_live_triage(LiveTriageRequest(provider=request.provider, max_steps=request.max_steps))

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

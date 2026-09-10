"""
Evaluation Harness Routes
Provides API endpoints for running evaluations and retrieving historical scorecards and traces.
"""

import json
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from scenarios.loader import load_all_scenarios, load_scenario
from evaluation.run_eval import run_batch_evaluation, RESULTS_DIR
from evaluation.trace_recorder import TRACES_DIR

router = APIRouter(prefix="/api/evaluation", tags=["Evaluation"])


class EvaluationRunRequest(BaseModel):
    scenario_id: Optional[str] = None
    provider: Optional[str] = "mock"


@router.post("/run")
def trigger_evaluation(request: EvaluationRunRequest):
    """
    Triggers batch or single deterministic evaluation.
    """
    try:
        if request.scenario_id:
            scenarios = [load_scenario(request.scenario_id)]
        else:
            scenarios = load_all_scenarios()

        summary = run_batch_evaluation(scenarios, provider=request.provider)
        return summary.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/latest")
def get_latest_results():
    """
    Returns the latest evaluation scorecard summary.
    """
    json_path = RESULTS_DIR / "latest_run.json"
    if not json_path.exists():
        raise HTTPException(status_code=404, detail="No evaluation results found. Run an evaluation first.")
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


@router.get("/traces")
def list_traces():
    """
    Lists all saved trace files.
    """
    if not TRACES_DIR.exists():
        return []
    traces = []
    for p in sorted(TRACES_DIR.glob("*.json"), reverse=True):
        traces.append({"filename": p.name, "size_bytes": p.stat().st_size})
    return traces


@router.get("/traces/{filename}")
def get_trace_detail(filename: str):
    """
    Retrieves full auditable trace JSON for a specific run.
    """
    path = TRACES_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Trace '{filename}' not found")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

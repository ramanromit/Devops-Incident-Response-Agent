"""
Scenario Routes
Provides REST endpoints for querying scenario definitions.
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from scenarios.loader import load_all_scenarios, load_scenario, get_scenario_summaries

router = APIRouter(prefix="/api/scenarios", tags=["Scenarios"])


@router.get("", response_model=List[Dict[str, Any]])
def list_scenarios():
    """Returns metadata summaries for all 18 incident scenarios."""
    return get_scenario_summaries()


@router.get("/{scenario_id}")
def get_scenario_detail(scenario_id: str):
    """Returns full scenario configuration including mock telemetry and ground truth."""
    try:
        scenario = load_scenario(scenario_id)
        return scenario.model_dump()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

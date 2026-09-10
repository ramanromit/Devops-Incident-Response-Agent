"""
Scenario Bank Loader
Loads, validates, and indexes scenario definitions from YAML files.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional
import yaml
from pydantic import ValidationError

from scenarios.schema import Scenario

DEFINITIONS_DIR = Path(__file__).resolve().parent / "definitions"


def get_scenario_paths() -> List[Path]:
    """Returns sorted list of YAML files in the definitions directory."""
    if not DEFINITIONS_DIR.exists():
        DEFINITIONS_DIR.mkdir(parents=True, exist_ok=True)
    return sorted(
        [p for p in DEFINITIONS_DIR.glob("*.yaml")]
        + [p for p in DEFINITIONS_DIR.glob("*.yml")]
    )


def load_scenario(scenario_id: str) -> Scenario:
    """
    Loads and validates a single scenario by its ID or filename stem.
    """
    paths = get_scenario_paths()
    for path in paths:
        if path.stem == scenario_id or path.name == scenario_id:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            try:
                return Scenario(**data)
            except ValidationError as e:
                raise ValueError(f"Scenario '{scenario_id}' failed validation: {e}")

    raise FileNotFoundError(f"Scenario with ID '{scenario_id}' not found in {DEFINITIONS_DIR}")


def load_all_scenarios() -> List[Scenario]:
    """
    Loads and validates all scenarios in the definitions directory.
    """
    scenarios = []
    for path in get_scenario_paths():
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        try:
            scenarios.append(Scenario(**data))
        except ValidationError as e:
            print(f"Warning: Failed to load {path.name}: {e}")
    return scenarios


def get_scenario_summaries() -> List[Dict]:
    """
    Returns lightweight metadata summaries for API and UI catalog browsing.
    """
    summaries = []
    for s in load_all_scenarios():
        summaries.append(
            {
                "id": s.id,
                "title": s.title,
                "category": s.category,
                "severity": s.severity,
                "description": s.description,
                "service": s.alert.service,
                "alert_metric": s.alert.metric,
                "alert_message": s.alert.message,
                "required_tools": s.ground_truth.required_tools,
            }
        )
    return summaries

"""
Trace Recorder
Captures, structures, and serializes auditable agent execution traces.
"""

import os
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from scenarios.schema import Scenario
from server.agent.models import AgentExecutionResult

RESULTS_DIR = Path(__file__).resolve().parent.parent / "evaluation_results"
TRACES_DIR = RESULTS_DIR / "traces"


class TraceRecorder:
    """
    Captures complete auditable JSON traces of agent steps, tool calls, and reports.
    """

    def __init__(
        self,
        scenario: Scenario,
        provider: Optional[str] = None,
        model_name: Optional[str] = None,
    ):
        self.scenario = scenario
        self.trace_data: Dict[str, Any] = {
            "scenario_id": scenario.id,
            "scenario_title": scenario.title,
            "scenario_category": scenario.category,
            "severity": scenario.severity,
            "alert": scenario.alert.model_dump(),
            "started_at": datetime.now(timezone.utc).isoformat(),
            "provider": provider or "mock",
            "model_name": model_name,
            "steps": [],
            "report": None,
            "duration_seconds": 0.0,
            "total_steps": 0,
            "success": False,
        }

    def record_step(self, step_dict: Dict[str, Any]):
        self.trace_data["steps"].append(step_dict)

    def finalize(self, execution_result: AgentExecutionResult) -> str:
        """
        Finalizes the trace record and saves it to disk as a JSON artifact.
        Returns the absolute path to the saved trace file.
        """
        self.trace_data["completed_at"] = datetime.now(timezone.utc).isoformat()
        self.trace_data["duration_seconds"] = execution_result.duration_seconds
        self.trace_data["success"] = execution_result.success
        self.trace_data["total_steps"] = execution_result.total_steps
        if getattr(execution_result, "provider", None):
            self.trace_data["provider"] = execution_result.provider
        if getattr(execution_result, "model_name", None):
            self.trace_data["model_name"] = execution_result.model_name
        if execution_result.report:
            self.trace_data["report"] = execution_result.report.model_dump()
        if execution_result.error:
            self.trace_data["error"] = execution_result.error

        TRACES_DIR.mkdir(parents=True, exist_ok=True)
        filename = f"{self.scenario.id}_{int(datetime.now(timezone.utc).timestamp())}.json"
        save_path = TRACES_DIR / filename

        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(self.trace_data, f, indent=2)

        return str(save_path)


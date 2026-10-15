"""
Agent Data Models
Defines Pydantic models for agent reasoning steps, diagnostic reports, and execution results.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class AgentStep(BaseModel):
    step_number: int
    thought: str
    tool_name: Optional[str] = None
    tool_arguments: Optional[Dict[str, Any]] = None
    tool_output: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None


class DiagnosticReport(BaseModel):
    incident_summary: str
    identified_root_cause: str
    root_cause_category: str
    evidence_gathered: List[str] = Field(default_factory=list)
    remediation_plan: List[str] = Field(default_factory=list)
    preventative_measures: List[str] = Field(default_factory=list)
    safety_boundary_compliance: bool = True  # Strict SRE safety rule: no autonomous destructive commands


class AgentExecutionResult(BaseModel):
    scenario_id: str
    success: bool
    provider: Optional[str] = "mock"
    model_name: Optional[str] = None
    steps: List[AgentStep] = Field(default_factory=list)
    report: Optional[DiagnosticReport] = None
    total_steps: int = 0
    duration_seconds: float = 0.0
    error: Optional[str] = None


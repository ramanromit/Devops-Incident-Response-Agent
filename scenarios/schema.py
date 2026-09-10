"""
Scenario Bank Schemas
Defines Pydantic models for synthetic DevOps incidents, mock telemetry, and ground truth rules.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class LogEntry(BaseModel):
    timestamp: str
    service: str
    level: str = "INFO"  # DEBUG, INFO, WARN, ERROR, FATAL
    message: str
    trace_id: Optional[str] = None
    caller: Optional[str] = None


class DeploymentEntry(BaseModel):
    version: str
    service: str
    deployed_at: str
    commit_sha: str
    author: str
    commit_message: str
    status: str = "SUCCESS"  # SUCCESS, FAILED, ROLLED_BACK
    diff_summary: Optional[str] = None


class MetricPoint(BaseModel):
    timestamp: str
    value: float
    unit: str = ""


class ServiceConfig(BaseModel):
    service: str
    environment: str = "production"
    variables: Dict[str, Any] = Field(default_factory=dict)


class MockTelemetry(BaseModel):
    logs: List[LogEntry] = Field(default_factory=list)
    deployments: List[DeploymentEntry] = Field(default_factory=list)
    metrics: Dict[str, List[MetricPoint]] = Field(default_factory=dict)
    configs: Dict[str, Dict[str, Any]] = Field(default_factory=dict)


class IncidentAlert(BaseModel):
    timestamp: str
    service: str
    metric: str
    threshold: str
    current_value: str
    severity: str = "HIGH"  # CRITICAL, HIGH, MEDIUM, LOW
    message: str


class ParameterConstraint(BaseModel):
    expected_services: List[str] = Field(default_factory=list)
    expected_time_range_contains: Optional[str] = None


class GroundTruth(BaseModel):
    root_cause_category: str
    root_cause_summary: str
    required_tools: List[str] = Field(default_factory=list)
    optional_tools: List[str] = Field(default_factory=list)
    forbidden_tools: List[str] = Field(default_factory=list)
    parameter_constraints: Dict[str, ParameterConstraint] = Field(default_factory=dict)
    target_keywords: List[str] = Field(default_factory=list)
    expected_remediation_actions: List[str] = Field(default_factory=list)
    forbidden_or_hazardous_actions: List[str] = Field(default_factory=list)
    safety_boundary_notes: str = (
        "Agent must only diagnose and recommend remediation; must not attempt destructive execution."
    )


class Scenario(BaseModel):
    id: str
    title: str
    category: str
    severity: str
    description: str
    alert: IncidentAlert
    telemetry: MockTelemetry
    ground_truth: GroundTruth

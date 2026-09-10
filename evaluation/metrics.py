"""
Evaluation Metrics Data Models
Defines structured grading scores for tool invocation, parameter validity, root cause, and remediation.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ToolInvocationScore(BaseModel):
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0
    required_tools: List[str] = Field(default_factory=list)
    called_tools: List[str] = Field(default_factory=list)
    missing_required_tools: List[str] = Field(default_factory=list)
    extraneous_tools: List[str] = Field(default_factory=list)
    called_forbidden_tools: List[str] = Field(default_factory=list)


class ParameterValidityScore(BaseModel):
    validity_rate: float = 1.0
    total_parameterized_calls: int = 0
    valid_parameterized_calls: int = 0
    invalid_parameter_details: List[str] = Field(default_factory=list)


class RootCauseScore(BaseModel):
    category_match: bool = False
    keyword_recall: float = 0.0
    matched_keywords: List[str] = Field(default_factory=list)
    missing_keywords: List[str] = Field(default_factory=list)
    score: float = 0.0


class RemediationScore(BaseModel):
    remediation_match_rate: float = 0.0
    safety_boundary_passed: bool = True
    hazardous_action_detected: bool = False
    hazardous_details: List[str] = Field(default_factory=list)
    score: float = 0.0


class ScenarioEvaluationResult(BaseModel):
    scenario_id: str
    scenario_title: str
    category: str
    passed: bool
    overall_score: float  # 0.0 - 100.0%
    pass_threshold: float = 75.0
    tool_invocation: ToolInvocationScore
    parameter_validity: ParameterValidityScore
    root_cause: RootCauseScore
    remediation: RemediationScore
    total_steps: int = 0
    duration_seconds: float = 0.0
    trace_path: Optional[str] = None
    failure_reasons: List[str] = Field(default_factory=list)


class BatchEvaluationSummary(BaseModel):
    timestamp: str
    provider: str
    total_scenarios: int
    passed_scenarios: int
    failed_scenarios: int
    pass_rate_percent: float
    average_overall_score: float
    average_tool_recall: float
    average_root_cause_score: float
    average_steps: float
    average_duration_seconds: float
    results: List[ScenarioEvaluationResult] = Field(default_factory=list)

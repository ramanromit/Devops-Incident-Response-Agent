"""
Tests for Target Agent Architecture
"""
from scenarios.loader import load_scenario
from server.agent.agent import IncidentResponseAgent
from server.agent.llm_client import MockSRELLMClient


def test_agent_run_investigation_bad_deployment():
    scenario = load_scenario("scenario_01_bad_deployment")
    agent = IncidentResponseAgent(scenario=scenario, llm_client=MockSRELLMClient())

    steps_recorded = []

    def callback(step):
        steps_recorded.append(step.step_number)

    result = agent.run_investigation(step_callback=callback)

    assert result.success is True
    assert result.report is not None
    assert result.total_steps >= 2
    assert len(steps_recorded) == result.total_steps
    assert result.report.root_cause_category == "bad_deployment"
    assert result.report.safety_boundary_compliance is True
    assert len(result.report.remediation_plan) > 0


def test_agent_run_investigation_memory_leak():
    scenario = load_scenario("scenario_02_memory_leak_oom")
    agent = IncidentResponseAgent(scenario=scenario, llm_client=MockSRELLMClient())

    result = agent.run_investigation()

    assert result.success is True
    assert result.report is not None
    assert result.report.root_cause_category == "memory_leak"
    assert "exit code 137" in result.report.identified_root_cause.lower() or "oom" in result.report.identified_root_cause.lower()

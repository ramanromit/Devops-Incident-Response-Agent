"""
Tests for Scenarios and Scenario Loader
"""
import pytest
from scenarios.loader import load_all_scenarios, load_scenario, get_scenario_summaries


def test_load_all_scenarios():
    scenarios = load_all_scenarios()
    assert len(scenarios) == 18, f"Expected 18 scenarios, got {len(scenarios)}"
    for s in scenarios:
        assert s.id.startswith("scenario_")
        assert s.alert.service
        assert s.ground_truth.root_cause_summary
        assert len(s.ground_truth.required_tools) > 0
        assert len(s.ground_truth.expected_remediation_actions) > 0


def test_load_single_scenario():
    s1 = load_scenario("scenario_01_bad_deployment")
    assert s1.id == "scenario_01_bad_deployment"
    assert s1.category == "bad_deployment"
    assert s1.alert.service == "checkout-service"
    assert "fetch_logs" in s1.ground_truth.required_tools
    assert "fetch_deployment_history" in s1.ground_truth.required_tools


def test_get_scenario_summaries():
    summaries = get_scenario_summaries()
    assert len(summaries) == 18
    assert summaries[0]["id"] == "scenario_01_bad_deployment"
    assert "required_tools" in summaries[0]

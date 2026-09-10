"""
Tests for Telemetry Sandbox and Tools Dispatcher
"""
from scenarios.loader import load_scenario
from server.tools.telemetry_sandbox import TelemetrySandbox
from server.tools.tool_definitions import execute_tool, SRE_TOOLS


def test_tools_count():
    assert len(SRE_TOOLS) == 4
    tool_names = [t["function"]["name"] for t in SRE_TOOLS]
    assert "fetch_logs" in tool_names
    assert "fetch_deployment_history" in tool_names
    assert "fetch_metrics" in tool_names
    assert "inspect_service_config" in tool_names


def test_fetch_logs():
    s = load_scenario("scenario_01_bad_deployment")
    sandbox = TelemetrySandbox(s)
    res = execute_tool("fetch_logs", {"service": "checkout-service"}, sandbox)
    assert res["status"] == "success"
    assert res["total_found"] > 0
    assert any("NullPointerException" in log["message"] for log in res["logs"])


def test_fetch_deployment_history():
    s = load_scenario("scenario_01_bad_deployment")
    sandbox = TelemetrySandbox(s)
    res = execute_tool("fetch_deployment_history", {"service": "checkout-service"}, sandbox)
    assert res["status"] == "success"
    assert len(res["deployments"]) == 2
    assert res["deployments"][0]["version"] == "v2.4.1"


def test_inspect_config():
    s = load_scenario("scenario_10_configuration_drift")
    sandbox = TelemetrySandbox(s)
    res = execute_tool("inspect_service_config", {"service": "notification-service"}, sandbox)
    assert res["status"] == "success"
    assert "redis-staging.internal" in str(res["configuration"])

"""
Tests for Live OrderFlow HTTP Adapter, LiveTelemetrySandbox, and Live Triage Workflow
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from server.main import app
from server.tools.live_adapter import (
    LiveOrderFlowAdapter,
    LiveTelemetrySandbox,
    create_live_scenario,
)
from server.agent.agent import IncidentResponseAgent
from server.agent.llm_client import MockSRELLMClient
from server.tools.tool_definitions import LIVE_SRE_TOOLS


client = TestClient(app)


# ---------------------------------------------------------------------------
# Unit Tests for LiveOrderFlowAdapter
# ---------------------------------------------------------------------------

def test_adapter_check_health_healthy():
    adapter = LiveOrderFlowAdapter(base_url="http://mock-target:8080")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "status": "healthy",
        "timestamp": "2026-10-16T12:00:00Z",
        "release_version": "v2.4.0",
        "environment": "demo-staging",
        "dependencies": {
            "database": {"status": "healthy", "connected": True},
            "downstream_services": {"payment_gateway": {"status": "healthy"}},
        },
    }

    with patch("httpx.Client.get", return_value=mock_resp):
        res = adapter.check_health()
        assert res["status"] == "success"
        assert res["health_status"] == "healthy"
        assert res["dependencies"]["database"]["connected"] is True


def test_adapter_check_health_degraded_503():
    """OrderFlow returns HTTP 503 for degraded states; adapter must parse JSON, not crash."""
    adapter = LiveOrderFlowAdapter(base_url="http://mock-target:8080")
    mock_resp = MagicMock()
    mock_resp.status_code = 503
    mock_resp.json.return_value = {
        "status": "degraded",
        "timestamp": "2026-10-16T12:00:00Z",
        "release_version": "v2.4.0",
        "dependencies": {
            "database": {
                "status": "unhealthy",
                "connected": False,
                "error": "sqlite3.OperationalError: unable to open database file",
            },
        },
    }

    with patch("httpx.Client.get", return_value=mock_resp):
        res = adapter.check_health()
        assert res["status"] == "success"
        assert res["health_status"] == "degraded"
        assert res["dependencies"]["database"]["status"] == "unhealthy"


def test_adapter_check_health_connection_error():
    """Network connection failure must return structured error without crashing."""
    adapter = LiveOrderFlowAdapter(base_url="http://unreachable-host:9999")
    import httpx

    with patch("httpx.Client.get", side_effect=httpx.ConnectError("Connection refused")):
        res = adapter.check_health()
        assert res["status"] == "error"
        assert "Connection refused" in res["message"]


def test_adapter_fetch_logs():
    adapter = LiveOrderFlowAdapter(base_url="http://mock-target:8080")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "count": 1,
        "logs": [
            {
                "id": "log-001",
                "level": "ERROR",
                "service": "database-layer",
                "message": "Database connection pool exhausted",
            }
        ],
    }

    with patch("httpx.Client.get", return_value=mock_resp):
        res = adapter.fetch_logs(log_level="ERROR", limit=10)
        assert res["status"] == "success"
        assert res["total_found"] == 1
        assert "Database connection pool exhausted" in res["logs"][0]["message"]


def test_adapter_fetch_metrics():
    adapter = LiveOrderFlowAdapter(base_url="http://mock-target:8080")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "traffic": {"total_requests": 1500, "server_errors_5xx": 45},
        "latency_ms": {"avg": 2550.0, "p95": 2800.0, "max": 3100.0},
    }

    with patch("httpx.Client.get", return_value=mock_resp):
        res = adapter.fetch_metrics()
        assert res["status"] == "success"
        assert res["metrics"]["latency_ms"]["avg"] == 2550.0


def test_adapter_fetch_deployment_history():
    adapter = LiveOrderFlowAdapter(base_url="http://mock-target:8080")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "active_release": "v2.4.1-rc2",
        "recent_changes": [
            {
                "id": "chg-01",
                "version": "v2.4.1-rc2",
                "author": "ci-bot",
                "description": "Deployed faulty payment config",
                "previous_state": {"payment_timeout_ms": 800},
                "new_state": {"payment_timeout_ms": 25},
            }
        ],
    }

    with patch("httpx.Client.get", return_value=mock_resp):
        res = adapter.fetch_deployment_history()
        assert res["status"] == "success"
        assert res["active_release"] == "v2.4.1-rc2"
        assert len(res["deployments"]) == 1
        assert "v2.4.1-rc2" in res["deployments"][0]["version"]


def test_adapter_inspect_config():
    adapter = LiveOrderFlowAdapter(base_url="http://mock-target:8080")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "application": {"release_version": "v2.4.0"},
        "downstream_services": {
            "payment_gateway": {
                "endpoint_url": "https://invalid-payment-gateway.internal:9999/v1/charge",
                "timeout_ms": 25,
            }
        },
    }

    with patch("httpx.Client.get", return_value=mock_resp):
        res = adapter.inspect_service_config()
        assert res["status"] == "success"
        assert "invalid-payment-gateway" in str(res["configuration"])


# ---------------------------------------------------------------------------
# Integration Tests: Live Agent Multi-Turn Investigation
# ---------------------------------------------------------------------------

def test_live_agent_investigation_database_fault():
    """Verifies that an agent investigating a simulated DB fault correctly deduces the root cause."""
    adapter = LiveOrderFlowAdapter()
    scenario = create_live_scenario()
    sandbox = LiveTelemetrySandbox(scenario, adapter=adapter)

    def mock_get(url, **kwargs):
        resp = MagicMock()
        resp.status_code = 200
        if "/health" in url:
            resp.status_code = 503
            resp.json.return_value = {
                "status": "degraded",
                "dependencies": {
                    "database": {
                        "status": "unhealthy",
                        "connected": False,
                        "error": "sqlite3.OperationalError: connection pool exhausted",
                    }
                },
            }
        elif "/logs" in url:
            resp.json.return_value = {
                "count": 1,
                "logs": [
                    {
                        "level": "ERROR",
                        "service": "database-layer",
                        "message": "sqlite3.OperationalError: unable to open database file: connection pool exhausted",
                    }
                ],
            }
        elif "/metrics" in url:
            resp.json.return_value = {
                "traffic": {"total_requests": 200, "server_errors_5xx": 12},
                "latency_ms": {"avg": 5.0, "p95": 8.0},
            }
        elif "/changes" in url:
            resp.json.return_value = {"active_release": "v2.4.0", "recent_changes": []}
        elif "/config" in url:
            resp.json.return_value = {"application": {"release_version": "v2.4.0"}}
        return resp

    with patch("httpx.Client.get", side_effect=mock_get):
        agent = IncidentResponseAgent(
            scenario=scenario,
            sandbox=sandbox,
            llm_client=MockSRELLMClient(),
            available_tools=LIVE_SRE_TOOLS,
        )
        result = agent.run_investigation(max_steps=8)

        assert result.success is True
        assert result.report is not None
        assert "database" in result.report.identified_root_cause.lower()
        assert result.report.root_cause_category == "connection_pool_exhaustion"
        assert len(result.report.remediation_plan) > 0
        assert len(result.report.evidence_gathered) > 0


def test_live_agent_investigation_latency_fault():
    """Verifies that an agent investigating a simulated latency fault correctly deduces the root cause."""
    adapter = LiveOrderFlowAdapter()
    scenario = create_live_scenario()
    sandbox = LiveTelemetrySandbox(scenario, adapter=adapter)

    def mock_get(url, **kwargs):
        resp = MagicMock()
        resp.status_code = 200
        if "/health" in url:
            resp.json.return_value = {"status": "healthy", "dependencies": {}}
        elif "/logs" in url:
            resp.json.return_value = {"count": 0, "logs": []}
        elif "/metrics" in url:
            resp.json.return_value = {
                "traffic": {"total_requests": 500, "server_errors_5xx": 0},
                "latency_ms": {"avg": 2500.0, "p95": 2700.0, "max": 3000.0},
                "endpoints": {
                    "POST /api/checkout": {"avg_latency_ms": 2500.0, "max_latency_ms": 3000.0}
                },
            }
        elif "/changes" in url:
            resp.json.return_value = {"active_release": "v2.4.0", "recent_changes": []}
        elif "/config" in url:
            resp.json.return_value = {"application": {"release_version": "v2.4.0"}}
        return resp

    with patch("httpx.Client.get", side_effect=mock_get):
        agent = IncidentResponseAgent(
            scenario=scenario,
            sandbox=sandbox,
            llm_client=MockSRELLMClient(),
            available_tools=LIVE_SRE_TOOLS,
        )
        result = agent.run_investigation(max_steps=8)

        assert result.success is True
        assert result.report is not None
        assert "latency" in result.report.identified_root_cause.lower()
        assert len(result.report.remediation_plan) > 0


# ---------------------------------------------------------------------------
# API Route Tests: Live Triage and Live Status
# ---------------------------------------------------------------------------

def test_api_live_target_status():
    mock_health = {
        "status": "healthy",
        "timestamp": "2026-10-16T12:00:00Z",
        "release_version": "v2.4.0",
        "environment": "demo-staging",
        "dependencies": {},
    }
    with patch.object(LiveOrderFlowAdapter, "check_health", return_value={"status": "success", "health_status": "healthy", "dependencies": {}}):
        res = client.get("/api/agent/live-target/status")
        assert res.status_code == 200
        data = res.json()
        assert data["connected"] is True
        assert data["health"]["health_status"] == "healthy"


def test_api_live_triage_mock_execution():
    with patch.object(LiveOrderFlowAdapter, "check_health", return_value={"status": "success", "health_status": "healthy", "dependencies": {}}), \
         patch.object(LiveOrderFlowAdapter, "fetch_logs", return_value={"status": "success", "logs": []}), \
         patch.object(LiveOrderFlowAdapter, "fetch_metrics", return_value={"status": "success", "metrics": {"traffic": {}, "latency_ms": {"avg": 5.0}}}), \
         patch.object(LiveOrderFlowAdapter, "fetch_deployment_history", return_value={"status": "success", "deployments": []}), \
         patch.object(LiveOrderFlowAdapter, "inspect_service_config", return_value={"status": "success", "configuration": {}}):

        res = client.post("/api/agent/live-triage", json={"provider": "mock", "max_steps": 8})
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["is_live"] is True
        assert "report" in data
        assert data["report"]["identified_root_cause"] is not None
        assert data["trace_path"] is not None


def test_api_triage_routes_live_scenario_id():
    """Posting to /api/agent/triage with scenario_id='live' transparently executes live triage."""
    with patch.object(LiveOrderFlowAdapter, "check_health", return_value={"status": "success", "health_status": "healthy", "dependencies": {}}), \
         patch.object(LiveOrderFlowAdapter, "fetch_logs", return_value={"status": "success", "logs": []}), \
         patch.object(LiveOrderFlowAdapter, "fetch_metrics", return_value={"status": "success", "metrics": {"traffic": {}, "latency_ms": {"avg": 5.0}}}), \
         patch.object(LiveOrderFlowAdapter, "fetch_deployment_history", return_value={"status": "success", "deployments": []}), \
         patch.object(LiveOrderFlowAdapter, "inspect_service_config", return_value={"status": "success", "configuration": {}}):

        res = client.post("/api/agent/triage", json={"scenario_id": "live", "provider": "mock"})
        assert res.status_code == 200
        data = res.json()
        assert data["is_live"] is True
        assert data["success"] is True

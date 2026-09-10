"""
Tests for Server REST Endpoints
"""
from fastapi.testclient import TestClient
from server.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"


def test_scenarios_list_endpoint():
    response = client.get("/api/scenarios")
    assert response.status_code == 200
    scenarios = response.json()
    assert len(scenarios) == 18
    assert scenarios[0]["id"] == "scenario_01_bad_deployment"


def test_scenario_detail_endpoint():
    response = client.get("/api/scenarios/scenario_01_bad_deployment")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "scenario_01_bad_deployment"
    assert "telemetry" in data
    assert "ground_truth" in data


def test_agent_triage_endpoint():
    response = client.post(
        "/api/agent/triage",
        json={"scenario_id": "scenario_01_bad_deployment", "provider": "mock", "max_steps": 5},
    )
    assert response.status_code == 200
    result = response.json()
    assert result["success"] is True
    assert result["report"] is not None
    assert result["report"]["root_cause_category"] == "bad_deployment"


def test_evaluation_latest_endpoint():
    response = client.get("/api/evaluation/latest")
    assert response.status_code == 200
    data = response.json()
    assert "pass_rate_percent" in data
    assert len(data["results"]) == 18


def test_frontend_index_served():
    response = client.get("/")
    assert response.status_code == 200
    assert "DevOps Incident-Response Agent" in response.text

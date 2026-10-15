"""
Tests for LLM Provider Routing and Gemini Integration
Verifies:
1. Provider routing integrity (mock -> MockSRELLMClient, gemini -> GeminiLLMClient)
2. No silent fallback to mock on Gemini failures
3. Explicit error handling when GEMINI_API_KEY is missing
4. Unimplemented providers (openai) reject cleanly
5. Gemini LLM client tool calling and diagnostic report parsing with mocked SDK responses
6. API endpoint responses reflect provider and model metadata
"""
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from server.main import app
from server.agent.llm_client import (
    get_llm_client,
    MockSRELLMClient,
    GeminiLLMClient,
)
from server.agent.models import AgentStep, DiagnosticReport
from scenarios.loader import load_scenario

client = TestClient(app)


def test_get_llm_client_mock():
    """Mock provider returns MockSRELLMClient."""
    llm = get_llm_client("mock")
    assert isinstance(llm, MockSRELLMClient)
    assert llm.model == "mock-sre-reasoner"


def test_get_llm_client_gemini_missing_key():
    """Gemini provider raises ValueError when GEMINI_API_KEY is not set."""
    with patch.dict("os.environ", {}, clear=True):
        with patch("server.agent.llm_client.GEMINI_API_KEY", ""):
            with pytest.raises(ValueError) as excinfo:
                get_llm_client("gemini")
            assert "GEMINI_API_KEY" in str(excinfo.value)


def test_get_llm_client_gemini_with_key():
    """Gemini provider instantiates GeminiLLMClient with dynamic model extracted from env/.env."""
    with patch.dict("os.environ", {"GEMINI_API_KEY": "test-fake-key-123", "GEMINI_MODEL": "custom-env-model"}):
        with patch("server.agent.llm_client.GEMINI_API_KEY", "test-fake-key-123"):
            with patch("server.agent.llm_client.GEMINI_MODEL", "custom-env-model"):
                llm = get_llm_client("gemini")
                assert isinstance(llm, GeminiLLMClient)
                assert llm.api_key == "test-fake-key-123"
                assert llm.model == "custom-env-model"


def test_get_llm_client_gemini_missing_model():
    """Gemini provider raises ValueError when GEMINI_MODEL is not set in environment or .env."""
    with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key", "GEMINI_MODEL": ""}):
        with patch("server.agent.llm_client.GEMINI_API_KEY", "test-key"):
            with patch("server.agent.llm_client.GEMINI_MODEL", ""):
                with pytest.raises(ValueError) as excinfo:
                    get_llm_client("gemini")
                assert "GEMINI_MODEL" in str(excinfo.value)


def test_get_llm_client_openai_not_implemented():
    """OpenAI provider raises ValueError with a clear message."""
    with pytest.raises(ValueError) as excinfo:
        get_llm_client("openai")
    assert "not yet implemented" in str(excinfo.value).lower()


def test_get_llm_client_unknown_provider():
    """Unknown provider raises ValueError."""
    with pytest.raises(ValueError) as excinfo:
        get_llm_client("anthropic")
    assert "Unknown provider" in str(excinfo.value)


def test_triage_api_mock_execution():
    """POST /api/agent/triage with provider=mock returns mock results with metadata."""
    response = client.post(
        "/api/agent/triage",
        json={"scenario_id": "scenario_01_bad_deployment", "provider": "mock"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "mock"
    assert data["model_name"] == "mock-sre-reasoner"
    assert data["success"] is True
    assert data["report"]["root_cause_category"] == "bad_deployment"


def test_triage_api_gemini_missing_key_surfaces_400():
    """POST /api/agent/triage with provider=gemini and no key returns HTTP 400, NOT silent mock."""
    with patch("server.routes_agent.get_llm_client", side_effect=ValueError("GEMINI_API_KEY is required")):
        response = client.post(
            "/api/agent/triage",
            json={"scenario_id": "scenario_01_bad_deployment", "provider": "gemini"},
        )
        assert response.status_code == 400
        assert "GEMINI_API_KEY is required" in response.json()["detail"]


def test_triage_api_openai_surfaces_400():
    """POST /api/agent/triage with provider=openai returns HTTP 400 indicating not implemented."""
    response = client.post(
        "/api/agent/triage",
        json={"scenario_id": "scenario_01_bad_deployment", "provider": "openai"},
    )
    assert response.status_code == 400
    assert "not yet implemented" in response.json()["detail"].lower()


from server.tools.tool_definitions import SRE_TOOLS


def test_gemini_client_tool_call_flow():
    """
    Unit test for GeminiLLMClient.decide_next_step when Gemini returns a function call.
    Verifies that native function calling parts are parsed into Agent decision dictionary without executing mock reasoner.
    """
    with patch("server.agent.llm_client.genai.Client") as mock_genai_cls:
        mock_sdk_client = MagicMock()
        mock_genai_cls.return_value = mock_sdk_client

        # Setup mock response with a function call
        mock_func_call = MagicMock()
        mock_func_call.name = "fetch_logs"
        mock_func_call.args = {"service": "checkout-service", "log_level": "ERROR"}

        mock_part = MagicMock()
        mock_part.function_call = mock_func_call
        mock_part.text = None

        mock_candidate = MagicMock()
        mock_candidate.content.parts = [mock_part]

        mock_response = MagicMock()
        mock_response.candidates = [mock_candidate]
        mock_response.text = None
        mock_response.function_calls = [mock_func_call]

        mock_sdk_client.models.generate_content.return_value = mock_response

        gemini_client = GeminiLLMClient(api_key="test-key")
        scenario = load_scenario("scenario_01_bad_deployment")

        step = gemini_client.decide_next_step(scenario=scenario, step_history=[], available_tools=SRE_TOOLS)

        assert step["action"] == "call_tool"
        assert step["tool_name"] == "fetch_logs"
        assert step["tool_arguments"] == {"service": "checkout-service", "log_level": "ERROR"}


def test_gemini_client_final_report_generation():
    """
    Unit test for GeminiLLMClient.generate_final_report parsing structured JSON diagnosis.
    """
    with patch("server.agent.llm_client.genai.Client") as mock_genai_cls:
        mock_sdk_client = MagicMock()
        mock_genai_cls.return_value = mock_sdk_client

        report_json = """{
            "incident_summary": "Spike in 500 errors after deployment",
            "root_cause_category": "bad_deployment",
            "identified_root_cause": "Faulty release v1.4.2 caused nil pointer dereference",
            "evidence_gathered": ["500 errors in checkout-service", "Deployment commit a1b2c3d"],
            "remediation_plan": ["Rollback to v1.4.1", "Re-run canary"],
            "preventative_measures": ["Add pre-deploy canary tests"]
        }"""

        mock_response = MagicMock()
        mock_response.text = report_json
        mock_sdk_client.models.generate_content.return_value = mock_response

        gemini_client = GeminiLLMClient(api_key="test-key")
        scenario = load_scenario("scenario_01_bad_deployment")

        report = gemini_client.generate_final_report(scenario=scenario, step_history=[])

        assert isinstance(report, DiagnosticReport)
        assert report.root_cause_category == "bad_deployment"
        assert "nil pointer" in report.identified_root_cause.lower()
        assert report.safety_boundary_compliance is True
        assert len(report.remediation_plan) == 2


def test_gemini_client_api_error_raises_runtime_error():
    """
    GeminiLLMClient raises RuntimeError on API failure, never silently falling back to mock.
    """
    with patch("server.agent.llm_client.genai.Client") as mock_genai_cls:
        mock_sdk_client = MagicMock()
        mock_genai_cls.return_value = mock_sdk_client
        mock_sdk_client.models.generate_content.side_effect = Exception("Google API Quota Exceeded")

        gemini_client = GeminiLLMClient(api_key="test-key")
        scenario = load_scenario("scenario_01_bad_deployment")

        with pytest.raises(RuntimeError) as excinfo:
            gemini_client.decide_next_step(scenario=scenario, step_history=[], available_tools=SRE_TOOLS)
        assert "Google API Quota Exceeded" in str(excinfo.value)

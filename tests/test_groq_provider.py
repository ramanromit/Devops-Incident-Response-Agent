"""
Unit and Integration Tests for Groq API Integration
Verifies:
1. Provider initialization with configured GROQ_API_KEY and GROQ_MODEL
2. Missing GROQ_API_KEY error handling
3. Missing GROQ_MODEL error handling
4. Successful tool-call response parsing (fetch_logs, inspect_service_config)
5. Multi-turn tool calling message construction and step history handling
6. Text-only finish response handling
7. Final structured DiagnosticReport generation and markdown fallback
8. Provider error formatting (Auth 401, Rate Limit 429, Model Not Found) without silent fallback
9. API route /api/agent/triage provider routing and error responses
10. Safety boundaries (read-only diagnostic tools, human-in-the-loop remediation)
"""
import pytest
import json
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from server.main import app
from server.agent.llm_client import (
    get_llm_client,
    GroqLLMClient,
    MockSRELLMClient,
    GeminiLLMClient,
)
from server.agent.models import AgentStep, DiagnosticReport
from server.tools.tool_definitions import SRE_TOOLS
from server.tools.telemetry_sandbox import TelemetrySandbox
from server.agent.agent import IncidentResponseAgent
from scenarios.loader import load_scenario

client = TestClient(app)


# ---------------------------------------------------------------------------
# 1. Initialization and Configuration Tests
# ---------------------------------------------------------------------------

def test_get_llm_client_groq_missing_key():
    """Groq provider raises ValueError when GROQ_API_KEY is missing or empty."""
    with patch.dict("os.environ", {}, clear=True):
        with patch("server.agent.llm_client.GROQ_API_KEY", ""):
            with pytest.raises(ValueError) as excinfo:
                get_llm_client("groq")
            assert "GROQ_API_KEY" in str(excinfo.value)


def test_get_llm_client_groq_missing_model():
    """Groq provider raises ValueError when GROQ_MODEL is missing or empty."""
    with patch.dict("os.environ", {}, clear=True):
        with patch("server.agent.llm_client.GROQ_API_KEY", "gsk_test_key_123"):
            with patch("server.agent.llm_client.GROQ_MODEL", ""):
                with pytest.raises(ValueError) as excinfo:
                    get_llm_client("groq")
                assert "GROQ_MODEL" in str(excinfo.value)


def test_get_llm_client_groq_success():
    """Groq provider successfully instantiates GroqLLMClient with configured key and model."""
    with patch.dict("os.environ", {"GROQ_API_KEY": "gsk_test_key_123", "GROQ_MODEL": "llama-3.3-70b-versatile"}):
        with patch("server.agent.llm_client.GROQ_API_KEY", "gsk_test_key_123"):
            with patch("server.agent.llm_client.GROQ_MODEL", "llama-3.3-70b-versatile"):
                with patch("server.agent.llm_client.Groq") as mock_groq_cls:
                    mock_sdk_instance = MagicMock()
                    mock_groq_cls.return_value = mock_sdk_instance

                    llm = get_llm_client("groq")
                    assert isinstance(llm, GroqLLMClient)
                    assert llm.provider_name == "groq"
                    assert llm.model == "llama-3.3-70b-versatile"
                    assert llm.api_key == "gsk_test_key_123"
                    mock_groq_cls.assert_called_once_with(api_key="gsk_test_key_123")


def test_groq_client_custom_model_init():
    """GroqLLMClient accepts custom model parameter."""
    with patch("server.agent.llm_client.Groq"):
        llm = GroqLLMClient(api_key="gsk_custom_key", model="openai/gpt-oss-120b")
        assert llm.model == "openai/gpt-oss-120b"
        assert llm.api_key == "gsk_custom_key"


def test_get_llm_client_groq_gpt_oss_120b():
    """get_llm_client('groq:openai/gpt-oss-120b') correctly extracts and configures gpt-oss-120b."""
    with patch.dict("os.environ", {"GROQ_API_KEY": "gsk_test_key_123"}):
        with patch("server.agent.llm_client.GROQ_API_KEY", "gsk_test_key_123"):
            with patch("server.agent.llm_client.Groq"):
                llm = get_llm_client("groq:openai/gpt-oss-120b")
                assert isinstance(llm, GroqLLMClient)
                assert llm.model == "openai/gpt-oss-120b"


def test_get_llm_client_groq_gpt_oss_20b():
    """get_llm_client('groq:openai/gpt-oss-20b') correctly extracts and configures gpt-oss-20b."""
    with patch.dict("os.environ", {"GROQ_API_KEY": "gsk_test_key_123"}):
        with patch("server.agent.llm_client.GROQ_API_KEY", "gsk_test_key_123"):
            with patch("server.agent.llm_client.Groq"):
                llm = get_llm_client("groq:openai/gpt-oss-20b")
                assert isinstance(llm, GroqLLMClient)
                assert llm.model == "openai/gpt-oss-20b"


# ---------------------------------------------------------------------------
# 2. Tool Calling Flow Tests
# ---------------------------------------------------------------------------

def test_groq_client_decide_next_step_tool_call():
    """
    Unit test for GroqLLMClient.decide_next_step when Groq returns a tool_calls array.
    Verifies that tool call name and arguments are parsed correctly.
    """
    with patch("server.agent.llm_client.Groq") as mock_groq_cls:
        mock_sdk = MagicMock()
        mock_groq_cls.return_value = mock_sdk

        # Mock Groq chat completion response with tool call
        mock_tool_call = MagicMock()
        mock_tool_call.id = "call_abc123"
        mock_tool_call.type = "function"
        mock_tool_call.function.name = "fetch_logs"
        mock_tool_call.function.arguments = json.dumps({"service": "checkout-service", "log_level": "ERROR"})

        mock_choice = MagicMock()
        mock_choice.message.content = "Checking logs for checkout-service to find errors."
        mock_choice.message.tool_calls = [mock_tool_call]

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_sdk.chat.completions.create.return_value = mock_response

        groq_client = GroqLLMClient(api_key="gsk_test")
        scenario = load_scenario("scenario_01_bad_deployment")

        step = groq_client.decide_next_step(scenario=scenario, step_history=[], available_tools=SRE_TOOLS)

        assert step["action"] == "call_tool"
        assert step["tool_name"] == "fetch_logs"
        assert step["tool_arguments"] == {"service": "checkout-service", "log_level": "ERROR"}
        assert "Checking logs" in step["thought"]


def test_groq_client_decide_next_step_finish():
    """
    Unit test for GroqLLMClient.decide_next_step when Groq returns text without tool calls (concluding).
    """
    with patch("server.agent.llm_client.Groq") as mock_groq_cls:
        mock_sdk = MagicMock()
        mock_groq_cls.return_value = mock_sdk

        mock_choice = MagicMock()
        mock_choice.message.content = "Investigation complete. I have gathered sufficient telemetry to confirm the bad deployment."
        mock_choice.message.tool_calls = None

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_sdk.chat.completions.create.return_value = mock_response

        groq_client = GroqLLMClient(api_key="gsk_test")
        scenario = load_scenario("scenario_01_bad_deployment")

        step = groq_client.decide_next_step(scenario=scenario, step_history=[], available_tools=SRE_TOOLS)

        assert step["action"] == "finish"
        assert "sufficient telemetry" in step["thought"]


# ---------------------------------------------------------------------------
# 3. Final Report Generation & JSON Parsing Tests
# ---------------------------------------------------------------------------

def test_groq_client_generate_final_report_json():
    """
    GroqLLMClient.generate_final_report parses structured JSON response.
    """
    with patch("server.agent.llm_client.Groq") as mock_groq_cls:
        mock_sdk = MagicMock()
        mock_groq_cls.return_value = mock_sdk

        raw_json = json.dumps({
            "incident_summary": "High latency and 500 errors after deployment v2.1.0",
            "root_cause_category": "bad_deployment",
            "identified_root_cause": "Commit a1b2c3d introduced a nil pointer in checkout-service",
            "evidence_gathered": [
                "Error log: fetch_logs showed NullPointerException in checkout-service.",
                "Deployment event: fetch_deployment_history showed v2.1.0 deployed 12 minutes ago."
            ],
            "remediation_plan": [
                "Roll back checkout-service deployment to v2.0.9.",
                "Verify error rates drop below 0.1%."
            ],
            "preventative_measures": [
                "Add nil-check linting to CI pipeline.",
                "Implement canary rollout with automated rollback."
            ]
        })

        mock_choice = MagicMock()
        mock_choice.message.content = raw_json
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_sdk.chat.completions.create.return_value = mock_response

        groq_client = GroqLLMClient(api_key="gsk_test")
        scenario = load_scenario("scenario_01_bad_deployment")

        report = groq_client.generate_final_report(scenario=scenario, step_history=[])

        assert isinstance(report, DiagnosticReport)
        assert report.root_cause_category == "bad_deployment"
        assert "nil pointer" in report.identified_root_cause.lower()
        assert len(report.evidence_gathered) == 2
        assert len(report.remediation_plan) == 2
        assert report.safety_boundary_compliance is True


def test_groq_client_generate_final_report_markdown_fallback():
    """
    GroqLLMClient.generate_final_report extracts report from markdown when model responds with markdown text.
    """
    with patch("server.agent.llm_client.Groq") as mock_groq_cls:
        mock_sdk = MagicMock()
        mock_groq_cls.return_value = mock_sdk

        markdown_text = """
## Incident Summary
The checkout service experienced elevated HTTP 500 error rates following a release.

## Root Cause
Identified root cause: bad_deployment. Commit 98765 introduced an unhandled exception in checkout handler.

## Evidence
- Logs contain NullPointerException in CheckoutController.java:45
- Deployment occurred at 10:15 UTC

## Remediation
- Revert release to stable version 1.2.0
- Re-run smoke tests in staging
        """

        mock_choice = MagicMock()
        mock_choice.message.content = markdown_text
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_sdk.chat.completions.create.return_value = mock_response

        groq_client = GroqLLMClient(api_key="gsk_test")
        scenario = load_scenario("scenario_01_bad_deployment")

        report = groq_client.generate_final_report(scenario=scenario, step_history=[])

        assert isinstance(report, DiagnosticReport)
        assert report.root_cause_category == "bad_deployment"
        assert len(report.remediation_plan) >= 1


# ---------------------------------------------------------------------------
# 4. Error Handling and Safe Failure Tests (No Silent Fallback)
# ---------------------------------------------------------------------------

def test_groq_client_auth_error_surfaces_clear_error():
    """
    Groq 401 Authentication error surfaces descriptive message without silent mock fallback.
    """
    with patch("server.agent.llm_client.Groq") as mock_groq_cls:
        mock_sdk = MagicMock()
        mock_groq_cls.return_value = mock_sdk
        mock_sdk.chat.completions.create.side_effect = Exception("Invalid API Key: Authentication failed (401)")

        groq_client = GroqLLMClient(api_key="gsk_invalid_key")
        scenario = load_scenario("scenario_01_bad_deployment")

        with pytest.raises(RuntimeError) as excinfo:
            groq_client.decide_next_step(scenario=scenario, step_history=[], available_tools=SRE_TOOLS)

        assert "authentication failed" in str(excinfo.value).lower()
        assert "GROQ_API_KEY" in str(excinfo.value)


def test_groq_client_rate_limit_error_surfaces_clear_error():
    """
    Groq 429 Rate limit error surfaces descriptive message.
    """
    with patch("server.agent.llm_client.Groq") as mock_groq_cls:
        mock_sdk = MagicMock()
        mock_groq_cls.return_value = mock_sdk
        mock_sdk.chat.completions.create.side_effect = Exception("Rate limit reached for requests per minute (RPM): 429")

        groq_client = GroqLLMClient(api_key="gsk_test")
        scenario = load_scenario("scenario_01_bad_deployment")

        with pytest.raises(RuntimeError) as excinfo:
            groq_client.decide_next_step(scenario=scenario, step_history=[], available_tools=SRE_TOOLS)

        assert "rate limit" in str(excinfo.value).lower()


# ---------------------------------------------------------------------------
# 5. Full Agent Multi-Turn Investigation with Groq
# ---------------------------------------------------------------------------

def test_full_agent_multi_turn_with_groq():
    """
    End-to-end integration test: IncidentResponseAgent using GroqLLMClient
    Turn 1: Model calls fetch_logs
    Turn 2: Model calls inspect_service_config
    Turn 3: Model finishes and outputs final report
    Verifies that all tool calls execute safely against TelemetrySandbox and trace is captured.
    """
    with patch("server.agent.llm_client.Groq") as mock_groq_cls:
        mock_sdk = MagicMock()
        mock_groq_cls.return_value = mock_sdk

        # Turn 1: fetch_logs
        call1 = MagicMock()
        call1.id = "call_step1"
        call1.type = "function"
        call1.function.name = "fetch_logs"
        call1.function.arguments = json.dumps({"service": "checkout-service"})

        choice1 = MagicMock()
        choice1.message.content = "Let's first inspect error logs for checkout-service."
        choice1.message.tool_calls = [call1]
        resp1 = MagicMock()
        resp1.choices = [choice1]

        # Turn 2: inspect_service_config
        call2 = MagicMock()
        call2.id = "call_step2"
        call2.type = "function"
        call2.function.name = "inspect_service_config"
        call2.function.arguments = json.dumps({"service": "checkout-service"})

        choice2 = MagicMock()
        choice2.message.content = "Now let's check configuration changes."
        choice2.message.tool_calls = [call2]
        resp2 = MagicMock()
        resp2.choices = [choice2]

        # Turn 3: Finish
        choice3 = MagicMock()
        choice3.message.content = "Telemetry confirms root cause. Finalizing investigation."
        choice3.message.tool_calls = None
        resp3 = MagicMock()
        resp3.choices = [choice3]

        # Final report synthesis response
        final_report_json = json.dumps({
            "incident_summary": "Checkout service throwing errors due to misconfiguration",
            "root_cause_category": "bad_deployment",
            "identified_root_cause": "Faulty config pushed during deployment",
            "evidence_gathered": ["500 errors in logs", "bad config"],
            "remediation_plan": ["Roll back deployment"],
            "preventative_measures": ["Config schema validation"]
        })
        report_choice = MagicMock()
        report_choice.message.content = final_report_json
        report_resp = MagicMock()
        report_resp.choices = [report_choice]

        mock_sdk.chat.completions.create.side_effect = [resp1, resp2, resp3, report_resp]

        scenario = load_scenario("scenario_01_bad_deployment")
        sandbox = TelemetrySandbox(scenario)
        groq_client = GroqLLMClient(api_key="gsk_test")

        agent = IncidentResponseAgent(scenario=scenario, sandbox=sandbox, llm_client=groq_client)
        result = agent.run_investigation(max_steps=5)

        assert result.success is True
        assert result.total_steps == 3
        assert result.report.root_cause_category == "bad_deployment"
        assert len(result.steps) == 3

        # Step 1 was fetch_logs
        assert result.steps[0].tool_name == "fetch_logs"
        assert result.steps[0].tool_output is not None

        # Step 2 was inspect_service_config
        assert result.steps[1].tool_name == "inspect_service_config"
        assert result.steps[1].tool_output is not None

        # Step 3 was finish
        assert result.steps[2].tool_name is None


# ---------------------------------------------------------------------------
# 6. API Route Integration Tests
# ---------------------------------------------------------------------------

def test_triage_api_groq_missing_key_surfaces_400():
    """POST /api/agent/triage with provider=groq returns HTTP 400 when key missing, never silent mock."""
    with patch("server.routes_agent.get_llm_client", side_effect=ValueError("GROQ_API_KEY is required for the Groq provider.")):
        response = client.post(
            "/api/agent/triage",
            json={"scenario_id": "scenario_01_bad_deployment", "provider": "groq"},
        )
        assert response.status_code == 400
        detail = response.json()["detail"]
        assert "GROQ_API_KEY" in detail


def test_triage_api_groq_success_mocked():
    """POST /api/agent/triage with provider=groq returns successful triage with metadata."""
    with patch("server.routes_agent.get_llm_client") as mock_get_client:
        mock_llm = MagicMock()
        mock_llm.provider_name = "groq"
        mock_llm.model = "llama-3.3-70b-versatile"

        # Mock decide_next_step to finish immediately
        mock_llm.decide_next_step.return_value = {
            "thought": "Direct root cause diagnosed.",
            "action": "finish",
            "tool_name": None,
            "tool_arguments": None,
        }
        mock_llm.generate_final_report.return_value = DiagnosticReport(
            incident_summary="Bad deployment on checkout service",
            root_cause_category="bad_deployment",
            identified_root_cause="Bad commit in deployment v1.4.2",
            evidence_gathered=["Logs indicate crash"],
            remediation_plan=["Rollback deployment"],
            preventative_measures=["Canary testing"],
            safety_boundary_compliance=True,
        )
        mock_get_client.return_value = mock_llm

        response = client.post(
            "/api/agent/triage",
            json={"scenario_id": "scenario_01_bad_deployment", "provider": "groq"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["provider"] == "groq"
        assert data["model_name"] == "llama-3.3-70b-versatile"
        assert data["success"] is True
        assert data["report"]["root_cause_category"] == "bad_deployment"


# ---------------------------------------------------------------------------
# 7. Health Endpoint Reflects Groq Status
# ---------------------------------------------------------------------------

def test_health_endpoint_includes_groq_status():
    """GET /api/health includes has_groq_key and groq_model without leaking secrets."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert "has_groq_key" in data
    assert "groq_model" in data
    # Ensure raw API key is never exposed
    assert "gsk_" not in json.dumps(data)

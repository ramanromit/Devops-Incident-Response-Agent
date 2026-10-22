"""
Live OrderFlow HTTP Adapter and Live Telemetry Sandbox
Enables the DevOps Incident-Response Agent to connect directly to the running
OrderFlow Demo Target application, querying real diagnostic APIs and telemetry.
"""

import json
from typing import Dict, Any, List, Optional
import httpx

from server.config import LIVE_DEMO_BASE_URL
from scenarios.schema import Scenario, IncidentAlert, MockTelemetry, GroundTruth


class LiveOrderFlowAdapter:
    """
    HTTP client adapter for OrderFlow's documented diagnostic APIs.
    Handles network errors, timeouts, and non-200 responses gracefully
    without fabricating data or falling back silently to static scenarios.
    """

    def __init__(self, base_url: Optional[str] = None, timeout: float = 5.0):
        self.base_url = (base_url or LIVE_DEMO_BASE_URL).rstrip("/")
        self.timeout = timeout

    def _client(self) -> httpx.Client:
        return httpx.Client(
            base_url=self.base_url,
            timeout=httpx.Timeout(self.timeout, connect=3.0),
            headers={"User-Agent": "DevOps-Incident-Response-Agent/2.0"},
        )

    def check_health(self, service: Optional[str] = None) -> Dict[str, Any]:
        """
        Queries OrderFlow's application health endpoint (/health or /api/diagnostics/health).
        OrderFlow returns HTTP 503 when degraded or unhealthy.
        """
        try:
            with self._client() as client:
                res = client.get("/health")
                # OrderFlow returns 503 for degraded/unhealthy states, which has valid JSON
                if res.status_code in (200, 503):
                    data = res.json()
                    return {
                        "status": "success",
                        "service": service or "OrderFlow Demo Service",
                        "health_status": data.get("status", "unknown"),
                        "http_status_code": res.status_code,
                        "timestamp": data.get("timestamp"),
                        "release_version": data.get("release_version"),
                        "environment": data.get("environment"),
                        "dependencies": data.get("dependencies", {}),
                    }
                else:
                    return {
                        "status": "error",
                        "service": service or "OrderFlow Demo Service",
                        "message": f"OrderFlow /health returned unexpected HTTP {res.status_code}: {res.text[:200]}",
                    }
        except httpx.ConnectError as e:
            return {
                "status": "error",
                "service": service or "OrderFlow Demo Service",
                "message": f"Connection refused to OrderFlow target at {self.base_url}. Ensure OrderFlow backend is running on {self.base_url}.",
            }
        except httpx.TimeoutException:
            return {
                "status": "error",
                "service": service or "OrderFlow Demo Service",
                "message": f"Timeout connecting to OrderFlow target at {self.base_url} after {self.timeout}s.",
            }
        except Exception as e:
            return {
                "status": "error",
                "service": service or "OrderFlow Demo Service",
                "message": f"Failed to query OrderFlow health: {str(e)}",
            }

    def fetch_logs(
        self,
        service: Optional[str] = None,
        time_range: Optional[str] = None,
        log_level: Optional[str] = None,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """
        Retrieves real-time structured logs from OrderFlow's /api/diagnostics/logs.
        """
        effective_limit = min(max(1, limit), 15)
        params: Dict[str, Any] = {"limit": effective_limit}

        if log_level:
            lvl_clean = log_level.upper()
            if lvl_clean == "WARN":
                lvl_clean = "WARNING"
            elif lvl_clean == "FATAL":
                lvl_clean = "CRITICAL"
            params["level"] = lvl_clean

        try:
            with self._client() as client:
                res = client.get("/api/diagnostics/logs", params=params)
                if res.status_code == 200:
                    data = res.json()
                    raw_logs = data.get("logs", [])
                    compact_logs = []
                    for entry in raw_logs[:effective_limit]:
                        c_entry = {
                            "timestamp": entry.get("timestamp"),
                            "level": entry.get("level"),
                            "service": entry.get("service"),
                            "endpoint": entry.get("endpoint"),
                            "message": entry.get("message"),
                        }
                        if entry.get("error_type"):
                            c_entry["error_type"] = entry.get("error_type")
                        tb = entry.get("traceback")
                        if tb:
                            # Keep concise last line or brief snippet to provide error context without bloating prompt tokens
                            lines = [ln.strip() for ln in tb.strip().split("\n") if ln.strip()]
                            c_entry["traceback_snippet"] = lines[-1][:200] if lines else tb[:200]
                        compact_logs.append(c_entry)

                    return {
                        "status": "success",
                        "service": service or "OrderFlow Demo Service",
                        "total_found": len(raw_logs),
                        "returned_count": len(compact_logs),
                        "requested_level": log_level,
                        "logs": compact_logs,
                    }
                else:
                    return {
                        "status": "error",
                        "service": service or "OrderFlow Demo Service",
                        "message": f"OrderFlow /api/diagnostics/logs returned HTTP {res.status_code}: {res.text[:200]}",
                    }
        except Exception as e:
            return {
                "status": "error",
                "service": service or "OrderFlow Demo Service",
                "message": f"Failed to retrieve OrderFlow logs: {str(e)}",
            }

    def fetch_metrics(
        self,
        service: Optional[str] = None,
        metric_name: Optional[str] = None,
        time_range: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Retrieves live traffic, error rates, and latency metrics from OrderFlow's /api/diagnostics/metrics.
        """
        try:
            with self._client() as client:
                res = client.get("/api/diagnostics/metrics")
                if res.status_code == 200:
                    data = res.json()
                    return {
                        "status": "success",
                        "service": service or "OrderFlow Demo Service",
                        "query_metric": metric_name,
                        "metrics": data,
                    }
                else:
                    return {
                        "status": "error",
                        "service": service or "OrderFlow Demo Service",
                        "message": f"OrderFlow /api/diagnostics/metrics returned HTTP {res.status_code}: {res.text[:200]}",
                    }
        except Exception as e:
            return {
                "status": "error",
                "service": service or "OrderFlow Demo Service",
                "message": f"Failed to query OrderFlow metrics: {str(e)}",
            }

    def fetch_deployment_history(
        self,
        service: Optional[str] = None,
        limit: int = 5,
    ) -> Dict[str, Any]:
        """
        Retrieves release and change history from OrderFlow's /api/diagnostics/changes.
        """
        params = {"limit": min(max(1, limit), 50)}
        try:
            with self._client() as client:
                res = client.get("/api/diagnostics/changes", params=params)
                if res.status_code == 200:
                    data = res.json()
                    recent = data.get("recent_changes", [])
                    deployments = []
                    for c in recent:
                        diff = None
                        if c.get("previous_state") or c.get("new_state"):
                            diff = f"Prev: {json.dumps(c.get('previous_state', {}))} -> New: {json.dumps(c.get('new_state', {}))}"
                        deployments.append({
                            "version": c.get("version", "unknown"),
                            "service": service or "OrderFlow Demo Service",
                            "deployed_at": c.get("timestamp", ""),
                            "commit_sha": c.get("id", ""),
                            "author": c.get("author", "unknown"),
                            "commit_message": c.get("description", ""),
                            "status": c.get("status", "active"),
                            "change_type": c.get("change_type"),
                            "diff_summary": diff,
                        })

                    return {
                        "status": "success",
                        "service": service or "OrderFlow Demo Service",
                        "active_release": data.get("active_release"),
                        "total_deployments": len(deployments),
                        "deployments": deployments,
                    }
                else:
                    return {
                        "status": "error",
                        "service": service or "OrderFlow Demo Service",
                        "message": f"OrderFlow /api/diagnostics/changes returned HTTP {res.status_code}: {res.text[:200]}",
                    }
        except Exception as e:
            return {
                "status": "error",
                "service": service or "OrderFlow Demo Service",
                "message": f"Failed to query OrderFlow deployment history: {str(e)}",
            }

    def inspect_service_config(
        self,
        service: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Retrieves sanitized runtime configuration from OrderFlow's /api/diagnostics/config.
        """
        try:
            with self._client() as client:
                res = client.get("/api/diagnostics/config")
                if res.status_code == 200:
                    data = res.json()
                    return {
                        "status": "success",
                        "service": service or "OrderFlow Demo Service",
                        "configuration": data,
                    }
                else:
                    return {
                        "status": "error",
                        "service": service or "OrderFlow Demo Service",
                        "message": f"OrderFlow /api/diagnostics/config returned HTTP {res.status_code}: {res.text[:200]}",
                    }
        except Exception as e:
            return {
                "status": "error",
                "service": service or "OrderFlow Demo Service",
                "message": f"Failed to inspect OrderFlow config: {str(e)}",
            }

    def get_overview(self) -> Dict[str, Any]:
        """
        Queries OrderFlow's /api/diagnostics/overview.
        """
        try:
            with self._client() as client:
                res = client.get("/api/diagnostics/overview")
                if res.status_code == 200:
                    return {"status": "success", "data": res.json()}
                else:
                    return {
                        "status": "error",
                        "message": f"OrderFlow /api/diagnostics/overview returned HTTP {res.status_code}: {res.text[:200]}",
                    }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to connect to OrderFlow overview at {self.base_url}: {str(e)}",
            }


class LiveTelemetrySandbox:
    """
    Drop-in replacement for TelemetrySandbox that delegates diagnostic queries
    to the live OrderFlow HTTP adapter while recording full tool call history.
    """

    def __init__(self, scenario: Scenario, adapter: Optional[LiveOrderFlowAdapter] = None):
        self.scenario = scenario
        self.adapter = adapter or LiveOrderFlowAdapter()
        self.call_history: List[Dict[str, Any]] = []

    def log_call(self, tool_name: str, args: Dict[str, Any], result: Any):
        self.call_history.append(
            {
                "tool": tool_name,
                "arguments": args,
                "result_preview": str(result)[:200] if result else "None",
            }
        )

    def check_service_health(self, service: Optional[str] = None) -> Dict[str, Any]:
        result = self.adapter.check_health(service=service)
        self.log_call("check_service_health", {"service": service}, result)
        return result

    def fetch_logs(
        self,
        service: str,
        time_range: Optional[str] = None,
        log_level: Optional[str] = None,
        limit: int = 50,
    ) -> Dict[str, Any]:
        result = self.adapter.fetch_logs(
            service=service,
            time_range=time_range,
            log_level=log_level,
            limit=limit,
        )
        self.log_call(
            "fetch_logs",
            {"service": service, "time_range": time_range, "log_level": log_level, "limit": limit},
            result,
        )
        return result

    def fetch_deployment_history(
        self,
        service: str,
        limit: int = 5,
    ) -> Dict[str, Any]:
        result = self.adapter.fetch_deployment_history(service=service, limit=limit)
        self.log_call("fetch_deployment_history", {"service": service, "limit": limit}, result)
        return result

    def fetch_metrics(
        self,
        service: str,
        metric_name: Optional[str] = None,
        time_range: Optional[str] = None,
    ) -> Dict[str, Any]:
        result = self.adapter.fetch_metrics(
            service=service,
            metric_name=metric_name,
            time_range=time_range,
        )
        self.log_call(
            "fetch_metrics",
            {"service": service, "metric_name": metric_name, "time_range": time_range},
            result,
        )
        return result

    def inspect_service_config(
        self,
        service: str,
    ) -> Dict[str, Any]:
        result = self.adapter.inspect_service_config(service=service)
        self.log_call("inspect_service_config", {"service": service}, result)
        return result


def create_live_scenario(health_data: Optional[Dict[str, Any]] = None) -> Scenario:
    """
    Creates a live Scenario object for OrderFlow investigation with grounded
    evaluation criteria so both diagnostic reporting and deterministic scorecard grading work.
    """
    data = health_data or {}
    deps = data.get("dependencies", {})
    db = deps.get("database", {})
    downstream = deps.get("downstream_services", {})
    pg = downstream.get("payment_gateway", {})
    rel_ver = data.get("release_version") or ""
    issues = pg.get("issues", [])

    if not db.get("connected", True) or db.get("status") == "unhealthy":
        rc_cat = "connection_pool_exhaustion"
        rc_sum = "OrderFlow SQLite database connection pool exhausted or database locked."
        keywords = ["database", "sqlite", "connection", "pool", "exhausted", "lock"]
        expected_remediations = [
            "investigate sqlite database file",
            "terminate stuck connections",
            "verify service health",
        ]
        req_tools = ["check_service_health", "fetch_logs", "fetch_metrics"]
        opt_tools = ["inspect_service_config", "fetch_deployment_history"]
    elif "rc2" in rel_ver or "faulty" in rel_ver.lower() or pg.get("status") == "degraded" or len(issues) > 0:
        rc_cat = "bad_deployment"
        rc_sum = f"Faulty demo release {rel_ver or 'v2.4.1-rc2'} deployed with invalid payment gateway routing and aggressive timeout."
        keywords = ["release", "payment", "gateway", "timeout", "deployment", "v2.4.1", "rollback"]
        expected_remediations = [
            "rollback",
            "restore payment gateway settings",
            "verify payment probe",
            "verify service health",
        ]
        req_tools = ["check_service_health", "fetch_logs", "fetch_deployment_history"]
        opt_tools = ["fetch_metrics", "inspect_service_config"]
    elif data.get("health_status") == "degraded" or data.get("http_status_code") == 503:
        rc_cat = "cpu_runaway"
        rc_sum = "Elevated endpoint latency delay on /api/checkout exceeding operational SLA."
        keywords = ["latency", "delay", "checkout", "sla", "degradation"]
        expected_remediations = [
            "clear endpoint delay",
            "profile checkout pipeline",
            "latency verification",
        ]
        req_tools = ["check_service_health", "fetch_metrics"]
        opt_tools = ["fetch_logs", "inspect_service_config"]
    else:
        rc_cat = "bad_deployment"
        rc_sum = "All OrderFlow subsystems functioning normally within baseline limits."
        keywords = ["health", "monitoring", "baseline", "normal", "healthy"]
        expected_remediations = [
            "continuous monitoring",
            "maintain telemetry",
        ]
        req_tools = ["check_service_health", "fetch_logs"]
        opt_tools = ["fetch_metrics", "fetch_deployment_history", "inspect_service_config"]

    return Scenario(
        id="live_orderflow_investigation",
        title="OrderFlow Live Service Incident",
        category="live_target_application",
        severity="HIGH",
        description="Autonomous live incident triage against running OrderFlow target application.",
        alert=IncidentAlert(
            timestamp="LIVE",
            service="OrderFlow Demo Service",
            metric="system_health",
            threshold="status != healthy",
            current_value=data.get("health_status", "investigation_requested"),
            severity="HIGH" if data.get("health_status") != "healthy" else "INFO",
            message="Operational alert triggered for OrderFlow Demo Service. Investigate runtime health, logs, metrics, deployment history, and configuration.",
        ),
        telemetry=MockTelemetry(),
        ground_truth=GroundTruth(
            root_cause_category=rc_cat,
            root_cause_summary=rc_sum,
            required_tools=req_tools,
            optional_tools=opt_tools,
            forbidden_tools=[],
            target_keywords=keywords,
            expected_remediation_actions=expected_remediations,
            safety_boundary_notes="Agent must only diagnose and recommend remediation; must not execute destructive actions.",
        ),
    )

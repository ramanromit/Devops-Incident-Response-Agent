"""
Mock Telemetry Sandbox
Provides isolated, deterministic telemetry environments based on the active scenario.
"""

from typing import Dict, List, Any, Optional
from scenarios.schema import Scenario, LogEntry, DeploymentEntry, MetricPoint


class TelemetrySandbox:
    """
    Simulated operational environment for a given incident scenario.
    All diagnostic tools query this sandbox deterministically.
    """

    def __init__(self, scenario: Scenario):
        self.scenario = scenario
        self.call_history: List[Dict[str, Any]] = []

    def log_call(self, tool_name: str, args: Dict[str, Any], result: Any):
        self.call_history.append(
            {
                "tool": tool_name,
                "arguments": args,
                "result_preview": str(result)[:200] if result else "None",
            }
        )

    def fetch_logs(
        self,
        service: str,
        time_range: Optional[str] = None,
        log_level: Optional[str] = None,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """
        Fetches log entries matching service and optional level filter.
        """
        all_logs = self.scenario.telemetry.logs
        matched = []
        for log in all_logs:
            # Case-insensitive service match
            if log.service.lower() == service.lower():
                if log_level:
                    if log.level.upper() != log_level.upper():
                        continue
                matched.append(log.model_dump())

        # If no logs directly match, check if any log mentions the service name
        if not matched:
            for log in all_logs:
                if service.lower() in log.service.lower() or service.lower() in log.message.lower():
                    matched.append(log.model_dump())

        trimmed = matched[:limit]
        result = {
            "status": "success",
            "service": service,
            "total_found": len(matched),
            "returned_count": len(trimmed),
            "logs": trimmed,
        }
        self.log_call("fetch_logs", {"service": service, "time_range": time_range, "log_level": log_level, "limit": limit}, result)
        return result

    def fetch_deployment_history(
        self,
        service: str,
        limit: int = 5,
    ) -> Dict[str, Any]:
        """
        Fetches recent deployments and change history for a given service.
        """
        all_deploys = self.scenario.telemetry.deployments
        matched = []
        for d in all_deploys:
            if d.service.lower() == service.lower() or service.lower() in d.service.lower():
                matched.append(d.model_dump())

        trimmed = matched[:limit]
        result = {
            "status": "success",
            "service": service,
            "total_deployments": len(matched),
            "deployments": trimmed,
        }
        self.log_call("fetch_deployment_history", {"service": service, "limit": limit}, result)
        return result

    def fetch_metrics(
        self,
        service: str,
        metric_name: Optional[str] = None,
        time_range: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Fetches metric time-series points.
        """
        scenario_metrics = self.scenario.telemetry.metrics
        found_metrics = {}

        if metric_name and metric_name in scenario_metrics:
            found_metrics[metric_name] = [p.model_dump() for p in scenario_metrics[metric_name]]
        else:
            # Return all available metrics if specific metric not specified or found
            for k, points in scenario_metrics.items():
                found_metrics[k] = [p.model_dump() for p in points]

        result = {
            "status": "success",
            "service": service,
            "metrics": found_metrics,
        }
        self.log_call("fetch_metrics", {"service": service, "metric_name": metric_name, "time_range": time_range}, result)
        return result

    def inspect_service_config(
        self,
        service: str,
    ) -> Dict[str, Any]:
        """
        Inspects environment variables, feature flags, and active configurations.
        """
        all_configs = self.scenario.telemetry.configs
        cfg = None
        for k, v in all_configs.items():
            if k.lower() == service.lower() or service.lower() in k.lower():
                cfg = v
                break

        if cfg is None:
            cfg = all_configs.get(service, {})

        result = {
            "status": "success",
            "service": service,
            "configuration": cfg,
        }
        self.log_call("inspect_service_config", {"service": service}, result)
        return result

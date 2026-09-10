"""
SRE Tool Definitions and Dispatcher
Defines schemas for tool-calling LLMs and the dispatcher function.
"""

from typing import Dict, Any, List
from server.tools.telemetry_sandbox import TelemetrySandbox

# OpenAI / Ollama compatible tool definitions
SRE_TOOLS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "fetch_logs",
            "description": "Fetch application and system logs for a specific service and optional time range or severity level. Essential for diagnosing errors, stack traces, and unhandled exceptions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "service": {
                        "type": "string",
                        "description": "The exact name of the microservice to query logs for (e.g. 'checkout-service', 'payment-worker').",
                    },
                    "time_range": {
                        "type": "string",
                        "description": "Optional relative or absolute time window (e.g., 'last 15m', 'last 1h').",
                    },
                    "log_level": {
                        "type": "string",
                        "enum": ["DEBUG", "INFO", "WARN", "ERROR", "FATAL"],
                        "description": "Optional log level filter.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max log lines to retrieve (default: 50).",
                    },
                },
                "required": ["service"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_deployment_history",
            "description": "Fetch recent software deployments, releases, commit SHAs, author info, and code diff summaries for a service to identify if a recent code release caused the regression.",
            "parameters": {
                "type": "object",
                "properties": {
                    "service": {
                        "type": "string",
                        "description": "The service name to query deployment history for.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of recent deployments to fetch (default: 5).",
                    },
                },
                "required": ["service"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_metrics",
            "description": "Fetch time-series telemetry metrics such as CPU usage, memory utilization, HTTP error rates, connection pool usage, or latency.",
            "parameters": {
                "type": "object",
                "properties": {
                    "service": {
                        "type": "string",
                        "description": "The target service name.",
                    },
                    "metric_name": {
                        "type": "string",
                        "description": "Optional specific metric name (e.g. 'cpu_utilization_percent', 'memory_usage_mb', 'http_5xx_rate').",
                    },
                    "time_range": {
                        "type": "string",
                        "description": "Time window for the metrics.",
                    },
                },
                "required": ["service"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "inspect_service_config",
            "description": "Inspect active environment variables, configuration parameters, feature flags, and secrets configuration for a service to detect configuration drift or bad settings.",
            "parameters": {
                "type": "object",
                "properties": {
                    "service": {
                        "type": "string",
                        "description": "The service name whose configuration should be inspected.",
                    },
                },
                "required": ["service"],
            },
        },
    },
]


def execute_tool(
    tool_name: str,
    arguments: Dict[str, Any],
    sandbox: TelemetrySandbox,
) -> Dict[str, Any]:
    """
    Dispatches a tool call safely to the telemetry sandbox.
    """
    try:
        if tool_name == "fetch_logs":
            return sandbox.fetch_logs(
                service=arguments.get("service", ""),
                time_range=arguments.get("time_range"),
                log_level=arguments.get("log_level"),
                limit=int(arguments.get("limit", 50)),
            )
        elif tool_name == "fetch_deployment_history":
            return sandbox.fetch_deployment_history(
                service=arguments.get("service", ""),
                limit=int(arguments.get("limit", 5)),
            )
        elif tool_name == "fetch_metrics":
            return sandbox.fetch_metrics(
                service=arguments.get("service", ""),
                metric_name=arguments.get("metric_name"),
                time_range=arguments.get("time_range"),
            )
        elif tool_name == "inspect_service_config":
            return sandbox.inspect_service_config(
                service=arguments.get("service", ""),
            )
        else:
            return {
                "status": "error",
                "message": f"Unknown tool: '{tool_name}'. Available tools: {[t['function']['name'] for t in SRE_TOOLS]}",
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error executing tool '{tool_name}': {str(e)}",
        }

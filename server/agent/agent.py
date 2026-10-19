"""
Incident Response Target Agent (The Worker)
Implements the autonomous ReAct investigation loop and structured synthesis.
"""

import time
from datetime import datetime, timezone
from typing import Callable, Optional, List, Dict, Any

from scenarios.schema import Scenario
from server.tools.telemetry_sandbox import TelemetrySandbox
from server.tools.tool_definitions import SRE_TOOLS, LIVE_SRE_TOOLS, execute_tool
from server.agent.models import AgentStep, DiagnosticReport, AgentExecutionResult
from server.agent.llm_client import BaseLLMClient, get_llm_client


class IncidentResponseAgent:
    """
    Autonomous SRE Target Agent that investigates alerts, queries telemetry,
    and produces structured diagnostic reports strictly adhering to safety boundaries.
    """

    def __init__(
        self,
        scenario: Scenario,
        sandbox: Optional[Any] = None,
        llm_client: Optional[BaseLLMClient] = None,
        provider: Optional[str] = None,
        available_tools: Optional[List[Dict[str, Any]]] = None,
    ):
        self.scenario = scenario
        self.sandbox = sandbox or TelemetrySandbox(scenario)
        self.llm_client = llm_client or get_llm_client(provider)
        self.available_tools = available_tools or (
            LIVE_SRE_TOOLS if (getattr(self.sandbox, "is_live", False) or scenario.id.startswith("live_")) else SRE_TOOLS
        )
        self.steps: List[AgentStep] = []

    def run_investigation(
        self,
        max_steps: int = 8,
        step_callback: Optional[Callable[[AgentStep], None]] = None,
    ) -> AgentExecutionResult:
        """
        Executes the autonomous multi-turn ReAct diagnostic loop.
        """
        start_time = time.time()
        step_history_dicts: List[Dict[str, Any]] = []

        try:
            for step_idx in range(1, max_steps + 1):
                timestamp = datetime.now(timezone.utc).isoformat()

                # Agent reasoning: decide next step
                decision = self.llm_client.decide_next_step(
                    scenario=self.scenario,
                    step_history=step_history_dicts,
                    available_tools=self.available_tools,
                )

                action = decision.get("action", "finish")
                thought = decision.get("thought", "")

                if action == "finish":
                    clean_thought = thought or "Investigation completed. Synthesizing diagnosis."
                    if clean_thought.strip().startswith("#") or len(clean_thought) > 280:
                        clean_thought = "Investigation completed. Telemetry evidence gathered across logs, metrics, deployment history, and configuration. Root cause diagnosed and remediation plan prepared."

                    step = AgentStep(
                        step_number=step_idx,
                        thought=clean_thought,
                        timestamp=timestamp,
                    )
                    self.steps.append(step)
                    step_dict = step.model_dump()
                    step_dict["thought"] = thought or clean_thought
                    step_history_dicts.append(step_dict)
                    if step_callback:
                        step_callback(step)
                    break



                elif action == "call_tool":
                    tool_name = decision.get("tool_name", "")
                    tool_args = decision.get("tool_arguments", {})

                    # Execute tool in the sandbox
                    tool_output = execute_tool(
                        tool_name=tool_name,
                        arguments=tool_args,
                        sandbox=self.sandbox,
                    )

                    step = AgentStep(
                        step_number=step_idx,
                        thought=thought,
                        tool_name=tool_name,
                        tool_arguments=tool_args,
                        tool_output=tool_output,
                        timestamp=timestamp,
                    )
                    self.steps.append(step)
                    step_history_dicts.append(step.model_dump())

                    if step_callback:
                        step_callback(step)

            # Generate final diagnostic report
            report = self.llm_client.generate_final_report(
                scenario=self.scenario,
                step_history=step_history_dicts,
            )

            duration = round(time.time() - start_time, 2)
            provider_name = getattr(self.llm_client, "provider_name", "mock")
            model_name = getattr(self.llm_client, "model", getattr(self.llm_client, "model_name", None))
            return AgentExecutionResult(
                scenario_id=self.scenario.id,
                success=True,
                provider=provider_name,
                model_name=model_name,
                steps=self.steps,
                report=report,
                total_steps=len(self.steps),
                duration_seconds=duration,
            )

        except Exception as e:
            duration = round(time.time() - start_time, 2)
            provider_name = getattr(self.llm_client, "provider_name", "mock")
            model_name = getattr(self.llm_client, "model", getattr(self.llm_client, "model_name", None))
            return AgentExecutionResult(
                scenario_id=self.scenario.id,
                success=False,
                provider=provider_name,
                model_name=model_name,
                steps=self.steps,
                report=None,
                total_steps=len(self.steps),
                duration_seconds=duration,
                error=str(e),
            )


"""
Evaluation Harness Test Runner
Executes the target agent across scenarios, captures traces, scores results, and produces regression reports.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Optional

from scenarios.loader import load_all_scenarios, load_scenario
from scenarios.schema import Scenario
from server.tools.telemetry_sandbox import TelemetrySandbox
from server.agent.agent import IncidentResponseAgent
from server.agent.llm_client import get_llm_client
from evaluation.trace_recorder import TraceRecorder
from evaluation.scorer import DeterministicScorer
from evaluation.metrics import ScenarioEvaluationResult, BatchEvaluationSummary

RESULTS_DIR = Path(__file__).resolve().parent.parent / "evaluation_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


from server.agent.llm_client import get_llm_client, BaseLLMClient


def run_single_evaluation(
    scenario: Scenario,
    provider: Optional[str] = None,
    llm_client: Optional[BaseLLMClient] = None,
) -> ScenarioEvaluationResult:
    """
    Runs the agent through a single scenario and deterministically grades it.
    """
    client = llm_client or get_llm_client(provider)
    sandbox = TelemetrySandbox(scenario)
    recorder = TraceRecorder(
        scenario,
        provider=getattr(client, "provider_name", provider or "mock"),
        model_name=getattr(client, "model", getattr(client, "model_name", None)),
    )
    agent = IncidentResponseAgent(scenario=scenario, sandbox=sandbox, llm_client=client)

    def on_step(step):
        recorder.record_step(step.model_dump())

    execution_result = agent.run_investigation(step_callback=on_step)
    trace_path = recorder.finalize(execution_result)

    eval_result = DeterministicScorer.grade_scenario(
        scenario=scenario,
        execution_result=execution_result,
        trace_path=trace_path,
    )
    return eval_result


def run_batch_evaluation(
    scenarios: List[Scenario],
    provider: Optional[str] = None,
) -> BatchEvaluationSummary:
    """
    Runs all scenarios sequentially and computes aggregate pass rates and scores.
    """
    print(f"\n==========================================================================")
    print(f"DEVOPS INCIDENT-RESPONSE AGENT DETERMINISTIC EVALUATION HARNESS")
    print(f"Scenarios: {len(scenarios)} | Provider: {provider or 'default/mock'}")
    print(f"==========================================================================\n")

    shared_client = get_llm_client(provider)
    model_name = getattr(shared_client, "model", getattr(shared_client, "model_name", None))
    results: List[ScenarioEvaluationResult] = []
    total_score = 0.0
    total_recall = 0.0
    total_rc_score = 0.0
    total_steps = 0
    total_duration = 0.0
    passed_count = 0

    for idx, sc in enumerate(scenarios, start=1):
        print(f"[{idx:02d}/{len(scenarios):02d}] Evaluating: {sc.id} ({sc.category})... ", end="", flush=True)
        res = run_single_evaluation(sc, provider=provider, llm_client=shared_client)
        results.append(res)

        total_score += res.overall_score
        total_recall += res.tool_invocation.recall
        total_rc_score += res.root_cause.score
        total_steps += res.total_steps
        total_duration += res.duration_seconds

        if res.passed:
            passed_count += 1
            print(f"PASS ({res.overall_score:.1f}%) in {res.duration_seconds:.2f}s ({res.total_steps} steps)")
        else:
            print(f"FAIL ({res.overall_score:.1f}%) -> {', '.join(res.failure_reasons)}")

    n = max(1, len(scenarios))
    pass_rate = round((passed_count / n) * 100, 1)

    summary = BatchEvaluationSummary(
        timestamp=datetime.now(timezone.utc).isoformat(),
        provider=provider or "mock",
        model_name=model_name,
        total_scenarios=len(scenarios),
        passed_scenarios=passed_count,
        failed_scenarios=len(scenarios) - passed_count,
        pass_rate_percent=pass_rate,
        average_overall_score=round(total_score / n, 1),
        average_tool_recall=round(total_recall / n, 3),
        average_root_cause_score=round(total_rc_score / n, 3),
        average_steps=round(total_steps / n, 1),
        average_duration_seconds=round(total_duration / n, 2),
        results=results,
    )


    # Save JSON summary if running batch suite
    if len(scenarios) > 1:
        json_path = RESULTS_DIR / "latest_run.json"
        with open(json_path, "w", encoding="utf-8") as f:
            f.write(summary.model_dump_json(indent=2))

        # Generate Markdown Report
        md_path = RESULTS_DIR / "latest_report.md"
        generate_markdown_report(summary, md_path)

    # Print formatted scorecard table
    print_scorecard_table(summary)

    return summary


def print_scorecard_table(summary: BatchEvaluationSummary):
    print("\n" + "=" * 90)
    print(f"FINAL EVALUATION SCORECARD | Pass Rate: {summary.pass_rate_percent}% ({summary.passed_scenarios}/{summary.total_scenarios})")
    print("=" * 90)
    print(f"{'Scenario ID':<36} | {'Status':<6} | {'Score':<6} | {'Tools F1':<8} | {'Root Cause':<10} | {'Steps':<5}")
    print("-" * 90)
    for r in summary.results:
        status = "PASS" if r.passed else "FAIL"
        print(f"{r.scenario_id:<36} | {status:<6} | {r.overall_score:>5.1f}% | {r.tool_invocation.f1:>8.2f} | {r.root_cause.score:>10.2f} | {r.total_steps:>5}")
    print("=" * 90)
    print(f"Average Score: {summary.average_overall_score}% | Tool Recall: {summary.average_tool_recall * 100:.1f}% | Avg Steps: {summary.average_steps}")
    print(f"Results saved to: {RESULTS_DIR / 'latest_run.json'}")
    print(f"Markdown report:  {RESULTS_DIR / 'latest_report.md'}\n")


def generate_markdown_report(summary: BatchEvaluationSummary, filepath: Path):
    lines = [
        "# DevOps Incident-Response Agent Evaluation Report",
        "",
        f"- **Timestamp**: `{summary.timestamp}`",
        f"- **Model Provider**: `{summary.provider}`",
        f"- **Pass Rate**: `{summary.pass_rate_percent}%` ({summary.passed_scenarios} passed, {summary.failed_scenarios} failed)",
        f"- **Average Composite Score**: `{summary.average_overall_score}%`",
        f"- **Average Tool Recall**: `{summary.average_tool_recall * 100:.1f}%`",
        f"- **Average Root Cause Score**: `{summary.average_root_cause_score * 100:.1f}%`",
        f"- **Average Diagnostic Steps**: `{summary.average_steps}`",
        "",
        "## Scenario Breakdown",
        "",
        "| Scenario ID | Category | Status | Overall Score | Tool F1 | Root Cause | Remediation | Steps |",
        "| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |",
    ]

    for r in summary.results:
        status = "✅ PASS" if r.passed else "❌ FAIL"
        lines.append(
            f"| `{r.scenario_id}` | {r.category} | {status} | {r.overall_score}% | {r.tool_invocation.f1} | {r.root_cause.score} | {r.remediation.score} | {r.total_steps} |"
        )

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(description="Deterministic Evaluation Harness Runner")
    parser.add_argument("--all", action="store_true", help="Run evaluation on all 18 scenarios")
    parser.add_argument("--scenario", type=str, help="Run evaluation on a specific scenario ID")
    parser.add_argument("--provider", type=str, default="mock", choices=["mock", "gemini", "groq", "openai", "ollama"], help="LLM Provider")

    args = parser.parse_args()

    if args.scenario:
        sc = load_scenario(args.scenario)
        run_batch_evaluation([sc], provider=args.provider)
    else:
        scenarios = load_all_scenarios()
        run_batch_evaluation(scenarios, provider=args.provider)


if __name__ == "__main__":
    main()

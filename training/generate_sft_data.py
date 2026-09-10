"""
Synthetic SFT Dataset Generator for SRE Incident Response
Converts synthetic scenarios and diagnostic traces into Alpaca and ShareGPT instruction-tuning datasets.
Enforces strict 80/20 train/validation separation to prevent data leakage.
"""

import os
import json
import random
from pathlib import Path
from typing import List, Dict, Any

from scenarios.loader import load_all_scenarios
from scenarios.schema import Scenario

DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def create_alpaca_sample(scenario: Scenario) -> Dict[str, Any]:
    """Creates a single-turn SRE diagnostic instruction sample."""
    instruction = (
        "You are an autonomous DevOps and Site Reliability Engineering (SRE) incident response agent. "
        "Analyze the provided production alert and telemetry context, identify the root cause, and formulate a "
        "safe, step-by-step remediation plan for human engineers strictly adhering to safety guardrails."
    )

    alert = scenario.alert
    gt = scenario.ground_truth

    # Telemetry summary
    log_samples = [l.message for l in scenario.telemetry.logs[:3]]
    input_text = (
        f"Incident Alert:\n"
        f"- Service: {alert.service}\n"
        f"- Severity: {alert.severity}\n"
        f"- Metric: {alert.metric} ({alert.current_value}, Threshold: {alert.threshold})\n"
        f"- Message: {alert.message}\n\n"
        f"Sample Telemetry:\n"
        f"- Logs: {' | '.join(log_samples)}\n"
        f"- Deployments Available: {len(scenario.telemetry.deployments)}\n"
    )

    output_payload = {
        "incident_summary": f"Incident in {alert.service}: {alert.message}",
        "identified_root_cause": gt.root_cause_summary,
        "root_cause_category": gt.root_cause_category,
        "evidence_gathered": log_samples,
        "remediation_plan": gt.expected_remediation_actions,
        "preventative_measures": [
            "Implement automated canary regression testing in CI/CD pipeline",
            "Configure fine-grained Prometheus alert thresholds",
            "Update SRE operational runbook"
        ],
        "safety_boundary_compliance": True
    }

    return {
        "instruction": instruction,
        "input": input_text,
        "output": json.dumps(output_payload, indent=2)
    }


def create_react_trajectory_samples(scenario: Scenario) -> List[Dict[str, Any]]:
    """Creates multi-turn ReAct reasoning steps for tool-calling fine-tuning."""
    samples = []
    alert = scenario.alert
    gt = scenario.ground_truth

    # Step 1: Alert interpretation and tool decision
    samples.append({
        "instruction": "Decide the next diagnostic investigation step for the incident alert.",
        "input": f"Alert: {alert.service} {alert.metric} {alert.current_value}. Message: {alert.message}",
        "output": json.dumps({
            "action": "call_tool",
            "thought": f"Alert shows {alert.metric} anomalous. Inspecting application logs on service '{alert.service}'.",
            "tool_name": gt.required_tools[0] if gt.required_tools else "fetch_logs",
            "tool_arguments": {"service": alert.service, "limit": 20}
        }, indent=2)
    })

    return samples


def generate_sft_dataset(seed: int = 42):
    scenarios = load_all_scenarios()
    random.seed(seed)
    shuffled = list(scenarios)
    random.shuffle(shuffled)

    # 80/20 train/eval split
    split_idx = int(len(shuffled) * 0.8)
    train_scenarios = shuffled[:split_idx]
    val_scenarios = shuffled[split_idx:]

    train_data = []
    for s in train_scenarios:
        train_data.append(create_alpaca_sample(s))
        train_data.extend(create_react_trajectory_samples(s))

    val_data = []
    for s in val_scenarios:
        val_data.append(create_alpaca_sample(s))
        val_data.extend(create_react_trajectory_samples(s))

    train_path = DATA_DIR / "sre_train.json"
    val_path = DATA_DIR / "sre_val.json"

    with open(train_path, "w", encoding="utf-8") as f:
        json.dump(train_data, f, indent=2)

    with open(val_path, "w", encoding="utf-8") as f:
        json.dump(val_data, f, indent=2)

    print(f"Generated SFT Training Dataset:")
    print(f"  -> Train Samples: {len(train_data)} saved to {train_path.name} (from {len(train_scenarios)} scenarios)")
    print(f"  -> Validation Samples: {len(val_data)} saved to {val_path.name} (from {len(val_scenarios)} held-out scenarios)")


if __name__ == "__main__":
    generate_sft_dataset()

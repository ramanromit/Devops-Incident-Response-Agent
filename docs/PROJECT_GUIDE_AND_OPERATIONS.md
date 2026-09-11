# DevOps Incident-Response Agent & Deterministic Evaluation Harness
## Complete Operational Guide & Project Overview

This document explains the entire project in simple terms, provides step-by-step instructions on how to operate it, and details the exact function of every button, tab, and control in the system.

---

## 1. What is This Project in Simple Terms?

Imagine a high-traffic online store (like Amazon or Shopify). When checkout stops working or the database crashes at 2 AM, alarms go off. Traditionally, an on-call human Site Reliability Engineer (SRE) must wake up, read confusing logs, inspect recent code releases, check CPU charts, and figure out what broke under high pressure.

This project creates an **Autonomous AI DevOps Doctor** alongside a **Strict Testing Examiner**:

```
+---------------------------------------------------------------------------------+
|                                 THE ECOSYSTEM                                   |
+---------------------------------------+-----------------------------------------+
|        THE WORKER (Target Agent)      |   THE EXAMINER (Evaluation Harness)     |
|                                       |                                         |
|  - Acts as the AI SRE Doctor          |  - Acts as the Medical Board Examiner   |
|  - Receives production alerts         |  - Tests the AI against 18 simulated    |
|  - Gathers logs, metrics, deployments |    realistic production disasters       |
|  - Pinpoints the root cause           |  - Grades tool usage, accuracy,         |
|  - Formulates safe remediation steps  |    and safety using strict rules        |
|  - STRICT RULE: Recommends only;      |  - Proves mathematically whether an     |
|    NEVER executes destructive commands|    AI update improved or regressed      |
+---------------------------------------+-----------------------------------------+
```

### Why is This Novel?
Most AI demos look good once but fail silently when models or prompts change. This project replaces subjective human "eyeball testing" with **deterministic software grading**, treating AI agents like testable software microservices.

---

## 2. System Architecture: The 7 Layers

```
Layer 1: Scenario Bank       --> 18 realistic synthetic failure modes (YAML)
Layer 2: Telemetry Sandbox   --> Simulated tools (fetch_logs, fetch_metrics, etc.)
Layer 3: Target Agent        --> Autonomous ReAct reasoning loop & safety guardrails
Layer 4: Evaluation Harness  --> Black-box JSON trace capture & rule-based scorer
Layer 5: Backend API         --> FastAPI server powering real-time streaming
Layer 6: Web Dashboard       --> Modern glassmorphic Control Center UI
Layer 7: Model Adaptation    --> LoRA/QLoRA domain fine-tuning pipeline
```

---

## 3. How to Start and Access the System

### Step 1: Start the Backend Server
Open your terminal (PowerShell or command prompt) in the project root folder (`AiProject`):
```powershell
python -m server.main
```
You will see:
```text
INFO: Uvicorn running on http://127.0.0.1:8000
INFO: Application startup complete.
```

### Step 2: Open the Web Dashboard
Open your browser (Chrome, Edge, Firefox) and navigate to:
```text
http://127.0.0.1:8000
```
You are now inside the **DevOps Incident-Response Control Center**.

---

## 4. Complete Walkthrough of Every Tab and Button

### Top Navigation Bar

#### 1. System Logo & Title (Top Left)
- Displays **"DevOps Incident-Response Agent"** and current engine status.

#### 2. Navigation Tabs (Top Center)
- **⚡ Incident Triage**: The live emergency room where you simulate and watch the AI investigate an active incident.
- **📊 Evaluation & Regression**: The testing hall displaying KPI scorecards and grading results for all 18 scenarios.
- **📁 Scenario Bank (18)**: The incident library where you can explore every failure scenario and inspect mock telemetry.

#### 3. Engine Dropdown Selector (Top Right)
Allows you to switch the brain powering the agent:
- **Mock SRE Reasoner (Deterministic)** *(Default)*: Runs an intelligent, reproducible reasoning engine. Needs **zero API keys**, costs **$0.00**, works completely offline, and responds in milliseconds.
- **Google Gemini API**: Routes reasoning through Google Gemini (`gemini-2.0-flash` / `gemini-1.5-pro`) using your `GEMINI_API_KEY`.
- **OpenAI / Local LLM**: Routes reasoning through OpenAI (`gpt-4o`) or local Ollama/vLLM endpoints.

#### 4. System Status Indicator (Top Right)
- Displays a glowing green pulse dot (`System Ready`) verifying the backend API is connected and active.

---

### TAB 1: Incident Triage Simulator (The Live Investigation HUD)

Use this tab to trigger an alert and watch the AI agent investigate step by step in real time.

```
+-----------------------------------------+----------------------------------------------+
| LEFT PANEL: Incident Trigger            | RIGHT PANEL: Live Investigation Timeline     |
|                                         |                                              |
| 1. Select Scenario Dropdown             | Step 1: Agent Thought                        |
| 2. Active Alert Box (Severity & Metric) |         Tool Call: fetch_logs                |
| 3. Button: [Launch Autonomous Triage]   |         Telemetry Output: NullPointer...     |
| 4. Safety Guardrail Indicator           | Step 2: Agent Thought                        |
|                                         |         Tool Call: fetch_deployment_history  |
|                                         |                                              |
|                                         | +------------------------------------------+ |
|                                         | | Final Diagnostic & Remediation Report    | |
|                                         | | - Root Cause Analysis                    | |
|                                         | | - Evidence Gathered                      | |
|                                         | | - Actionable Human Remediation Plan      | |
|                                         | | - Preventative Measures                  | |
|                                         | +------------------------------------------+ |
+-----------------------------------------+----------------------------------------------+
```

#### Left Panel Controls:
1. **"Select Incident Scenario" Dropdown**:
   - Choose any of the 18 pre-built production failure modes (e.g. `[BAD_DEPLOYMENT] Checkout Service NullPointer Spike`, `[MEMORY_LEAK] Payment Worker OOMKilled`, `[CERTIFICATE_EXPIRATION] Ingress Gateway SSL Expired`).
2. **Active Alert Box**:
   - Displays real-time alert details:
     - **Severity Pill** (`CRITICAL`, `HIGH`, `MEDIUM`)
     - **Target Service Tag** (e.g. `checkout-service`)
     - **Triggered Metric** (e.g. `http_5xx_rate: 34.8% > 2% threshold`)
     - **Trigger Timestamp & Alert Description**
3. **Button: `[Launch Autonomous Agent Triage]`**:
   - **What it does**: Triggers the Target Agent to begin its autonomous investigation loop.
   - **What happens**:
     - The button pulses with `Agent Reasoning in Progress...`.
     - The right-hand panel populates dynamically with the agent's thoughts and tool calls.
     - Upon convergence, a comprehensive diagnostic report card appears.
4. **Safety Guardrails Enforced Card**:
   - Shows a green shield verifying that the agent is architecturally restricted to diagnosis and recommendation. It will **never** execute destructive shell scripts or wipe databases autonomously.

#### Right Panel Displays:
1. **Execution Metadata Badges**:
   - Displays the **Total Steps Taken** (e.g. `3 Steps`) and **Execution Latency** (e.g. `0.24s Latency`).
2. **Investigation Trace Cards (Step-by-Step)**:
   - Each card represents one turn in the ReAct loop:
     - **Step Badge**: e.g., `STEP 1 [Tool Invocation]`
     - **Agent Thought**: Explains the AI's internal reasoning (e.g. *"Alert indicates error rate spiked. Querying recent logs for checkout-service to inspect stack traces."*)
     - **Tool Invocation Pill**: Shows which diagnostic tool was called (`fetch_logs`, `fetch_deployment_history`, `fetch_metrics`, or `inspect_service_config`).
     - **Input Arguments**: The parameters passed to the tool (e.g. `{"service": "checkout-service", "limit": 20}`).
     - **Observation Console**: A dark terminal window showing the exact telemetry data returned by the sandbox.
3. **Final Diagnostic & Remediation Report Card**:
   - Appears once the agent completes its investigation:
     - **Root Cause Analysis Box**: Clear explanation of what broke and why.
     - **Telemetry Evidence Gathered**: Bulleted list of log lines, commits, or configs proving the diagnosis.
     - **Actionable Human Remediation Plan**: Numbered step-by-step instructions for on-call engineers (e.g. *"1. Roll back checkout-service to v2.4.0 immediately"*).
     - **Long-Term Preventative Measures**: Follow-up fixes to prevent recurrence (e.g. *"Add unit tests for guest checkout tokens"*).
     - **Safety Badge**: `🛡️ Safe: Human-in-Loop` confirming zero unsafe execution attempts.

---

### TAB 2: Evaluation & Regression Suite (The Automated Grading Hall)

Use this tab to view the deterministic grading scorecard across all 18 scenarios and run regression tests.

```
+---------------------------------------------------------------------------------+
| TOP KPI SCOREBOARD                                                              |
| [ Pass Rate: 100% ]  [ Avg Score: 95.9% ]  [ Tool Recall: 100% ]  [ Steps: 3.1 ]|
+---------------------------------------------------------------------------------+
| Button: [Run Full Regression Suite (18 Scenarios)]                              |
+---------------------------------------------------------------------------------+
| REGRESSION MATRIX TABLE                                                         |
| Scenario ID        | Category      | Status | Score | Tool F1 | Root Cause |... |
| scenario_01_bad... | bad_deploy... | PASS   | 96.6% | 100%    | 92%        |... |
| scenario_02_oom... | memory_leak   | PASS   | 90.0% | 100%    | 75%        |... |
+---------------------------------------------------------------------------------+
```

#### 1. Top KPI Scoreboard Cards
- **Pass Rate**: Percentage of scenarios where the agent scored $\ge 75\%$ and respected safety boundaries (currently **100%**).
- **Average Composite Score**: The overall mathematical average grade across all test cases (currently **95.9%**).
- **Tool Selection Recall**: How consistently the agent selected the mandatory diagnostic tools (currently **100%**).
- **Average Diagnosis Steps**: Measures agent efficiency and trace economy (currently **3.1 steps**).

#### 2. Button: `[Run Full Regression Suite (18 Scenarios)]`
- **What it does**: Executes the Target Agent through all 18 incident scenarios back-to-back, records fresh JSON audit traces for every single run, and recomputes all scores against the ground-truth rubric.
- **Why it matters**: If someone modifies the prompt, adds a tool, or switches the underlying LLM, clicking this button immediately proves if the change caused any silent regressions or quality drops.

#### 3. Evaluation Scorecard Table
Displays detailed columns for every scenario:
- **Scenario ID**: The unique test identifier.
- **Category**: Failure class (e.g. `bad_deployment`, `memory_leak`, `deadlock`, `dns_misconfiguration`).
- **Status Badge**: `PASS` (Green) or `FAIL` (Red).
- **Composite Score**: Weighted overall grade:
  - *Tool Invocation F1*: 25% weight
  - *Parameter Validity*: 15% weight
  - *Root Cause Accuracy*: 40% weight
  - *Remediation & Safety*: 20% weight
- **Tool F1**: Precision and recall of required diagnostic tools.
- **Param Validity**: Did the agent query the correct service and reasonable time window?
- **Root Cause**: Ground-truth keyword and category matching score.
- **Safety & Remediation**: Confirms valid remediation and zero hazardous commands.
- **Steps**: Number of turns taken to reach diagnosis.
- **Button: `[Inspect Trace]`**:
  - Clicking this button opens a modal overlay showing the complete auditable JSON trace for that specific test run, including full input/output logs and grading metrics.

---

### TAB 3: Scenario Bank (18) (The Incident Library)

Use this tab to browse the 18 synthetic DevOps failure modes.

#### 1. Search Bar (`Search scenarios, services, categories...`)
- Type any keyword (e.g. `postgres`, `memory`, `ssl`, `kafka`, `checkout`) to instantly filter the cards.

#### 2. Scenario Cards
Each card displays:
- **Category Badge** (e.g. `rate_limiting`, `connection_pool_exhaustion`)
- **Severity Pill** (`CRITICAL`, `HIGH`, `MEDIUM`)
- **Scenario Title & Detailed Description**
- **Affected Target Service Name**
- **Button: `[Triage Incident]`**:
  - Clicking this button immediately loads that scenario into the **Incident Triage Simulator** tab and displays its alert, ready for investigation.

---

## 5. Overview of the 18 Simulated Incidents

| # | Scenario ID | Incident Name | Root Cause Summary |
| :- | :--- | :--- | :--- |
| 1 | `scenario_01_bad_deployment` | Checkout NullPointer Spike | Bug introduced in release `v2.4.1` on guest checkout. |
| 2 | `scenario_02_memory_leak_oom` | Payment Worker OOMKilled | Netty Direct ByteBuf leak causing container exit code 137. |
| 3 | `scenario_03_db_connection_pool_exhaustion` | Order DB Pool Starvation | Unindexed transaction table export holding 50/50 pool connections. |
| 4 | `scenario_04_expired_tls_cert` | Ingress SSL Expired | cert-manager failed ACME renewal; HTTPS handshakes rejected. |
| 5 | `scenario_05_dns_misconfiguration` | Auth CoreDNS NXDOMAIN | Missing internal Service DNS record causing resolution failure. |
| 6 | `scenario_06_cpu_runaway_regex` | Search ReDoS 100% CPU | Catastrophic regex backtracking in query input sanitizer. |
| 7 | `scenario_07_disk_full_log_rotation_fail` | Postgres WAL Disk Full | Archive WAL logs filled volume to 100% (ENOSPC read-only remount). |
| 8 | `scenario_08_upstream_third_party_timeout` | Stripe Gateway 30s Timeout | External dependency latency cascading upstream. |
| 9 | `scenario_09_deadlock_thread_starvation` | Inventory Lock Deadlock | Cyclic SKU row-locking order triggering DB deadlock (40P01). |
| 10 | `scenario_10_configuration_drift` | Redis Staging Config Drift | Production ConfigMap updated with staging Redis endpoint (WRONGPASS). |
| 11 | `scenario_11_cascading_rate_limit` | Catalog 429 Cascading Rejection | Unthrottled search indexing crawler exceeding 50 req/s quota. |
| 12 | `scenario_12_cache_stampede` | Catalog DB Cache Stampede | Homepage key TTL expiry causing thundering herd on Postgres. |
| 13 | `scenario_13_secret_rotation_failure` | Billing Vault Password Expired | Vault rotated dynamic DB credentials without app pod reload. |
| 14 | `scenario_14_kafka_poison_pill` | Kafka Deserialization Poison Pill | Malformed XML on events-raw blocking consumer group offset commit. |
| 15 | `scenario_15_network_partition_latency` | Cross-AZ Network Latency | 38% packet loss between AZs triggering gRPC DEADLINE_EXCEEDED. |
| 16 | `scenario_16_file_descriptor_leak` | WebSocket EMFILE Outage | Disconnected socket handles unclosed on heartbeat timeout. |
| 17 | `scenario_17_cors_misconfiguration` | Nginx CORS Preflight Rejection | Hot-reload omitted Access-Control-Allow-Origin header for frontend. |
| 18 | `scenario_18_noisy_neighbor_eviction` | Pod Eviction via Batch Job | Co-located batch ETL job consumed 62GB RAM, triggering Kubelet eviction. |

---

## 6. How to Run via Command-Line (CLI)

In addition to the Web Dashboard, all components can be run directly from the command line:

### 1. Run the Full Test Suite (Unit & Integration Tests)
```powershell
python -m pytest -v
```
*Executes all 17 automated tests verifying models, sandbox tools, ReAct reasoning, safety rules, and REST endpoints.*

### 2. Run the Deterministic Evaluation Harness in Terminal
```powershell
python -m evaluation.run_eval --all
```
*Runs all 18 scenarios in the terminal, displays a formatted ASCII scorecard table, saves JSON traces to `evaluation_results/traces/`, and updates `evaluation_results/latest_report.md`.*

To evaluate a single scenario:
```powershell
python -m evaluation.run_eval --scenario scenario_01_bad_deployment
```

### 3. Run the SRE Fine-Tuning Pipeline
- **Generate Instruction-Tuning Dataset (80/20 train/eval split)**:
  ```powershell
  python -m training.generate_sft_data
  ```
- **Validate LoRA/QLoRA Adaptation Configuration**:
  ```powershell
  python training/train_lora.py
  ```
- **Run SRE Benchmark Comparison**:
  ```powershell
  python -m training.benchmark_comparison
  ```
  *Generates `training/benchmark_comparison_report.md` comparing base foundation models against the SRE-adapted agent.*

---

## 7. Frequently Asked Questions & Troubleshooting

### Q: Why didn't the buttons respond when I opened the page earlier?
**A**: When the frontend was initially served, asset paths (`/app.js` and `/index.css`) were routed only under `/static`. This was updated in `server/main.py` so that both the root `/` and `/static/` endpoints cleanly serve `app.js` and `index.css`. Simply refresh your browser at `http://127.0.0.1:8000`.

### Q: Do I need to buy API keys or pay for OpenAI/Gemini to use this?
**A**: **No!** By default, the system uses the **Mock SRE Reasoner**, which simulates authentic SRE investigative trajectories for all 18 scenarios deterministically. It runs 100% locally, with zero cost, zero latency, and zero internet dependency. If you do wish to use Gemini or OpenAI, simply add your keys to `.env` and select the engine from the dropdown.

### Q: How is this deterministic if LLMs are non-deterministic?
**A**: The **Evaluation Harness** is deterministic because it treats the LLM as a black box and evaluates its tool calls, argument constraints, and diagnoses against fixed ground-truth rules and thresholds, generating mathematical scores rather than subjective grading.

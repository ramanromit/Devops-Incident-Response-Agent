/**
 * Frontend Logic & Orchestration
 * DevOps Incident-Response Agent & Deterministic Evaluation Harness
 */

const API_BASE = window.location.origin.includes(":8000") 
  ? window.location.origin 
  : "http://127.0.0.1:8000";

let allScenarios = [];
let activeScenario = null;
let currentTrace = null;

// Initialize on DOM ready
document.addEventListener("DOMContentLoaded", () => {
  initNavigation();
  initProviderListener();
  loadScenarios();
  loadLatestEvaluation();
  setupEventListeners();
});

// Navigation Tabs
function initNavigation() {
  const tabs = document.querySelectorAll(".nav-tab");
  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      tabs.forEach(t => t.classList.remove("active"));
      document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));

      tab.classList.add("active");
      const targetId = `tab-${tab.dataset.tab}`;
      const targetContent = document.getElementById(targetId);
      if (targetContent) {
        targetContent.classList.add("active");
      }
    });
  });
}

// Engine Provider Selection
function initProviderListener() {
  const select = document.getElementById("providerSelect");
  select.addEventListener("change", (e) => {
    console.log(`Engine provider switched to: ${e.target.value}`);
  });
}

// Load Scenario Catalog
async function loadScenarios() {
  try {
    const res = await fetch(`${API_BASE}/api/scenarios`);
    if (!res.ok) throw new Error("Failed to load scenarios");
    allScenarios = await res.json();

    populateScenarioDropdown();
    renderScenarioCatalog(allScenarios);

    if (allScenarios.length > 0) {
      selectScenario(allScenarios[0].id);
    }
  } catch (err) {
    console.error("Error loading scenarios:", err);
  }
}

// Populate Dropdown
function populateScenarioDropdown() {
  const dropdown = document.getElementById("scenarioSelect");
  dropdown.innerHTML = "";
  allScenarios.forEach(sc => {
    const opt = document.createElement("option");
    opt.value = sc.id;
    opt.textContent = `[${sc.category.toUpperCase()}] ${sc.title}`;
    dropdown.appendChild(opt);
  });

  dropdown.addEventListener("change", (e) => {
    selectScenario(e.target.value);
  });
}

// Select Scenario and load details
async function selectScenario(scenarioId) {
  try {
    const res = await fetch(`${API_BASE}/api/scenarios/${scenarioId}`);
    if (!res.ok) throw new Error("Failed to fetch scenario details");
    activeScenario = await res.json();

    renderActiveAlert(activeScenario);
    clearInvestigationFeed();
  } catch (err) {
    console.error("Error selecting scenario:", err);
  }
}

// Render active alert in sidebar
function renderActiveAlert(scenario) {
  const alert = scenario.alert;
  document.getElementById("alertSeverityPill").textContent = alert.severity || scenario.severity;
  document.getElementById("alertServiceTag").textContent = alert.service;
  document.getElementById("alertMetricName").textContent = `Metric: ${alert.metric}`;
  document.getElementById("alertMetricVal").textContent = `${alert.current_value} (Threshold: ${alert.threshold})`;
  document.getElementById("alertMessageText").textContent = alert.message;
  document.getElementById("alertTimestampText").textContent = `Triggered: ${alert.timestamp}`;
}

// Render Scenario Catalog Grid
function renderScenarioCatalog(scenarios) {
  const grid = document.getElementById("scenarioGrid");
  grid.innerHTML = "";

  scenarios.forEach(sc => {
    const card = document.createElement("div");
    card.className = "scenario-card";
    card.innerHTML = `
      <div>
        <div class="sc-header">
          <span class="badge badge-accent">${sc.category}</span>
          <span class="severity-pill" style="font-size: 0.65rem;">${sc.severity}</span>
        </div>
        <div class="sc-title">${sc.title}</div>
        <div class="sc-desc">${sc.description}</div>
      </div>
      <div class="sc-footer">
        <span>Service: <strong>${sc.service}</strong></span>
        <button class="btn btn-primary btn-sm" onclick="launchScenarioFromCatalog('${sc.id}')">Triage Incident</button>
      </div>
    `;
    grid.appendChild(card);
  });
}

// Launch from catalog
window.launchScenarioFromCatalog = function(scenarioId) {
  const dropdown = document.getElementById("scenarioSelect");
  dropdown.value = scenarioId;
  selectScenario(scenarioId);

  // Switch to simulator tab
  document.getElementById("tabSimulatorBtn").click();
};

// Clear Feed
function clearInvestigationFeed() {
  const feed = document.getElementById("timelineFeed");
  feed.innerHTML = `
    <div class="empty-state" id="timelinePlaceholder">
      <div class="empty-icon">⚡</div>
      <div class="empty-title">Ready for Incident Investigation</div>
      <div class="empty-subtitle">Select an incident scenario and click <strong>"Launch Autonomous Agent Triage"</strong> to watch the agent analyze telemetry and deduce the root cause.</div>
    </div>
  `;
  document.getElementById("finalReportCard").style.display = "none";
  document.getElementById("executionMeta").style.display = "none";
}

// Event Listeners
function setupEventListeners() {
  const runBtn = document.getElementById("runTriageBtn");
  runBtn.addEventListener("click", runAgentTriage);

  const fullEvalBtn = document.getElementById("runFullEvalBtn");
  fullEvalBtn.addEventListener("click", runFullEvaluationSuite);

  const searchInput = document.getElementById("scenarioSearchInput");
  searchInput.addEventListener("input", (e) => {
    const query = e.target.value.toLowerCase();
    const filtered = allScenarios.filter(sc => 
      sc.title.toLowerCase().includes(query) ||
      sc.service.toLowerCase().includes(query) ||
      sc.category.toLowerCase().includes(query) ||
      sc.description.toLowerCase().includes(query)
    );
    renderScenarioCatalog(filtered);
  });

  const closeModalBtn = document.getElementById("closeTraceModalBtn");
  closeModalBtn.addEventListener("click", () => {
    document.getElementById("traceModal").style.display = "none";
  });
}

// Run Agent Triage
async function runAgentTriage() {
  if (!activeScenario) return;

  const runBtn = document.getElementById("runTriageBtn");
  const provider = document.getElementById("providerSelect").value;
  const feed = document.getElementById("timelineFeed");

  runBtn.disabled = true;
  runBtn.innerHTML = `<span class="pulse-dot"></span> Agent Reasoning in Progress...`;

  feed.innerHTML = "";
  document.getElementById("finalReportCard").style.display = "none";
  document.getElementById("executionMeta").style.display = "flex";
  document.getElementById("stepCounterBadge").textContent = "Investigating...";
  document.getElementById("durationBadge").textContent = "Timing...";

  try {
    const res = await fetch(`${API_BASE}/api/agent/triage`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        scenario_id: activeScenario.id,
        provider: provider,
        max_steps: 8,
      }),
    });

    if (!res.ok) throw new Error("Agent triage failed");
    const result = await res.json();

    renderAgentTimeline(result.steps);
    renderFinalReport(result.report);

    document.getElementById("stepCounterBadge").textContent = `${result.total_steps} Steps Taken`;
    document.getElementById("durationBadge").textContent = `${result.duration_seconds.toFixed(2)}s Latency`;
  } catch (err) {
    console.error("Triage error:", err);
    feed.innerHTML = `<div class="alert-box alert-critical">Triage execution error: ${err.message}</div>`;
  } finally {
    runBtn.disabled = false;
    runBtn.innerHTML = `
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <polygon points="5 3 19 12 5 21 5 3"></polygon>
      </svg>
      Launch Autonomous Agent Triage
    `;
  }
}

// Render Timeline Steps
function renderAgentTimeline(steps) {
  const feed = document.getElementById("timelineFeed");
  feed.innerHTML = "";

  steps.forEach((step, idx) => {
    const card = document.createElement("div");
    card.className = "timeline-step-card";

    let toolMarkup = "";
    if (step.tool_name) {
      toolMarkup = `
        <div class="step-tool-call">
          <div style="display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 0.75rem; color: var(--text-secondary);">Tool Invocated:</span>
            <span class="tool-badge">${step.tool_name}</span>
          </div>
          <div class="tool-arguments">Input: ${JSON.stringify(step.tool_arguments)}</div>
          ${step.tool_output ? `<div class="tool-output-preview">${JSON.stringify(step.tool_output, null, 2)}</div>` : ''}
        </div>
      `;
    }

    card.innerHTML = `
      <div class="step-header">
        <span class="step-badge">STEP ${step.step_number}</span>
        <span class="badge badge-outline">${step.tool_name ? 'Tool Invocation' : 'Synthesis & Conclusion'}</span>
      </div>
      <div class="step-thought">${step.thought}</div>
      ${toolMarkup}
    `;
    feed.appendChild(card);
  });
}

// Render Final Report
function renderFinalReport(report) {
  if (!report) return;

  const card = document.getElementById("finalReportCard");
  document.getElementById("reportIncidentSummary").textContent = report.incident_summary;
  document.getElementById("reportCategoryBadge").textContent = report.root_cause_category;
  document.getElementById("reportRootCauseText").textContent = report.identified_root_cause;

  const evidenceList = document.getElementById("reportEvidenceList");
  evidenceList.innerHTML = "";
  (report.evidence_gathered || []).forEach(item => {
    const li = document.createElement("li");
    li.textContent = item;
    evidenceList.appendChild(li);
  });

  const remList = document.getElementById("reportRemediationList");
  remList.innerHTML = "";
  (report.remediation_plan || []).forEach(item => {
    const li = document.createElement("li");
    li.textContent = item;
    remList.appendChild(li);
  });

  const prevList = document.getElementById("reportPreventativeList");
  prevList.innerHTML = "";
  (report.preventative_measures || []).forEach(item => {
    const li = document.createElement("li");
    li.textContent = item;
    prevList.appendChild(li);
  });

  card.style.display = "block";
  card.scrollIntoView({ behavior: "smooth" });
}

// Load Latest Evaluation Summary
async function loadLatestEvaluation() {
  try {
    const res = await fetch(`${API_BASE}/api/evaluation/latest`);
    if (!res.ok) return;
    const data = await res.json();
    renderEvaluationKPIs(data);
    renderScorecardTable(data.results);
  } catch (err) {
    console.warn("Could not load latest evaluation:", err);
  }
}

// Render Evaluation KPIs
function renderEvaluationKPIs(data) {
  document.getElementById("kpiPassRate").textContent = `${data.pass_rate_percent}%`;
  document.getElementById("kpiPassCount").textContent = `${data.passed_scenarios} of ${data.total_scenarios} Scenarios Passed`;
  document.getElementById("kpiAvgScore").textContent = `${data.average_overall_score}%`;
  document.getElementById("kpiToolRecall").textContent = `${(data.average_tool_recall * 100).toFixed(1)}%`;
  document.getElementById("kpiAvgSteps").textContent = data.average_steps.toFixed(1);
}

// Render Scorecard Table
function renderScorecardTable(results) {
  const tbody = document.getElementById("evalScorecardBody");
  tbody.innerHTML = "";

  results.forEach(r => {
    const tr = document.createElement("tr");
    const statusClass = r.passed ? "badge-success" : "badge-danger";
    const statusText = r.passed ? "PASS" : "FAIL";

    tr.innerHTML = `
      <td><strong>${r.scenario_id}</strong></td>
      <td><span class="badge badge-outline">${r.category}</span></td>
      <td><span class="badge ${statusClass}">${statusText}</span></td>
      <td><strong>${r.overall_score.toFixed(1)}%</strong></td>
      <td>${(r.tool_invocation.f1 * 100).toFixed(0)}%</td>
      <td>${(r.parameter_validity.validity_rate * 100).toFixed(0)}%</td>
      <td>${(r.root_cause.score * 100).toFixed(0)}%</td>
      <td>${r.remediation.safety_boundary_passed ? '🛡️ Passed' : '⚠️ Violated'}</td>
      <td>${r.total_steps}</td>
      <td>
        <button class="btn btn-primary btn-sm" onclick="viewTraceDetail('${r.scenario_id}', ${JSON.stringify(r).replace(/"/g, '&quot;')})">
          Inspect Trace
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

// Inspect Trace Modal
window.viewTraceDetail = function(scenarioId, evalResult) {
  const modal = document.getElementById("traceModal");
  document.getElementById("modalTraceTitle").textContent = `Audit Trace: ${scenarioId}`;
  document.getElementById("modalTraceSubtitle").textContent = `Score: ${evalResult.overall_score}% | Steps: ${evalResult.total_steps} | Category: ${evalResult.category}`;

  const viewport = document.getElementById("modalTraceContent");
  viewport.innerHTML = `<pre>${JSON.stringify(evalResult, null, 2)}</pre>`;

  modal.style.display = "flex";
};

// Run Full Evaluation Suite
async function runFullEvaluationSuite() {
  const btn = document.getElementById("runFullEvalBtn");
  const provider = document.getElementById("providerSelect").value;

  btn.disabled = true;
  btn.innerHTML = `<span class="pulse-dot"></span> Running Harness Evaluation...`;

  try {
    const res = await fetch(`${API_BASE}/api/evaluation/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ provider: provider }),
    });

    if (!res.ok) throw new Error("Evaluation run failed");
    const summary = await res.json();

    renderEvaluationKPIs(summary);
    renderScorecardTable(summary.results);
  } catch (err) {
    console.error("Error running evaluation:", err);
    alert(`Evaluation run failed: ${err.message}`);
  } finally {
    btn.disabled = false;
    btn.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M23 4v6h-6M1 20v-6h6"/>
        <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
      </svg>
      Run Full Regression Suite (18 Scenarios)
    `;
  }
}

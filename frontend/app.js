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
  checkSystemHealth();
  loadScenarios();
  loadLatestEvaluation();
  setupEventListeners();
});

function getProviderLabel(provider) {
  if (!provider || provider === "mock") return "Mock SRE Reasoner";
  if (provider.startsWith("groq")) {
    if (provider.includes("gpt-oss-120b")) return "Groq GPT-OSS 120B";
    if (provider.includes("gpt-oss-20b")) return "Groq GPT-OSS 20B";
    return "Groq API";
  }
  if (provider.startsWith("gemini")) return "Google Gemini API";
  return "Mock SRE Reasoner";
}

// System Health & Engine Config Check
async function checkSystemHealth() {
  try {
    const res = await fetch(`${API_BASE}/api/health`);
    if (!res.ok) return;
    const data = await res.json();
    const select = document.getElementById("providerSelect");
    if (!select) return;

    const geminiOption = select.querySelector('option[value^="gemini"]');
    if (geminiOption) {
      if (!data.has_gemini_key) {
        geminiOption.textContent = `Google Gemini API (API Key Missing)`;
      }
    }

    const groqOptions = select.querySelectorAll('option[value^="groq"]');
    groqOptions.forEach(opt => {
      if (!data.has_groq_key && !opt.textContent.includes("Missing")) {
        opt.textContent += " (API Key Missing)";
      }
    });
  } catch (e) {
    console.warn("Health check error:", e);
  }
}

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
  const evalCard = document.getElementById("incidentEvaluationCard");
  if (evalCard) evalCard.style.display = "none";
  document.getElementById("executionMeta").style.display = "none";
}

// Event Listeners
let currentInvestigationMode = "scenario"; // "scenario" | "live"
let liveTargetHealthData = null;

function setupEventListeners() {
  const runBtn = document.getElementById("runTriageBtn");
  runBtn.addEventListener("click", runAgentTriage);

  const evalSingleBtn = document.getElementById("evaluateScenarioBtn");
  if (evalSingleBtn) {
    evalSingleBtn.addEventListener("click", runSingleScenarioEvaluation);
  }

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

  // Mode Switcher Listeners
  const modeScenarioBtn = document.getElementById("modeScenarioBtn");
  if (modeScenarioBtn) {
    modeScenarioBtn.addEventListener("click", () => setInvestigationMode("scenario"));
  }
  const modeLiveBtn = document.getElementById("modeLiveBtn");
  if (modeLiveBtn) {
    modeLiveBtn.addEventListener("click", () => setInvestigationMode("live"));
  }

  // Live Target Controls
  const refreshLiveBtn = document.getElementById("refreshLiveHealthBtn");
  if (refreshLiveBtn) {
    refreshLiveBtn.addEventListener("click", checkLiveTargetHealth);
  }
}

// Switch between Scenario Bank Mode and Live Target Mode
function setInvestigationMode(mode) {
  currentInvestigationMode = mode;
  const scenarioBtn = document.getElementById("modeScenarioBtn");
  const liveBtn = document.getElementById("modeLiveBtn");
  const scenarioContainer = document.getElementById("scenarioModeContainer");
  const liveContainer = document.getElementById("liveModeContainer");
  const evalBtn = document.getElementById("evaluateScenarioBtn");
  const runBtn = document.getElementById("runTriageBtn");
  const modeHeaderBadge = document.getElementById("modeHeaderBadge");

  if (mode === "live") {
    if (scenarioBtn) scenarioBtn.classList.remove("active");
    if (liveBtn) liveBtn.classList.add("active");
    if (scenarioContainer) scenarioContainer.style.display = "none";
    if (liveContainer) liveContainer.style.display = "block";
    if (evalBtn) evalBtn.style.display = "none";
    if (modeHeaderBadge) {
      modeHeaderBadge.textContent = "Live Telemetry Target";
      modeHeaderBadge.className = "badge badge-accent";
    }
    if (runBtn) {
      runBtn.innerHTML = `
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polygon points="5 3 19 12 5 21 5 3"></polygon>
        </svg>
        Launch Live Incident Investigation
      `;
    }
    checkLiveTargetHealth();
  } else {
    if (liveBtn) liveBtn.classList.remove("active");
    if (scenarioBtn) scenarioBtn.classList.add("active");
    if (liveContainer) liveContainer.style.display = "none";
    if (scenarioContainer) scenarioContainer.style.display = "block";
    if (evalBtn) evalBtn.style.display = "block";
    if (modeHeaderBadge) {
      modeHeaderBadge.textContent = "Scenario Simulation";
      modeHeaderBadge.className = "badge badge-outline";
    }
    if (runBtn) {
      runBtn.innerHTML = `
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polygon points="5 3 19 12 5 21 5 3"></polygon>
        </svg>
        Launch Autonomous Agent Triage
      `;
    }
  }
}

// Probes the running OrderFlow application health via the Agent backend adapter
async function checkLiveTargetHealth() {
  const badge = document.getElementById("liveTargetHealthBadge");
  const probeVal = document.getElementById("liveHealthProbeVal");
  const releaseEl = document.getElementById("liveTargetReleaseText");
  const urlEl = document.getElementById("liveTargetUrlText");
  const checkedEl = document.getElementById("liveCheckedTime");

  if (badge) badge.textContent = "Probing...";

  try {
    const res = await fetch(`${API_BASE}/api/agent/live-target/status`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    liveTargetHealthData = data;

    if (data.target_url && urlEl) {
      urlEl.textContent = data.target_url;
    }

    if (data.connected && data.health) {
      const h = data.health;
      const status = (h.health_status || "unknown").toLowerCase();
      if (releaseEl && h.release_version) {
        releaseEl.textContent = h.release_version;
      }

      if (badge) {
        if (status === "healthy") {
          badge.textContent = "Healthy (200 OK)";
          badge.className = "badge badge-accent";
          badge.style.background = "rgba(16, 185, 129, 0.2)";
          badge.style.color = "#34d399";
        } else if (status === "degraded") {
          badge.textContent = "Degraded (503)";
          badge.className = "badge badge-accent";
          badge.style.background = "rgba(245, 158, 11, 0.25)";
          badge.style.color = "#fbbf24";
        } else {
          badge.textContent = `${status.toUpperCase()} (Alert)`;
          badge.className = "badge badge-accent";
          badge.style.background = "rgba(239, 68, 68, 0.25)";
          badge.style.color = "#f87171";
        }
      }

      if (probeVal) {
        const dbConnected = h.dependencies && h.dependencies.database ? h.dependencies.database.connected : null;
        if (dbConnected === false) {
          probeVal.textContent = "DB: Disconnected (Fault Active)";
          probeVal.style.color = "#f87171";
        } else if (status === "degraded" || status === "unhealthy") {
          probeVal.textContent = "Subsystem Probes Degraded";
          probeVal.style.color = "#fbbf24";
        } else {
          probeVal.textContent = "All Probes Nominal (200 OK)";
          probeVal.style.color = "#34d399";
        }
      }
    } else {
      if (badge) {
        badge.textContent = "Unreachable (Port 8080)";
        badge.style.background = "rgba(239, 68, 68, 0.25)";
        badge.style.color = "#f87171";
      }
      if (probeVal) {
        probeVal.textContent = "Cannot reach OrderFlow backend";
        probeVal.style.color = "#f87171";
      }
    }

    if (checkedEl) {
      checkedEl.textContent = `Last checked: ${new Date().toLocaleTimeString()}`;
    }
  } catch (err) {
    console.warn("Live health probe error:", err);
    if (badge) {
      badge.textContent = "Target Unreachable";
      badge.style.background = "rgba(239, 68, 68, 0.25)";
      badge.style.color = "#f87171";
    }
  }
}


// Run Agent Triage (Scenario Mode or Live Mode)
async function runAgentTriage() {
  const isLive = currentInvestigationMode === "live";
  if (!isLive && !activeScenario) return;

  const runBtn = document.getElementById("runTriageBtn");
  const provider = document.getElementById("providerSelect").value;
  const feed = document.getElementById("timelineFeed");
  const providerBadge = document.getElementById("providerBadge");

  const providerLabel = getProviderLabel(provider);

  runBtn.disabled = true;
  runBtn.innerHTML = `<span class="pulse-dot"></span> ${providerLabel} ${isLive ? 'Investigating Live Target...' : 'Reasoning in Progress...'}`;

  feed.innerHTML = "";
  document.getElementById("finalReportCard").style.display = "none";
  const evalCard = document.getElementById("incidentEvaluationCard");
  if (evalCard) evalCard.style.display = "none";
  document.getElementById("executionMeta").style.display = "flex";
  if (providerBadge) {
    providerBadge.textContent = `Engine: ${providerLabel}${isLive ? ' [LIVE TARGET]' : ''}`;
    providerBadge.className = (provider.startsWith("gemini") || provider.startsWith("groq")) ? "badge badge-accent" : "badge badge-outline";
  }
  document.getElementById("stepCounterBadge").textContent = isLive ? "Querying Live Telemetry..." : "Investigating...";
  document.getElementById("durationBadge").textContent = "Timing...";

  const stopThinking = showThinkingIndicator(providerLabel);

  try {
    const endpoint = isLive ? `${API_BASE}/api/agent/live-triage` : `${API_BASE}/api/agent/triage`;
    const payload = isLive
      ? { provider: provider, max_steps: 8 }
      : { scenario_id: activeScenario.id, provider: provider, max_steps: 8 };

    const res = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    stopThinking();

    if (!res.ok) {
      let detailMsg = `Agent triage failed with HTTP status ${res.status}`;
      try {
        const errJson = await res.json();
        if (errJson.detail) detailMsg = errJson.detail;
      } catch (e) {}
      throw new Error(detailMsg);
    }
    const result = await res.json();

    if (providerBadge) {
      const activeModel = result.model_name ? ` (${result.model_name})` : "";
      const targetLabel = result.is_live ? " [LIVE TARGET]" : "";
      providerBadge.textContent = `Engine: ${result.provider || provider}${activeModel}${targetLabel}`;
    }

    await renderAgentTimeline(result.steps, result.provider, result.model_name, true);
    if (result.report) {
      renderFinalReport(result.report, isLive);
    }
    if (result.evaluation) {
      renderIncidentEvaluation(result.evaluation, result.provider, result.model_name, isLive);
    }

    document.getElementById("stepCounterBadge").textContent = `${result.total_steps} Steps Taken`;
    document.getElementById("durationBadge").textContent = `${result.duration_seconds.toFixed(2)}s Latency`;
  } catch (err) {
    stopThinking();
    console.error("Triage error:", err);
    feed.innerHTML = `
      <div class="alert-box alert-critical" style="margin-bottom: 16px;">
        <div style="font-weight: 700; font-size: 0.95rem; margin-bottom: 6px; display: flex; align-items: center; gap: 8px;">
          <span>⚠️</span> Investigation Execution Failed (${providerLabel})
        </div>
        <div style="color: var(--text-secondary); line-height: 1.5; font-family: 'JetBrains Mono', monospace; font-size: 0.85rem;">
          ${err.message}
        </div>
      </div>
    `;
    if (providerBadge) {
      providerBadge.textContent = `Engine: ${providerLabel} (Failed)`;
    }
  } finally {
    runBtn.disabled = false;
    runBtn.innerHTML = `
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <polygon points="5 3 19 12 5 21 5 3"></polygon>
      </svg>
      ${isLive ? "Launch Live Incident Investigation" : "Launch Autonomous Agent Triage"}
    `;
  }
}

function escapeHtml(text) {
  if (!text) return "";
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function formatInlineMarkdown(text) {
  if (!text) return "";
  let s = escapeHtml(text);
  s = s.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  s = s.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>');
  s = s.replace(/\n/g, '<br>');
  return s;
}

function formatStepThought(thought, isFinish) {
  if (!thought) return "";

  // If finish step has raw markdown or excessive length
  if (isFinish && (thought.startsWith("#") || thought.includes("## Incident Summary") || thought.includes("## Root Cause") || thought.length > 250)) {
    let summaryText = "";
    const sumMatch = thought.match(/##\s*1\.\s*Incident\s*Summary\s*([\s\S]*?)(?=##|$)/i) 
                  || thought.match(/Incident\s*Summary:?\s*([\s\S]*?)(?=##|$)/i);
    if (sumMatch) {
      summaryText = sumMatch[1].replace(/[\*\#\-]/g, '').trim().split('\n')[0];
    }

    let rcText = "";
    const rcMatch = thought.match(/##\s*2\.\s*Identified\s*Root\s*Cause[^\n]*\n([\s\S]*?)(?=##|$)/i)
                 || thought.match(/Root\s*Cause:?\s*([\s\S]*?)(?=##|$)/i);
    if (rcMatch) {
      rcText = rcMatch[1].replace(/^[\*\#\-\s]+/gm, '').trim().split('\n')[0];
    }

    return `
      <div class="synthesis-conclusion-card">
        <div class="synthesis-banner">
          <span class="synthesis-icon">🎯</span>
          <div>
            <div class="synthesis-title">Investigation Concluded &amp; Root Cause Diagnosed</div>
            <div class="synthesis-desc">Target agent gathered telemetry across logs, metrics, deployment history, and configuration. Final report and remediation synthesized below.</div>
          </div>
        </div>
        ${summaryText ? `<div class="synthesis-snippet"><strong>Executive Summary:</strong> ${escapeHtml(summaryText)}</div>` : ''}
        ${rcText ? `<div class="synthesis-snippet"><strong>Root Cause:</strong> ${escapeHtml(rcText)}</div>` : ''}
        <div class="synthesis-action">
          <button class="btn btn-outline btn-sm" onclick="document.getElementById('finalReportCard').scrollIntoView({behavior: 'smooth'})">
            📋 View Complete Diagnostic Report &amp; Remediation Plan Below ↓
          </button>
        </div>
      </div>
    `;
  }

  return formatInlineMarkdown(thought);
}

// Thinking Animation Indicator
function showThinkingIndicator(providerLabel) {
  const feed = document.getElementById("timelineFeed");
  const thinkingCard = document.createElement("div");
  thinkingCard.className = "thinking-card";
  thinkingCard.id = "activeThinkingCard";

  const startTime = Date.now();
  const phases = [
    `Analyzing incident alert parameters & service topology (${providerLabel})...`,
    "Correlating metric spikes with recent deployment history...",
    "Formulating diagnostic hypothesis and selecting telemetry tools...",
    "Querying logs, configuration, and runtime telemetry...",
    "Synthesizing root-cause evidence and advisory remediation...",
  ];
  let phaseIdx = 0;

  thinkingCard.innerHTML = `
    <div class="thinking-header">
      <div class="thinking-badge-group">
        <div class="thinking-pulse-icon"></div>
        <div class="thinking-label">
          <span>Thinking</span>
          <span class="thinking-dots">
            <span class="thinking-dot"></span>
            <span class="thinking-dot"></span>
            <span class="thinking-dot"></span>
          </span>
        </div>
      </div>
      <span class="thinking-timer" id="thinkingTimer">0.0s</span>
    </div>
    <div class="thinking-status-text" id="thinkingStatus">${phases[0]}</div>
  `;
  feed.appendChild(thinkingCard);

  const timerInterval = setInterval(() => {
    const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
    const timerEl = document.getElementById("thinkingTimer");
    if (timerEl) timerEl.textContent = `${elapsed}s`;

    const statusEl = document.getElementById("thinkingStatus");
    if (statusEl && Math.floor(elapsed) % 2 === 0) {
      const nextIdx = Math.min(Math.floor(elapsed / 1.8), phases.length - 1);
      if (nextIdx !== phaseIdx) {
        phaseIdx = nextIdx;
        statusEl.style.opacity = "0";
        setTimeout(() => {
          if (statusEl) {
            statusEl.textContent = phases[phaseIdx];
            statusEl.style.opacity = "1";
          }
        }, 150);
      }
    }
  }, 100);

  return () => {
    clearInterval(timerInterval);
    const card = document.getElementById("activeThinkingCard");
    if (card) card.remove();
  };
}

// Word-by-word streaming typewriter animation
async function animateTextGenerating(container, fullHtml, rawText) {
  if (fullHtml.includes("synthesis-conclusion-card")) {
    container.innerHTML = fullHtml;
    container.style.animation = "fadeIn 0.35s ease";
    return;
  }

  container.classList.add("generating");
  container.innerHTML = `<span class="generating-cursor"></span>`;

  const words = rawText.split(/(\s+)/);
  let currentAccum = "";

  for (let i = 0; i < words.length; i++) {
    currentAccum += words[i];
    container.innerHTML = formatInlineMarkdown(currentAccum) + `<span class="generating-cursor"></span>`;
    if (words[i].trim().length > 0) {
      await new Promise(r => setTimeout(r, 12));
    }
  }

  container.innerHTML = fullHtml;
  container.classList.remove("generating");
}

// Render Timeline Steps (with optional streaming generation animation)
async function renderAgentTimeline(steps, provider, modelName, animate = false) {
  const feed = document.getElementById("timelineFeed");
  feed.innerHTML = "";

  // Engine & Model Attribution Banner
  const banner = document.createElement("div");
  banner.className = "engine-attribution-banner";
  const isGroq = (provider || "").startsWith("groq");
  const isGemini = (provider || "").startsWith("gemini");
  const icon = isGroq ? "⚡" : (isGemini ? "✨" : "⚙️");
  const engineTitle = isGroq ? "Groq API (Ultra-Low Latency Inference)" : (isGemini ? "Google Gemini API (Autonomous Function Calling)" : "Mock SRE Reasoner (Deterministic Replay)");
  const modelText = modelName ? `Model: <code>${modelName}</code>` : "";

  banner.innerHTML = `
    <div style="display: flex; align-items: center; justify-content: space-between; padding: 10px 14px; background: rgba(245, 158, 11, 0.08); border: 1px solid rgba(245, 158, 11, 0.25); border-radius: 8px; margin-bottom: 14px; font-size: 0.85rem;">
      <div style="display: flex; align-items: center; gap: 8px;">
        <span style="font-size: 1.1rem;">${icon}</span>
        <span><strong>Active Engine:</strong> ${engineTitle}</span>
      </div>
      <div style="color: var(--text-secondary); font-family: 'JetBrains Mono', monospace; font-size: 0.78rem;">
        ${modelText}
      </div>
    </div>
  `;
  feed.appendChild(banner);

  for (let idx = 0; idx < steps.length; idx++) {
    const step = steps[idx];
    const card = document.createElement("div");
    card.className = "timeline-step-card";

    let toolMarkup = "";
    if (step.tool_name) {
      toolMarkup = `
        <div class="step-tool-call" style="${animate ? 'animation: fadeIn 0.3s ease;' : ''}">
          <div style="display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 0.75rem; color: var(--text-secondary);">Tool Invocated:</span>
            <span class="tool-badge">${step.tool_name}</span>
          </div>
          <div class="tool-arguments">Input: ${JSON.stringify(step.tool_arguments)}</div>
          ${step.tool_output ? `<div class="tool-output-preview">${JSON.stringify(step.tool_output, null, 2)}</div>` : ''}
        </div>
      `;
    }

    const isFinish = !step.tool_name;
    const thoughtHtml = formatStepThought(step.thought, isFinish);

    card.innerHTML = `
      <div class="step-header">
        <span class="step-badge">STEP ${step.step_number}</span>
        <span class="badge ${isFinish ? 'badge-accent' : 'badge-outline'}">${isFinish ? 'Synthesis & Conclusion' : 'Tool Invocation'}</span>
      </div>
      <div class="step-thought" id="stepThought_${idx}"></div>
      <div id="stepTool_${idx}"></div>
    `;
    feed.appendChild(card);

    const thoughtEl = card.querySelector(`#stepThought_${idx}`);
    const toolEl = card.querySelector(`#stepTool_${idx}`);

    if (animate && step.thought) {
      if (isFinish && thoughtHtml.includes("synthesis-conclusion-card")) {
        thoughtEl.innerHTML = thoughtHtml;
      } else {
        await animateTextGenerating(thoughtEl, thoughtHtml, step.thought);
      }
      if (toolMarkup) {
        toolEl.innerHTML = toolMarkup;
      }
      await new Promise(r => setTimeout(r, 80));
    } else {
      thoughtEl.innerHTML = thoughtHtml;
      if (toolMarkup) {
        toolEl.innerHTML = toolMarkup;
      }
    }
  }
}


// Render Final Report
// Clean report strings of dirty markdown artifacts (horizontal rules, redundant labels)
function cleanReportString(str, isRootCause, isSummary) {
  if (!str) return "";
  let s = str.trim();
  // Strip horizontal rules
  s = s.replace(/[\r\n]+\s*[-*_]{3,}\s*[\r\n]+/g, ' ');
  s = s.replace(/\s*[-*_]{3,}\s*/g, ' ');

  if (isRootCause) {
    s = s.replace(/^[\*\-\s#]*\*{0,2}(?:root\s+cause|identified\s+root\s+cause|diagnosis)\*{0,2}:?\s*/i, '');
  } else if (isSummary) {
    s = s.replace(/^[\*\-\s#]*\*{0,2}(?:incident\s+summary|summary|overview)\*{0,2}:?\s*/i, '');
    s = s.replace(/\s+-\s+\*\*/g, ' | **');
  }

  // Strip leading bullet/dash/hash without stripping bold tags
  s = s.replace(/^\s*[-*+•#]\s+/, '');
  s = s.trim().replace(/^[-:]+|[-:]+$/g, '').trim();
  return s;
}

// Render Final Report
function renderFinalReport(report, isLive = false) {
  if (!report) return;

  const card = document.getElementById("finalReportCard");

  // Meta Chips
  const metaChipsContainer = document.getElementById("reportMetaChips");
  if (metaChipsContainer) {
    if (isLive) {
      const ts = new Date().toISOString().substring(0, 19) + "Z";
      metaChipsContainer.innerHTML = `
        <span class="meta-chip"><span>🖥️</span> Service: <strong>OrderFlow Demo Service</strong></span>
        <span class="meta-chip"><span>📡</span> Telemetry: <strong>Live Target Runtime</strong></span>
        <span class="meta-chip"><span style="color: #f87171;">⚠️</span> Mode: <strong style="color: #f87171;">LIVE INCIDENT</strong></span>
        <span class="meta-chip"><span>⏱️</span> Time: <strong>${escapeHtml(ts)}</strong></span>
      `;
    } else if (activeScenario) {
      const srv = activeScenario.alert?.service || activeScenario.service || "production";
      const metric = activeScenario.alert?.metric || "health_check";
      const val = activeScenario.alert?.current_value != null ? activeScenario.alert.current_value : "Alert";
      const ts = activeScenario.alert?.timestamp || new Date().toISOString().substring(0, 19) + "Z";

      metaChipsContainer.innerHTML = `
        <span class="meta-chip"><span>🖥️</span> Service: <strong>${escapeHtml(srv)}</strong></span>
        <span class="meta-chip"><span>📈</span> Metric: <strong>${escapeHtml(metric)} (${escapeHtml(String(val))})</strong></span>
        <span class="meta-chip"><span style="color: #f87171;">⚠️</span> Severity: <strong style="color: #f87171;">CRITICAL</strong></span>
        <span class="meta-chip"><span>⏱️</span> Time: <strong>${escapeHtml(ts)}</strong></span>
      `;
    }
  }

  // Executive Incident Summary
  const subEl = document.getElementById("reportIncidentSummary");
  if (subEl) {
    const cleanSum = cleanReportString(report.incident_summary, false, true);
    subEl.innerHTML = formatInlineMarkdown(cleanSum);
  }

  // Category Badge
  const badgeEl = document.getElementById("reportCategoryBadge");
  if (badgeEl) {
    badgeEl.textContent = report.root_cause_category;
  }

  // Root Cause Box
  const rcEl = document.getElementById("reportRootCauseText");
  if (rcEl) {
    const cleanRc = cleanReportString(report.identified_root_cause, true, false);
    rcEl.innerHTML = formatInlineMarkdown(cleanRc);
  }

  // Telemetry Evidence Cards
  const evidenceList = document.getElementById("reportEvidenceList");
  if (evidenceList) {
    evidenceList.innerHTML = "";
    const items = (report.evidence_gathered || []).map(item => cleanReportString(item)).filter(item => item.length > 5);
    items.forEach(raw => {
      let title = "Telemetry Observation";
      let body = raw;
      const match = raw.match(/^\*{0,2}([A-Za-z0-9\s/_\-]+?)\*{0,2}:\s*(.*)$/);
      if (match) {
        title = match[1].trim();
        body = match[2].trim();
      }
      if (body.endsWith(":")) body = body.slice(0, -1).trim();

      let icon = "📡";
      const lt = title.toLowerCase();
      if (lt.includes("log") || lt.includes("exception")) icon = "📄";
      else if (lt.includes("deploy") || lt.includes("version") || lt.includes("commit")) icon = "🚀";
      else if (lt.includes("metric") || lt.includes("spike") || lt.includes("rate") || lt.includes("telemetry")) icon = "📈";
      else if (lt.includes("config") || lt.includes("flag") || lt.includes("env")) icon = "⚙️";

      const div = document.createElement("div");
      div.className = "evidence-card";
      div.innerHTML = `
        <div class="evidence-header">
          <span class="evidence-icon">${icon}</span>
          <span class="evidence-title">${escapeHtml(title)}</span>
        </div>
        <div class="evidence-body">${formatInlineMarkdown(body)}</div>
      `;
      evidenceList.appendChild(div);
    });
  }

  // Actionable Remediation Step Cards
  const remList = document.getElementById("reportRemediationList");
  if (remList) {
    remList.innerHTML = "";

    // Consolidate split heading + body pairs if present
    const rawItems = (report.remediation_plan || []).map(item => cleanReportString(item)).filter(Boolean);
    const consolidated = [];
    let i = 0;
    while (i < rawItems.length) {
      const curr = rawItems[i];
      const isHeaderOnly = (curr.endsWith(":") || curr.endsWith(":**") || /^\*{0,2}(?:step\s*\d+:?\s*)?[A-Za-z0-9\s\-_/()]+\*{0,2}:?$/i.test(curr)) && curr.length < 80 && !curr.includes(".");
      if (isHeaderOnly) {
        const label = curr.replace(/^[\*\#\-\s]+|[\*\#:\s]+$/g, '');
        if (i + 1 < rawItems.length && !rawItems[i + 1].endsWith(":") && rawItems[i + 1].length > 5) {
          consolidated.push(`**${label}**: ${rawItems[i + 1]}`);
          i += 2;
          continue;
        }
        if (!/(?:code fix|post-incident)/i.test(label)) {
          consolidated.push(`**${label}**`);
        }
        i += 1;
        continue;
      }
      consolidated.push(curr);
      i += 1;
    }

    consolidated.forEach((raw, idx) => {
      let title = `Step ${idx + 1}: Action Instruction`;
      let desc = raw;
      const match = raw.match(/^\*{0,2}(?:(?:Step\s*\d+:?\s*)?([A-Za-z0-9\s/_\-()]+?))\*{0,2}:\s*(.*)$/i);
      if (match) {
        title = match[1].trim();
        desc = match[2].trim();
      }
      if (desc.endsWith(":")) desc = desc.slice(0, -1).trim();

      const div = document.createElement("div");
      div.className = "remediation-step-card";
      div.innerHTML = `
        <div class="step-num-badge">${idx + 1}</div>
        <div class="step-content">
          <div class="step-title">${escapeHtml(title)}</div>
          <div class="step-desc">${formatInlineMarkdown(desc)}</div>
        </div>
      `;
      remList.appendChild(div);
    });
  }

  // Preventative Measures Guardrail Cards
  const prevList = document.getElementById("reportPreventativeList");
  if (prevList) {
    prevList.innerHTML = "";
    const items = (report.preventative_measures || []).map(item => cleanReportString(item)).filter(item => item.length > 5);
    items.forEach(raw => {
      let title = "Guardrail";
      let desc = raw;
      const match = raw.match(/^\*{0,2}([A-Za-z0-9\s/_\-]+?)\*{0,2}:\s*(.*)$/);
      if (match) {
        title = match[1].trim();
        desc = match[2].trim();
      }
      if (desc.endsWith(":")) desc = desc.slice(0, -1).trim();

      const div = document.createElement("div");
      div.className = "preventative-card";
      div.innerHTML = `
        <div class="preventative-icon">🛡️</div>
        <div class="preventative-content">
          <div class="preventative-title">${escapeHtml(title)}</div>
          <div class="preventative-desc">${formatInlineMarkdown(desc)}</div>
        </div>
      `;
      prevList.appendChild(div);
    });
  }

  card.style.display = "block";
  card.scrollIntoView({ behavior: "smooth" });
}


// Render Incident Evaluation Scorecard in Tab 1
function renderIncidentEvaluation(evalData, provider, modelName, isLive = false) {
  const card = document.getElementById("incidentEvaluationCard");
  if (!card || !evalData) return;

  const isGemini = provider === "gemini";
  const engineTitle = isGemini ? "Google Gemini API" : ((provider && provider.startsWith("groq")) ? "Groq LPU" : (provider === "openai" ? "OpenAI Engine" : "Mock SRE Reasoner"));
  const modelText = modelName ? ` (${modelName})` : "";
  const criteriaText = isLive ? "live OrderFlow telemetry diagnostic criteria" : "scenario ground-truth criteria";
  document.getElementById("evalEngineLabel").textContent = `Evaluated with ${engineTitle}${modelText} against ${criteriaText}`;

  const verdictBadge = document.getElementById("evalVerdictBadge");
  if (evalData.passed) {
    verdictBadge.textContent = "PASS";
    verdictBadge.className = "badge badge-success";
  } else {
    verdictBadge.textContent = "FAIL";
    verdictBadge.className = "badge badge-danger";
  }

  const scoreBadge = document.getElementById("evalCompositeScoreBadge");
  scoreBadge.textContent = `Overall Score: ${evalData.overall_score.toFixed(1)}%`;
  scoreBadge.className = evalData.passed ? "badge badge-success" : "badge badge-danger";

  // Tool Invocation F1
  const toolF1 = evalData.tool_invocation ? evalData.tool_invocation.f1 : 0;
  const toolRecall = evalData.tool_invocation ? evalData.tool_invocation.recall : 0;
  const toolCallsCount = evalData.tool_invocation ? (evalData.tool_invocation.called_tools || []).length : 0;
  document.getElementById("evalToolF1").textContent = `${(toolF1 * 100).toFixed(1)}%`;
  document.getElementById("evalToolDetails").textContent = `Recall: ${(toolRecall * 100).toFixed(0)}% (${toolCallsCount} calls)`;

  // Parameter Validity
  const paramVal = evalData.parameter_validity ? evalData.parameter_validity.validity_rate : 0;
  const validCalls = evalData.parameter_validity ? (evalData.parameter_validity.valid_parameterized_calls ?? evalData.parameter_validity.valid_calls ?? 0) : 0;
  const totalCalls = evalData.parameter_validity ? (evalData.parameter_validity.total_parameterized_calls ?? evalData.parameter_validity.total_calls ?? 0) : 0;
  document.getElementById("evalParamValidity").textContent = `${(paramVal * 100).toFixed(1)}%`;
  document.getElementById("evalParamDetails").textContent = `Valid queries: ${validCalls}/${totalCalls}`;

  // Root Cause Score
  const rcScore = evalData.root_cause ? evalData.root_cause.score : 0;
  const catMatch = evalData.root_cause && evalData.root_cause.category_match ? "Matched" : "Mismatch";
  const kwRecall = evalData.root_cause ? evalData.root_cause.keyword_recall : 0;
  document.getElementById("evalRootCauseScore").textContent = `${(rcScore * 100).toFixed(1)}%`;
  document.getElementById("evalRootCauseDetails").textContent = `Category: ${catMatch} | Keywords: ${(kwRecall * 100).toFixed(0)}%`;

  // Remediation & Safety
  const safetyScore = evalData.remediation ? evalData.remediation.score : 0;
  const safetyPassed = evalData.remediation && evalData.remediation.safety_boundary_passed;
  document.getElementById("evalSafetyScore").textContent = `${(safetyScore * 100).toFixed(1)}%`;
  document.getElementById("evalSafetyDetails").textContent = safetyPassed ? "🛡️ Safety: Safe (Human-in-Loop)" : "⚠️ Safety Boundary Violated";

  // Failure reasons
  const failBox = document.getElementById("evalFailureReasonsBox");
  const failList = document.getElementById("evalFailureReasonsList");
  failList.innerHTML = "";
  if (evalData.failure_reasons && evalData.failure_reasons.length > 0) {
    evalData.failure_reasons.forEach(reason => {
      const li = document.createElement("li");
      li.textContent = reason;
      failList.appendChild(li);
    });
    failBox.style.display = "block";
  } else {
    failBox.style.display = "none";
  }

  // Setup trace inspect button
  const traceBtn = document.getElementById("viewCurrentTraceBtn");
  if (traceBtn) {
    traceBtn.onclick = () => {
      viewTraceDetail(evalData.scenario_id, evalData);
    };
  }

  card.style.display = "block";
  card.scrollIntoView({ behavior: "smooth" });
}

// Run Evaluation for the Active Scenario Only
async function runSingleScenarioEvaluation() {
  if (!activeScenario) return;

  const btn = document.getElementById("evaluateScenarioBtn");
  const provider = document.getElementById("providerSelect").value;
  const providerLabel = getProviderLabel(provider);
  const providerBadge = document.getElementById("providerBadge");
  const feed = document.getElementById("timelineFeed");

  btn.disabled = true;
  btn.innerHTML = `<span class="pulse-dot"></span> Evaluating (${providerLabel})...`;

  document.getElementById("finalReportCard").style.display = "none";
  const evalCard = document.getElementById("incidentEvaluationCard");
  if (evalCard) evalCard.style.display = "none";

  document.getElementById("executionMeta").style.display = "flex";
  if (providerBadge) {
    providerBadge.textContent = `Engine: ${providerLabel}`;
    providerBadge.className = (provider.startsWith("gemini") || provider.startsWith("groq")) ? "badge badge-accent" : "badge badge-outline";
  }
  document.getElementById("stepCounterBadge").textContent = "Evaluating...";
  document.getElementById("durationBadge").textContent = "Timing...";

  try {
    const res = await fetch(`${API_BASE}/api/evaluation/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        scenario_id: activeScenario.id,
        provider: provider,
      }),
    });

    if (!res.ok) {
      let errDetail = `Evaluation failed (${res.status})`;
      try {
        const errJson = await res.json();
        if (errJson.detail) errDetail = errJson.detail;
      } catch (e) {}
      throw new Error(errDetail);
    }

    const summary = await res.json();
    if (summary.results && summary.results.length > 0) {
      const evalData = summary.results[0];

      document.getElementById("stepCounterBadge").textContent = `${evalData.total_steps} steps`;
      document.getElementById("durationBadge").textContent = `${evalData.duration_seconds}s`;

      // Render the Evaluation Scorecard
      renderIncidentEvaluation(evalData, provider, evalData.model_name);

      // Populate timeline feed and diagnostic report from the saved trace
      if (evalData.trace_path) {
        const filename = evalData.trace_path.split(/[\\/]/).pop();
        try {
          const traceRes = await fetch(`${API_BASE}/api/evaluation/traces/${encodeURIComponent(filename)}`);
          if (traceRes.ok) {
            const traceData = await traceRes.json();
            if (traceData.steps && traceData.steps.length > 0) {
              renderAgentTimeline(traceData.steps, evalData.provider, evalData.model_name);
            }
            if (traceData.report) {
              renderFinalReport(traceData.report);
            }

          }
        } catch (e) {
          console.warn("Could not load trace details for single evaluation:", e);
        }
      }
    }
  } catch (err) {
    console.error("Single evaluation error:", err);
    alert(`Scenario evaluation error: ${err.message}`);
  } finally {
    btn.disabled = false;
    btn.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
        <polyline points="14 2 14 8 20 8"></polyline>
        <line x1="16" y1="13" x2="8" y2="13"></line>
        <line x1="16" y1="17" x2="8" y2="17"></line>
        <polyline points="10 9 9 9 8 9"></polyline>
      </svg>
      Run Evaluation on this Scenario
    `;
  }
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
window._evalResultsMap = window._evalResultsMap || {};

function renderScorecardTable(results) {
  const tbody = document.getElementById("evalScorecardBody");
  tbody.innerHTML = "";

  results.forEach(r => {
    window._evalResultsMap[r.scenario_id] = r;
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
        <button class="btn btn-primary btn-sm" onclick="viewTraceDetail('${r.scenario_id}')">
          Inspect Trace
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

// Inspect Trace Modal
window.viewTraceDetail = async function(scenarioId, evalResult) {
  const modal = document.getElementById("traceModal");
  const data = evalResult || (window._evalResultsMap && window._evalResultsMap[scenarioId]) || {};

  document.getElementById("modalTraceTitle").textContent = `Audit Trace: ${scenarioId}`;
  document.getElementById("modalTraceSubtitle").textContent = `Score: ${data.overall_score || 0}% | Steps: ${data.total_steps || 0} | Category: ${data.category || ""}`;

  const viewport = document.getElementById("modalTraceContent");
  viewport.innerHTML = `<div style="padding: 24px; text-align: center; color: var(--text-secondary);"><span class="pulse-dot"></span> Loading auditable trace...</div>`;
  modal.style.display = "flex";

  if (data && data.trace_path) {
    const filename = data.trace_path.split(/[\\/]/).pop();
    try {
      const res = await fetch(`${API_BASE}/api/evaluation/traces/${encodeURIComponent(filename)}`);
      if (res.ok) {
        const fullTrace = await res.json();
        viewport.innerHTML = `<pre>${JSON.stringify(fullTrace, null, 2)}</pre>`;
        return;
      }
    } catch (e) {
      console.warn("Could not load trace file directly, falling back to evalResult", e);
    }
  }

  viewport.innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
};



// Run Full Evaluation Suite
async function runFullEvaluationSuite() {
  const btn = document.getElementById("runFullEvalBtn");
  const provider = document.getElementById("providerSelect").value;
  const providerLabel = getProviderLabel(provider);

  btn.disabled = true;
  btn.innerHTML = `<span class="pulse-dot"></span> Running Harness Evaluation (${providerLabel})...`;

  try {
    const res = await fetch(`${API_BASE}/api/evaluation/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ provider: provider }),
    });

    if (!res.ok) {
      let errDetail = `Evaluation run failed (${res.status})`;
      try {
        const errJson = await res.json();
        if (errJson.detail) errDetail = errJson.detail;
      } catch (e) {}
      throw new Error(errDetail);
    }
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

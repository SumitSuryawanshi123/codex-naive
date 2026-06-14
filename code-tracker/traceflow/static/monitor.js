const params = new URLSearchParams(window.location.search);
const projectId = params.get("project_id");

const state = {
  latestTraceId: null,
  latestSignature: null,
  selectedTraceId: null,
};

const els = {
  flowRail: document.querySelector("#flowRail"),
  functionList: document.querySelector("#functionList"),
  metricDuration: document.querySelector("#metricDuration"),
  metricMethod: document.querySelector("#metricMethod"),
  metricSpans: document.querySelector("#metricSpans"),
  metricStatus: document.querySelector("#metricStatus"),
  statusPill: document.querySelector("#statusPill"),
  timeline: document.querySelector("#timeline"),
  traceCount: document.querySelector("#traceCount"),
  traceId: document.querySelector("#traceId"),
  traceList: document.querySelector("#traceList"),
  traceSubtitle: document.querySelector("#traceSubtitle"),
};

if (!projectId) {
  els.statusPill.textContent = "Missing project";
  els.traceSubtitle.textContent = "Open this page from TraceFlow after uploading a project";
} else {
  pollTraces();
  setInterval(pollTraces, 1000);
}

async function pollTraces() {
  try {
    const response = await fetch(`/api/projects/${encodeURIComponent(projectId)}/traces`);
    if (!response.ok) {
      throw new Error(`Trace API returned ${response.status}`);
    }
    const traces = await response.json();
    els.statusPill.textContent = traces.length ? "Live" : "Waiting";
    els.traceCount.textContent = String(traces.length);
    renderTraceList(traces);

    const selected =
      traces.find((trace) => trace.trace_id === state.selectedTraceId) || traces[0] || null;
    const signature = selected
      ? `${selected.trace_id}:${selected.status_code}:${selected.duration_ms}:${selected.events?.length || 0}`
      : null;
    if (selected && signature !== state.latestSignature) {
      state.latestTraceId = selected.trace_id;
      state.latestSignature = signature;
      renderTrace(selected);
    }
  } catch (error) {
    els.statusPill.textContent = "Disconnected";
    els.traceSubtitle.textContent = error instanceof Error ? error.message : String(error);
  }
}

function renderTraceList(traces) {
  if (!traces.length) {
    els.traceList.innerHTML = '<div class="empty-state">Waiting for app traffic</div>';
    return;
  }

  els.traceList.innerHTML = traces
    .slice(0, 12)
    .map(
      (trace) => `
        <button class="trace-list-item ${trace.trace_id === state.selectedTraceId ? "is-selected" : ""}" type="button" data-trace-id="${escapeHtml(trace.trace_id)}">
          <span>${escapeHtml(trace.method)} ${escapeHtml(trace.path)}</span>
          <strong>${escapeHtml(String(trace.status_code || "-"))}</strong>
        </button>
      `,
    )
    .join("");

  els.traceList.querySelectorAll("[data-trace-id]").forEach((button) => {
    button.addEventListener("click", () => {
      state.selectedTraceId = button.dataset.traceId;
      state.latestTraceId = null;
      state.latestSignature = null;
      pollTraces();
    });
  });
}

function renderTrace(trace) {
  const events = trace.events || [];
  els.traceSubtitle.textContent = trace.title;
  els.traceId.textContent = trace.trace_id;
  els.metricMethod.textContent = trace.method;
  els.metricStatus.textContent = String(trace.status_code || "-");
  els.metricDuration.textContent = formatDuration(trace.duration_ms);
  els.metricSpans.textContent = String(events.length);
  renderFlow(events);
  renderTimeline(events);
  renderFunctions(events);
}

function renderFlow(events) {
  if (!events.length) {
    els.flowRail.innerHTML = '<div class="empty-state">No spans recorded</div>';
    return;
  }

  els.flowRail.innerHTML = events
    .slice(0, 16)
    .map(
      (event, index) => `
        <div class="flow-node kind-${escapeHtml(event.kind)} ${event.status === "error" ? "is-error" : ""}" style="animation-delay: ${index * 45}ms">
          <span>${escapeHtml(event.kind)}</span>
          <strong title="${escapeHtml(event.name)}">${escapeHtml(shortName(event.name))}</strong>
        </div>
      `,
    )
    .join("");
}

function renderTimeline(events) {
  els.timeline.innerHTML = events
    .map((event, index) => {
      const depth = Math.min(Number(event.depth || 0), 7);
      const detail = event.error || event.detail || event.kind;
      return `
        <li class="timeline-item kind-${escapeHtml(event.kind)} ${event.status === "error" ? "is-error" : ""}" style="--depth: ${depth}; animation-delay: ${index * 30}ms">
          <span class="timeline-dot" aria-hidden="true"></span>
          <div class="timeline-main">
            <strong>${escapeHtml(event.name)}</strong>
            <span>${escapeHtml(detail)}</span>
          </div>
          <span class="duration">${formatDuration(event.duration_ms)}</span>
        </li>
      `;
    })
    .join("");
}

function renderFunctions(events) {
  const functionEvents = events.filter((event) =>
    [
      "route",
      "service",
      "repository",
      "database",
      "validation",
      "model",
      "function",
      "profiler",
    ].includes(event.kind),
  );

  if (!functionEvents.length) {
    els.functionList.innerHTML = '<li><strong>None</strong><span>-</span></li>';
    return;
  }

  els.functionList.innerHTML = functionEvents
    .slice(0, 30)
    .map(
      (event) => `
        <li>
          <strong>${escapeHtml(shortName(event.name))}</strong>
          <span>${formatDuration(event.duration_ms)}</span>
        </li>
      `,
    )
    .join("");
}

function formatDuration(value) {
  if (value === null || value === undefined) {
    return "-";
  }
  if (Number(value) < 1) {
    return "<1 ms";
  }
  return `${Number(value).toFixed(1)} ms`;
}

function shortName(name) {
  if (!name) {
    return "";
  }
  const parts = String(name).split(".");
  return parts[parts.length - 1];
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

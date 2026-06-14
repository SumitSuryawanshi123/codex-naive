const demoActions = {
  create: {
    label: "Create ticket",
    method: "POST",
    url: "/api/tickets",
    body: () => ({
      subject: "Workspace setup blocked",
      description: "Customer cannot finish the first workspace setup step.",
      customer: "Acme Ops",
      priority: "high",
    }),
  },
  list: {
    label: "List tickets",
    method: "GET",
    url: "/api/tickets",
  },
  update: {
    label: "Update latest",
    method: "PATCH",
    url: () => `/api/tickets/${state.latestTicketId || 1}`,
    body: () => ({
      status: "waiting",
      priority: "urgent",
    }),
  },
  delete: {
    label: "Delete latest",
    method: "DELETE",
    url: () => `/api/tickets/${state.latestTicketId || 1}`,
  },
};

const state = {
  busy: false,
  latestTicketId: 1,
  project: null,
};

const els = {
  appTarget: document.querySelector("#appTarget"),
  demoButtons: document.querySelectorAll("[data-demo-action]"),
  flowRail: document.querySelector("#flowRail"),
  functionList: document.querySelector("#functionList"),
  latestTicketBadge: document.querySelector("#latestTicketBadge"),
  metricDuration: document.querySelector("#metricDuration"),
  metricMethod: document.querySelector("#metricMethod"),
  metricSpans: document.querySelector("#metricSpans"),
  metricStatus: document.querySelector("#metricStatus"),
  openAppLink: document.querySelector("#openAppLink"),
  openMonitorLink: document.querySelector("#openMonitorLink"),
  projectLinks: document.querySelector("#projectLinks"),
  projectStatus: document.querySelector("#projectStatus"),
  requestBody: document.querySelector("#requestBody"),
  requestMethod: document.querySelector("#requestMethod"),
  requestPath: document.querySelector("#requestPath"),
  responseBody: document.querySelector("#responseBody"),
  responseStatus: document.querySelector("#responseStatus"),
  routeCount: document.querySelector("#routeCount"),
  routeList: document.querySelector("#routeList"),
  sendRequestButton: document.querySelector("#sendRequestButton"),
  statusPill: document.querySelector("#statusPill"),
  stopProjectButton: document.querySelector("#stopProjectButton"),
  timeline: document.querySelector("#timeline"),
  traceId: document.querySelector("#traceId"),
  traceSubtitle: document.querySelector("#traceSubtitle"),
  uploadButton: document.querySelector("#uploadButton"),
  zipInput: document.querySelector("#zipInput"),
  zipName: document.querySelector("#zipName"),
};

els.demoButtons.forEach((button) => {
  button.addEventListener("click", () => runDemoAction(button.dataset.demoAction));
});
els.uploadButton.addEventListener("click", uploadProject);
els.stopProjectButton.addEventListener("click", stopProject);
els.sendRequestButton.addEventListener("click", sendProjectRequest);
els.zipInput.addEventListener("change", () => {
  els.zipName.textContent = els.zipInput.files[0]?.name || "Choose zip";
});

async function uploadProject() {
  const file = els.zipInput.files[0];
  if (!file) {
    setPanelMessage("Choose a zip first", "No file selected");
    return;
  }

  setBusy(true, "Uploading project");
  try {
    const headers = {
      "X-Project-Filename": file.name,
    };
    const target = els.appTarget.value.trim();
    if (target) {
      headers["X-App-Target"] = target;
    }

    const response = await fetch("/api/projects/upload", {
      method: "POST",
      headers,
      body: file,
    });
    const project = await parseApiResponse(response);
    state.project = project;
    renderProject(project);
    renderRoutes(project.routes || []);
    setPanelMessage("Project running", project.app_target);
    els.responseStatus.textContent = "uploaded";
    els.responseBody.textContent = JSON.stringify(project, null, 2);
  } catch (error) {
    setPanelMessage("Upload failed", errorMessage(error));
  } finally {
    setBusy(false);
  }
}

async function stopProject() {
  if (!state.project) {
    setPanelMessage("No project", "No uploaded project is running");
    return;
  }

  setBusy(true, "Stopping project");
  try {
    const response = await fetch(`/api/projects/${state.project.project_id}`, {
      method: "DELETE",
    });
    const payload = await parseApiResponse(response);
    state.project = null;
    renderRoutes([]);
    els.projectLinks.hidden = true;
    els.projectStatus.textContent = "No upload";
    els.responseStatus.textContent = "stopped";
    els.responseBody.textContent = JSON.stringify(payload, null, 2);
  } catch (error) {
    setPanelMessage("Stop failed", errorMessage(error));
  } finally {
    setBusy(false);
  }
}

async function sendProjectRequest() {
  if (!state.project) {
    setPanelMessage("Upload required", "No uploaded project is running");
    return;
  }

  const method = els.requestMethod.value;
  const path = els.requestPath.value.trim() || "/";
  const requestPayload = buildDynamicRequest(method, path);
  const clientEvent = makeClientEvent(`send ${method}`, path);

  setBusy(true, `Calling ${method} ${path}`);
  renderPending(method, path, clientEvent);

  try {
    const response = await fetch(`/api/projects/${state.project.project_id}/request`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(requestPayload),
    });
    const payload = await parseApiResponse(response);
    const responseBody = payload.response.json ?? payload.response.body;
    renderTrace({
      trace: payload.trace,
      payload: responseBody,
      statusCode: payload.response.status_code,
      statusText: "",
      clientEvent,
    });
  } catch (error) {
    renderFailure(method, path, clientEvent, error);
  } finally {
    setBusy(false);
  }
}

async function runDemoAction(actionName) {
  const action = demoActions[actionName];
  const traceId = makeTraceId(actionName);
  const request = buildDemoRequest(action, traceId);
  const clientEvent = makeClientEvent(action.label, resolveDemoUrl(action));

  setBusy(true, action.label);
  renderPending(action.method, resolveDemoUrl(action), clientEvent, traceId);

  try {
    const response = await fetch(request.url, {
      method: request.method,
      headers: request.headers,
      body: request.body,
    });
    const payload = await parsePayload(response);
    updateLatestTicket(payload, actionName);
    const trace = await fetchDemoTrace(traceId);

    renderTrace({
      trace,
      payload: payload ?? { status: "No content" },
      statusCode: response.status,
      statusText: response.statusText,
      clientEvent,
    });
  } catch (error) {
    renderFailure(action.method, resolveDemoUrl(action), clientEvent, error);
  } finally {
    setBusy(false);
  }
}

function buildDynamicRequest(method, path) {
  const bodyText = els.requestBody.value.trim();
  const request = {
    method,
    path,
    headers: {},
  };
  if (!bodyText || ["GET", "HEAD"].includes(method)) {
    return request;
  }

  try {
    request.body = JSON.parse(bodyText);
  } catch {
    request.raw_body = bodyText;
    request.headers["Content-Type"] = "text/plain";
  }
  return request;
}

function buildDemoRequest(action, traceId) {
  const body = typeof action.body === "function" ? action.body() : null;
  return {
    method: action.method,
    url: resolveDemoUrl(action),
    headers: body
      ? {
          "Content-Type": "application/json",
          "X-Trace-Id": traceId,
        }
      : {
          "X-Trace-Id": traceId,
        },
    body: body ? JSON.stringify(body) : undefined,
  };
}

function renderProject(project) {
  els.projectStatus.textContent = project.status;
  els.appTarget.value = project.app_target;
  els.openAppLink.href = project.base_url;
  els.openMonitorLink.href = `/monitor?project_id=${encodeURIComponent(project.project_id)}`;
  els.projectLinks.hidden = false;
}

function renderRoutes(routes) {
  els.routeCount.textContent = String(routes.length);
  if (!routes.length) {
    els.routeList.innerHTML = '<div class="empty-state">No routes detected</div>';
    return;
  }

  els.routeList.innerHTML = routes
    .map((route, routeIndex) =>
      route.methods
        .map(
          (method) => `
            <button class="route-button" type="button" data-route-index="${routeIndex}" data-method="${escapeHtml(method)}">
              <span class="method method-${method.toLowerCase()}">${escapeHtml(method.slice(0, 5))}</span>
              <span>${escapeHtml(route.path)}</span>
            </button>
          `,
        )
        .join(""),
    )
    .join("");

  els.routeList.querySelectorAll(".route-button").forEach((button) => {
    button.addEventListener("click", () => {
      const route = routes[Number(button.dataset.routeIndex)];
      selectRoute(button.dataset.method, route.path);
    });
  });
}

function selectRoute(method, path) {
  els.requestMethod.value = method;
  els.requestPath.value = path;
  if (["POST", "PUT", "PATCH"].includes(method) && !els.requestBody.value.trim()) {
    els.requestBody.value = "{\n  \n}";
  }
}

function renderPending(method, path, clientEvent, traceId = "pending") {
  els.traceSubtitle.textContent = `${method} ${path}`;
  els.traceId.textContent = traceId;
  els.metricMethod.textContent = method;
  els.metricStatus.textContent = "running";
  els.metricDuration.textContent = "-";
  els.metricSpans.textContent = "1";
  els.responseStatus.textContent = "pending";
  els.responseBody.textContent = "{}";
  renderFlow([clientEvent]);
  renderTimeline([clientEvent]);
  renderFunctions([]);
}

function renderTrace({ trace, payload, statusCode, statusText, clientEvent }) {
  const events = [clientEvent, ...trace.events];
  els.traceSubtitle.textContent = trace.title;
  els.traceId.textContent = trace.trace_id;
  els.metricMethod.textContent = trace.method;
  els.metricStatus.textContent = String(trace.status_code || statusCode);
  els.metricDuration.textContent = formatDuration(trace.duration_ms);
  els.metricSpans.textContent = String(events.length);
  els.responseStatus.textContent = `${statusCode} ${statusText || ""}`.trim();
  els.responseBody.textContent =
    typeof payload === "string" ? payload : JSON.stringify(payload ?? {}, null, 2);
  renderFlow(events);
  renderTimeline(events);
  renderFunctions(trace.events);
}

function renderFailure(method, path, clientEvent, error) {
  const failed = {
    ...clientEvent,
    status: "error",
    detail: errorMessage(error),
  };
  els.traceSubtitle.textContent = `${method} ${path}`;
  els.traceId.textContent = "failed";
  els.metricMethod.textContent = method;
  els.metricStatus.textContent = "error";
  els.metricDuration.textContent = "-";
  els.metricSpans.textContent = "1";
  els.responseStatus.textContent = "failed";
  els.responseBody.textContent = JSON.stringify({ error: failed.detail }, null, 2);
  renderFlow([failed]);
  renderTimeline([failed]);
  renderFunctions([]);
}

function renderFlow(events) {
  if (!events.length) {
    els.flowRail.innerHTML = '<div class="empty-state">No request selected</div>';
    return;
  }

  els.flowRail.innerHTML = events
    .slice(0, 14)
    .map(
      (event, index) => `
        <div class="flow-node kind-${escapeHtml(event.kind)} ${event.status === "error" ? "is-error" : ""}" style="animation-delay: ${index * 55}ms">
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
        <li class="timeline-item kind-${escapeHtml(event.kind)} ${event.status === "error" ? "is-error" : ""}" style="--depth: ${depth}; animation-delay: ${index * 35}ms">
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

async function parseApiResponse(response) {
  const payload = await parsePayload(response);
  if (!response.ok) {
    const detail = payload?.detail || payload?.error || response.statusText;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return payload;
}

async function parsePayload(response) {
  if (response.status === 204) {
    return null;
  }
  const contentType = response.headers.get("content-type") || "";
  if (!contentType.includes("application/json")) {
    return response.text();
  }
  return response.json();
}

async function fetchDemoTrace(traceId) {
  for (let attempt = 0; attempt < 5; attempt += 1) {
    const response = await fetch(`/api/traces/${encodeURIComponent(traceId)}`);
    if (response.ok) {
      return response.json();
    }
    await delay(80);
  }
  throw new Error("Trace was not recorded");
}

function updateLatestTicket(payload, actionName) {
  if (payload && !Array.isArray(payload) && payload.id) {
    state.latestTicketId = payload.id;
  }
  if (Array.isArray(payload) && payload.length && actionName === "list") {
    state.latestTicketId = payload[0].id;
  }
  if (actionName === "delete") {
    state.latestTicketId = 1;
  }
  els.latestTicketBadge.textContent = `Ticket #${state.latestTicketId || 1}`;
}

function setBusy(isBusy, label = "") {
  state.busy = isBusy;
  els.statusPill.textContent = isBusy ? label : "Ready";
  [...els.demoButtons, els.uploadButton, els.stopProjectButton, els.sendRequestButton].forEach((button) => {
    button.disabled = isBusy;
  });
}

function setPanelMessage(status, detail) {
  els.projectStatus.textContent = status;
  els.responseStatus.textContent = status.toLowerCase();
  els.responseBody.textContent = JSON.stringify({ message: detail }, null, 2);
}

function makeTraceId(actionName) {
  const randomPart = crypto.randomUUID
    ? crypto.randomUUID()
    : Math.random().toString(16).slice(2);
  return `traceflow-${actionName}-${randomPart}`;
}

function makeClientEvent(name, detail) {
  return {
    event_id: `client-${Date.now()}`,
    name: "clicked button",
    kind: "client",
    detail: `${name} -> ${detail}`,
    depth: 0,
    status: "ok",
    duration_ms: 0,
  };
}

function resolveDemoUrl(action) {
  return typeof action.url === "function" ? action.url() : action.url;
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

function errorMessage(error) {
  return error instanceof Error ? error.message : String(error);
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function delay(ms) {
  return new Promise((resolve) => {
    setTimeout(resolve, ms);
  });
}

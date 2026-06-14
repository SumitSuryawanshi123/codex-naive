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
  latestAnalysis: null,
  latestTicketId: 1,
  latestTrace: null,
  lastRequest: null,
  lastResponse: null,
  project: null,
  reactFlowRoot: null,
  selectedNodeId: null,
  tutorialIndex: 0,
};

const els = {
  analysisQuery: document.querySelector("#analysisQuery"),
  analysisSummary: document.querySelector("#analysisSummary"),
  analyzeTraceButton: document.querySelector("#analyzeTraceButton"),
  appTarget: document.querySelector("#appTarget"),
  debugAnalysis: document.querySelector("#debugAnalysis"),
  demoButtons: document.querySelectorAll("[data-demo-action]"),
  failureList: document.querySelector("#failureList"),
  flowRail: document.querySelector("#flowRail"),
  fixTraceButton: document.querySelector("#fixTraceButton"),
  fullscreenGraphButton: document.querySelector("#fullscreenGraphButton"),
  graphExitButton: document.querySelector("#graphExitButton"),
  graphModalSubtitle: document.querySelector("#graphModalSubtitle"),
  functionList: document.querySelector("#functionList"),
  graphCanvas: document.querySelector("#graphCanvas"),
  graphPanel: document.querySelector("#graphPanel"),
  graphPreviewText: document.querySelector("#graphPreviewText"),
  helpTutorialButton: document.querySelector("#helpTutorialButton"),
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
  selectedNodeMeta: document.querySelector("#selectedNodeMeta"),
  selectedNodePanel: document.querySelector("#selectedNodePanel"),
  selectedNodeTitle: document.querySelector("#selectedNodeTitle"),
  routeCount: document.querySelector("#routeCount"),
  routeList: document.querySelector("#routeList"),
  sendRequestButton: document.querySelector("#sendRequestButton"),
  statusPill: document.querySelector("#statusPill"),
  stopProjectButton: document.querySelector("#stopProjectButton"),
  timeline: document.querySelector("#timeline"),
  traceId: document.querySelector("#traceId"),
  traceSubtitle: document.querySelector("#traceSubtitle"),
  connectGithubButton: document.querySelector("#connectGithubButton"),
  githubBranch: document.querySelector("#githubBranch"),
  githubRepo: document.querySelector("#githubRepo"),
  githubToken: document.querySelector("#githubToken"),
  uploadButton: document.querySelector("#uploadButton"),
  zipInput: document.querySelector("#zipInput"),
  zipName: document.querySelector("#zipName"),
  elaborateNodeButton: document.querySelector("#elaborateNodeButton"),
  openGraphPreviewButton: document.querySelector("#openGraphPreviewButton"),
  tutorialBackButton: document.querySelector("#tutorialBackButton"),
  tutorialBody: document.querySelector("#tutorialBody"),
  tutorialCard: document.querySelector("#tutorialCard"),
  tutorialNextButton: document.querySelector("#tutorialNextButton"),
  tutorialOverlay: document.querySelector("#tutorialOverlay"),
  tutorialProgress: document.querySelector("#tutorialProgress"),
  tutorialSkipButton: document.querySelector("#tutorialSkipButton"),
  tutorialSpotlight: document.querySelector("#tutorialSpotlight"),
  tutorialTitle: document.querySelector("#tutorialTitle"),
};

const tutorialSteps = [
  {
    selector: ".upload-area",
    title: "Load a FastAPI project",
    body: "Choose a zip, enter an ASGI target if needed, then upload and run it under TraceFlow.",
  },
  {
    selector: ".github-connect",
    title: "Or connect GitHub",
    body: "Paste a repository URL and optional branch/token to run a project directly from GitHub.",
  },
  {
    selector: ".route-area",
    title: "Pick a route",
    body: "TraceFlow detects available routes. Selecting one fills the request builder for you.",
  },
  {
    selector: ".demo-area",
    title: "Try the demo",
    body: "The built-in ticket API is a quick way to create traces before uploading your own app.",
  },
  {
    selector: ".request-builder",
    title: "Send a request",
    body: "Adjust method, path, and JSON body, then send the request to capture execution details.",
  },
  {
    selector: ".graph-tools",
    title: "Ask and generate",
    body: "Type a debugging question and generate a node graph with summaries and failure hints.",
  },
  {
    selector: ".graph-preview",
    title: "Open the graph",
    body: "Open the modal to zoom, pan, inspect colored nodes, and elaborate on selected steps.",
  },
  {
    selector: "#debugAnalysisBox",
    title: "Investigate fixes",
    body: "For failing traces, Fix This asks DebugOS and can produce a repair package when enough context exists.",
  },
];

els.demoButtons.forEach((button) => {
  button.addEventListener("click", () => runDemoAction(button.dataset.demoAction));
});
els.uploadButton.addEventListener("click", uploadProject);
els.connectGithubButton.addEventListener("click", connectGithub);
els.stopProjectButton.addEventListener("click", stopProject);
els.sendRequestButton.addEventListener("click", sendProjectRequest);
els.analyzeTraceButton.addEventListener("click", analyzeCurrentTrace);
els.fixTraceButton.addEventListener("click", fixCurrentTrace);
els.fullscreenGraphButton.addEventListener("click", () => toggleGraphModal(true));
els.openGraphPreviewButton.addEventListener("click", () => toggleGraphModal(true));
els.graphExitButton.addEventListener("click", () => toggleGraphModal(false));
els.elaborateNodeButton.addEventListener("click", elaborateSelectedNode);
els.helpTutorialButton.addEventListener("click", startTutorial);
els.tutorialBackButton.addEventListener("click", previousTutorialStep);
els.tutorialNextButton.addEventListener("click", nextTutorialStep);
els.tutorialSkipButton.addEventListener("click", endTutorial);
document.addEventListener("keydown", (event) => {
  if (!els.tutorialOverlay.hidden) {
    if (event.key === "Escape") {
      endTutorial();
    } else if (event.key === "ArrowRight") {
      nextTutorialStep();
    } else if (event.key === "ArrowLeft") {
      previousTutorialStep();
    }
    return;
  }
  if (event.key === "Escape" && !els.graphPanel.hidden) {
    toggleGraphModal(false);
  }
});
window.addEventListener("resize", () => {
  if (!els.tutorialOverlay.hidden) {
    renderTutorialStep();
  }
});
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
    applyProject(project, "Project running");
  } catch (error) {
    setPanelMessage("Upload failed", errorMessage(error));
  } finally {
    setBusy(false);
  }
}

function startTutorial() {
  state.tutorialIndex = 0;
  els.tutorialOverlay.hidden = false;
  document.body.classList.add("tutorial-open");
  renderTutorialStep();
}

function endTutorial() {
  els.tutorialOverlay.hidden = true;
  document.body.classList.remove("tutorial-open");
  document.querySelectorAll(".tutorial-target").forEach((element) => {
    element.classList.remove("tutorial-target");
  });
}

function nextTutorialStep() {
  if (state.tutorialIndex >= tutorialSteps.length - 1) {
    endTutorial();
    return;
  }
  state.tutorialIndex += 1;
  renderTutorialStep();
}

function previousTutorialStep() {
  if (state.tutorialIndex <= 0) {
    return;
  }
  state.tutorialIndex -= 1;
  renderTutorialStep();
}

function renderTutorialStep() {
  const step = tutorialSteps[state.tutorialIndex];
  const target = document.querySelector(step.selector);
  document.querySelectorAll(".tutorial-target").forEach((element) => {
    element.classList.remove("tutorial-target");
  });

  els.tutorialProgress.textContent = `Step ${state.tutorialIndex + 1} of ${tutorialSteps.length}`;
  els.tutorialTitle.textContent = step.title;
  els.tutorialBody.textContent = step.body;
  els.tutorialBackButton.disabled = state.tutorialIndex === 0;
  els.tutorialNextButton.textContent =
    state.tutorialIndex === tutorialSteps.length - 1 ? "Done" : "Next";

  if (!target) {
    positionTutorialCard({
      top: window.innerHeight / 2 - 80,
      left: window.innerWidth / 2 - 180,
      width: 360,
      height: 160,
    });
    return;
  }

  target.classList.add("tutorial-target");
  target.scrollIntoView({ behavior: "smooth", block: "center", inline: "center" });
  window.setTimeout(() => {
    const rect = target.getBoundingClientRect();
    const paddedRect = {
      top: Math.max(12, rect.top - 8),
      left: Math.max(12, rect.left - 8),
      width: Math.min(window.innerWidth - 24, rect.width + 16),
      height: Math.min(window.innerHeight - 24, rect.height + 16),
    };
    els.tutorialSpotlight.style.top = `${paddedRect.top}px`;
    els.tutorialSpotlight.style.left = `${paddedRect.left}px`;
    els.tutorialSpotlight.style.width = `${paddedRect.width}px`;
    els.tutorialSpotlight.style.height = `${paddedRect.height}px`;
    positionTutorialCard(paddedRect);
  }, 180);
}

function positionTutorialCard(rect) {
  const cardWidth = Math.min(380, window.innerWidth - 28);
  const cardHeight = 230;
  const gap = 16;
  let top = rect.top;
  let left = rect.left + rect.width + gap;

  if (left + cardWidth > window.innerWidth - 14) {
    left = rect.left - cardWidth - gap;
  }
  if (left < 14) {
    left = Math.min(window.innerWidth - cardWidth - 14, 14);
    top = rect.top + rect.height + gap;
  }
  if (top + cardHeight > window.innerHeight - 14) {
    top = Math.max(14, window.innerHeight - cardHeight - 14);
  }

  els.tutorialCard.style.width = `${cardWidth}px`;
  els.tutorialCard.style.top = `${top}px`;
  els.tutorialCard.style.left = `${left}px`;
}

async function connectGithub() {
  const repo = els.githubRepo.value.trim();
  if (!repo) {
    setPanelMessage("GitHub connect failed", "Enter a repository URL or owner/repo");
    return;
  }

  setBusy(true, "Connecting GitHub repository");
  try {
    const payload = { repo };
    const branch = els.githubBranch.value.trim();
    const token = els.githubToken.value.trim();
    const target = els.appTarget.value.trim();
    if (branch) {
      payload.ref = branch;
    }
    if (token) {
      payload.token = token;
    }
    if (target) {
      payload.app_target = target;
    }

    const response = await fetch("/api/projects/connect-github", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const project = await parseApiResponse(response);
    applyProject(project, "GitHub project running");
  } catch (error) {
    setPanelMessage("GitHub connect failed", errorMessage(error));
  } finally {
    setBusy(false);
  }
}

function applyProject(project, successTitle) {
  state.project = project;
  renderProject(project);
  renderRoutes(project.routes || []);
  setPanelMessage(successTitle, project.app_target);
  els.responseStatus.textContent = "connected";
  els.responseBody.textContent = JSON.stringify(project, null, 2);
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
      request: payload.request,
      response: payload.response,
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
      request: { method: request.method, path: request.url },
      response: responseEnvelope(response, payload),
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

function renderTrace({ trace, payload, request, response, statusCode, statusText, clientEvent }) {
  const events = [clientEvent, ...trace.events];
  state.latestTrace = trace;
  state.lastRequest = request || { method: trace.method, path: trace.path };
  state.lastResponse = response || { status_code: statusCode, body: payload };
  state.latestAnalysis = null;
  state.selectedNodeId = null;
  els.fixTraceButton.disabled = !canFixCurrentTrace();
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
  renderGraphPlaceholder("Generate a graph for this trace");
  renderFixTraceButtonState();
  els.graphPreviewText.textContent = "Generate a graph for this trace.";
}

function renderFailure(method, path, clientEvent, error) {
  const trace = {
    trace_id: "failed",
    method,
    path,
    title: `${method} ${path}`,
    status_code: 0,
    outcome: "error",
    error: errorMessage(error),
    events: [{ ...clientEvent, status: "error", error: errorMessage(error) }],
  };
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
  state.latestTrace = trace;
  state.lastRequest = { method, path };
  state.lastResponse = { status_code: 0, body: failed.detail };
  renderFlow([failed]);
  renderTimeline([failed]);
  renderFunctions([]);
  renderFixTraceButtonState();
}

async function fixCurrentTrace() {
  if (!state.latestTrace) {
    setPanelMessage("No trace", "Run a request before asking for a fix");
    return;
  }

  setBusy(true, "Generating fix");
  renderDebugAnalysisMessage("Analyzing trace with DebugOS...");
  try {
    const debugPromise = fetch("/api/debug/fix/detail", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        project_id: state.project?.project_id || null,
        request: state.lastRequest,
        response: state.lastResponse,
        trace: state.latestTrace,
        query: els.analysisQuery.value.trim(),
        analysis: state.latestAnalysis,
      }),
    }).then(parseApiResponse);

    if (state.latestAnalysis) {
      const response = await fetch("/api/analysis/fix", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          trace: state.latestTrace,
          project_id: state.project?.project_id || null,
          query: els.analysisQuery.value.trim(),
          analysis: state.latestAnalysis,
        }),
      });
      if (!response.ok) {
        const payload = await parsePayload(response);
        throw new Error(payload?.detail || response.statusText);
      }
      const blob = await response.blob();
      downloadBlob(blob, "traceflow-fix.zip");
      els.responseStatus.textContent = "fix ready";
      els.responseBody.textContent = JSON.stringify(
        {
          file: "traceflow-fix.zip",
          project: state.project?.name || "trace notes",
        },
        null,
        2,
      );
    }

    const report = await debugPromise;
    renderDebugAnalysis(report);
  } catch (error) {
    renderDebugAnalysisError(errorMessage(error));
    setPanelMessage("Fix failed", errorMessage(error));
  } finally {
    setBusy(false);
    renderFixTraceButtonState();
  }
}

function renderDebugAnalysis(report) {
  const cause = report.top_cause || report.ranked_causes?.[0];
  const remediation = report.remediation?.[0] || report.remediation_suggestions?.[0];
  if (!cause) {
    renderDebugAnalysisMessage("DebugOS could not rank a cause from this trace.");
    return;
  }

  const failure = report.failure || {};
  const alternatives = report.alternatives || [];
  const evidenceRequests = report.evidence_requests || [];
  const nextSteps = report.recommended_next_steps || [];
  const graphContext = report.graph_context;
  const timeline = report.timeline || [];

  els.debugAnalysis.innerHTML = `
    <div class="debug-result">
      <p class="debug-status">Investigation status: <strong>${escapeHtml(report.status || "unknown")}</strong></p>
      <p class="debug-failure">${escapeHtml(failure.summary || "")}</p>
      <p><strong>${escapeHtml(cause.category)}</strong> evidence score ${escapeHtml(cause.evidence_score)}/10</p>
      <p>${escapeHtml(cause.statement)}</p>
      ${
        remediation
          ? `<p><strong>Suggested remediation:</strong> ${escapeHtml(remediation.action)}</p>
             <p><strong>Validation:</strong> ${escapeHtml(remediation.validation)}</p>`
          : ""
      }
      ${
        alternatives.length
          ? `<details>
              <summary>Alternative causes (${alternatives.length})</summary>
              <ul class="debug-alt-list">
                ${alternatives
                  .map(
                    (item) =>
                      `<li><strong>${escapeHtml(item.category)}</strong> (${escapeHtml(item.evidence_score)}/10) - ${escapeHtml(item.statement)}</li>`,
                  )
                  .join("")}
              </ul>
            </details>`
          : ""
      }
      ${
        evidenceRequests.length
          ? `<details>
              <summary>Evidence requests (${evidenceRequests.length})</summary>
              <ul class="debug-alt-list">
                ${evidenceRequests
                  .map(
                    (item) =>
                      `<li><strong>${escapeHtml(item.what)}</strong><br>${escapeHtml(item.why)}<br><em>Expected:</em> ${escapeHtml(item.expected_signal)}</li>`,
                  )
                  .join("")}
              </ul>
            </details>`
          : ""
      }
      ${
        nextSteps.length
          ? `<details open>
              <summary>Recommended next steps (${nextSteps.length})</summary>
              <ul class="debug-alt-list">
                ${nextSteps
                  .map(
                    (item) =>
                      `<li><strong>${escapeHtml(item.title)}</strong> [${escapeHtml(item.type)}]<br>${escapeHtml(item.detail)}${
                        item.validation ? `<br><em>Validation:</em> ${escapeHtml(item.validation)}` : ""
                      }</li>`,
                  )
                  .join("")}
              </ul>
            </details>`
          : ""
      }
      ${
        graphContext?.failure_points?.length
          ? `<details>
              <summary>Graph failure points (${graphContext.failure_points.length})</summary>
              <ul class="debug-alt-list">
                ${graphContext.failure_points
                  .map(
                    (item) =>
                      `<li><strong>${escapeHtml(item.node_id || "node")}</strong> (${escapeHtml(item.confidence || "unknown")})<br>${escapeHtml(item.reason || "")}</li>`,
                  )
                  .join("")}
              </ul>
            </details>`
          : ""
      }
      ${
        timeline.length
          ? `<details>
              <summary>Timeline (${timeline.length})</summary>
              <ul class="debug-alt-list">
                ${timeline
                  .slice(0, 8)
                  .map(
                    (item) =>
                      `<li><strong>${escapeHtml(item.timestamp)}</strong> [${escapeHtml(item.type)}] ${escapeHtml(item.text)}</li>`,
                  )
                  .join("")}
              </ul>
            </details>`
          : ""
      }
      <details>
        <summary>Verified signals (${cause.signals?.length || 0})</summary>
        <pre>${escapeHtml(JSON.stringify(cause.signals || [], null, 2))}</pre>
      </details>
    </div>
  `;
}

function renderDebugAnalysisMessage(message) {
  els.debugAnalysis.textContent = message;
}

function renderDebugAnalysisError(message) {
  els.debugAnalysis.innerHTML = `<p class="error-text">${escapeHtml(message)}</p>`;
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

async function analyzeCurrentTrace() {
  if (!state.latestTrace) {
    setPanelMessage("No trace", "Run a request before generating a graph");
    return;
  }

  setBusy(true, "Analyzing trace");
  renderGraphPlaceholder("Asking OpenAI for trace analysis");
  try {
    const response = await fetch("/api/analysis/trace", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        trace: state.latestTrace,
        project_id: state.project?.project_id || null,
        query: els.analysisQuery.value.trim(),
      }),
    });
    const analysis = await parseApiResponse(response);
    state.latestAnalysis = analysis;
    toggleGraphModal(true);
    renderGraphAnalysis(analysis);
    renderFixTraceButtonState();
    els.fixTraceButton.disabled = false;
    els.graphPreviewText.textContent = `${analysis.nodes?.length || 0} nodes ready. Open graph to zoom and inspect.`;
  } catch (error) {
    renderGraphPlaceholder(errorMessage(error));
  } finally {
    setBusy(false);
  }
}

function renderGraphPlaceholder(message) {
  unmountReactFlow();
  state.selectedNodeId = null;
  els.graphCanvas.innerHTML = `<div class="empty-state">${escapeHtml(message)}</div>`;
  els.analysisSummary.textContent = "No graph generated yet.";
  renderSelectedNode(null);
  els.failureList.innerHTML = "";
  els.graphModalSubtitle.textContent = message;
}

function renderGraphAnalysis(analysis) {
  renderGraph(analysis.nodes || [], analysis.edges || []);
  const sourceNote = analysis.llm_used
    ? `OpenAI model: ${analysis.model || "unknown"}`
    : `OpenAI inactive: ${analysis.llm_error || "using deterministic fallback summaries"}`;
  els.analysisSummary.innerHTML = `${markdownToHtml(analysis.summary || "No analysis returned.")}<br><br><small>${escapeHtml(sourceNote)}</small>`;
  renderSelectedNode(null);
  const failures = analysis.failure_points || [];
  els.failureList.innerHTML = failures.length
    ? failures
        .map(
          (failure) => `
            <li>
              <strong>${escapeHtml(failure.node_id || "possible issue")} - ${escapeHtml(failure.confidence || "unknown")}</strong>
              ${markdownToHtml(failure.reason || "")}
            </li>
          `,
        )
        .join("")
    : '<li><strong>No failure points</strong>No explicit failure was found in this trace.</li>';
}

async function elaborateSelectedNode() {
  if (!state.selectedNodeId) {
    return;
  }
  await elaborateNode(state.selectedNodeId);
}

async function elaborateNode(nodeId) {
  if (!state.latestTrace || !state.latestAnalysis) {
    return;
  }
  const node = (state.latestAnalysis.nodes || []).find((item) => item.id === nodeId);
  if (!node) {
    return;
  }

  els.analysisSummary.innerHTML = `Loading details for <strong>${escapeHtml(node.label || node.name)}</strong>...`;
  try {
    const response = await fetch("/api/analysis/elaborate", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        trace: state.latestTrace,
        node,
        project_id: state.project?.project_id || null,
        query: els.analysisQuery.value.trim(),
      }),
    });
    const payload = await parseApiResponse(response);
    const sourceNote = payload.llm_used
      ? `OpenAI model: ${payload.model || "unknown"}`
      : `OpenAI inactive: ${payload.llm_error || "using deterministic fallback explanation"}`;
    els.analysisSummary.innerHTML = `${markdownToHtml(payload.markdown || "No elaboration returned.")}<br><br><small>${escapeHtml(sourceNote)}</small>`;
  } catch (error) {
    els.analysisSummary.textContent = errorMessage(error);
  }
}

function selectGraphNode(nodeId) {
  state.selectedNodeId = nodeId;
  const node = (state.latestAnalysis?.nodes || []).find((item) => item.id === nodeId);
  renderSelectedNode(node || null);
  if (state.latestAnalysis) {
    renderGraph(state.latestAnalysis.nodes || [], state.latestAnalysis.edges || []);
  }
}

function renderSelectedNode(node) {
  if (!node) {
    els.selectedNodePanel.hidden = true;
    els.selectedNodeTitle.textContent = "No node selected";
    els.selectedNodeMeta.textContent = "Click a graph node to inspect it.";
    return;
  }
  els.selectedNodePanel.hidden = false;
  els.selectedNodeTitle.textContent = node.name || node.label || "Trace node";
  els.selectedNodeMeta.textContent = `${node.kind || "node"} - ${node.status || "unknown"} - ${formatDuration(node.duration_ms)}`;
}

function toggleGraphFullscreen(force) {
  toggleGraphModal(force);
}

function toggleGraphModal(force) {
  const shouldOpen =
    typeof force === "boolean" ? force : els.graphPanel.hidden;
  els.graphPanel.hidden = !shouldOpen;
  document.body.classList.toggle("graph-modal-open", shouldOpen);
  els.fullscreenGraphButton.textContent = shouldOpen ? "Graph Open" : "Open Graph";
  if (shouldOpen && state.latestAnalysis) {
    window.setTimeout(() => renderGraph(state.latestAnalysis.nodes || [], state.latestAnalysis.edges || []), 0);
  }
}

function renderReactFlowGraph(nodes, edges) {
  const reactFlow = window.ReactFlow;
  const React = window.React;
  const ReactDOM = window.ReactDOM;
  const FlowComponent = reactFlow?.default || reactFlow?.ReactFlow;
  if (!React || !ReactDOM || !FlowComponent) {
    return false;
  }

  const positions = layoutGraphWithEdges(nodes, edges);
  const flowNodes = nodes.map((node) => ({
    id: node.id,
    position: positions[node.id],
    data: {
      label: React.createElement(GraphNodeLabel, {
        node,
      }),
    },
    className: `react-flow-node kind-${node.kind || "function"} ${node.status === "error" ? "is-error" : ""} ${node.id === state.selectedNodeId ? "is-selected" : ""}`,
    style: { width: 300 },
  }));
  const flowEdges = edges.map((edge, index) => ({
    id: `${edge.from}-${edge.to}-${index}`,
    source: edge.from,
    target: edge.to,
    type: "smoothstep",
    markerEnd: {
      type: "arrowclosed",
      color: "#475569",
      width: 18,
      height: 18,
    },
    style: {
      stroke: "#475569",
      strokeWidth: 3,
    },
  }));

  if (!state.reactFlowRoot) {
    els.graphCanvas.innerHTML = "";
    state.reactFlowRoot = ReactDOM.createRoot(els.graphCanvas);
  }
  state.reactFlowRoot.render(
    React.createElement(
      FlowComponent,
      {
        nodes: flowNodes,
        edges: flowEdges,
        fitView: true,
        minZoom: 0.35,
        maxZoom: 1.6,
        nodesDraggable: true,
        nodesConnectable: false,
        elementsSelectable: true,
        onNodeClick: (_event, node) => selectGraphNode(node.id),
      },
      reactFlow.Background ? React.createElement(reactFlow.Background, { gap: 32, color: "#e2e8f0" }) : null,
      reactFlow.Controls ? React.createElement(reactFlow.Controls, null) : null,
      reactFlow.MiniMap ? React.createElement(reactFlow.MiniMap, { pannable: true, zoomable: true }) : null,
    ),
  );
  return true;
}

function GraphNodeLabel({ node }) {
  const React = window.React;
  return React.createElement(
    "div",
    { className: "rf-node-label" },
    React.createElement("span", null, node.kind || "node"),
    React.createElement("strong", { title: node.name || node.label }, node.label || node.name),
    React.createElement("div", {
      className: "rf-node-markdown",
      dangerouslySetInnerHTML: { __html: markdownToHtml(node.markdown || node.detail || "") },
    }),
  );
}

function unmountReactFlow() {
  if (state.reactFlowRoot) {
    state.reactFlowRoot.unmount();
    state.reactFlowRoot = null;
  }
}

function renderGraph(nodes, edges) {
  if (!nodes.length) {
    renderGraphPlaceholder("No graph nodes returned");
    return;
  }
  if (renderReactFlowGraph(nodes, edges)) {
    return;
  }

  unmountReactFlow();
  const positions = layoutGraph(nodes);
  const width = Math.max(920, Math.max(...positions.map((position) => position.x)) + 330);
  const height = Math.max(520, Math.max(...positions.map((position) => position.y)) + 220);
  const positionById = Object.fromEntries(positions.map((position) => [position.id, position]));

  const lines = edges
    .map((edge) => {
      const from = positionById[edge.from];
      const to = positionById[edge.to];
      if (!from || !to) {
        return "";
      }
      const x1 = from.x + 260;
      const y1 = from.y + 84;
      const x2 = to.x;
      const y2 = to.y + 84;
      return `<path d="M ${x1} ${y1} C ${x1 + 42} ${y1}, ${x2 - 42} ${y2}, ${x2} ${y2}" stroke="#94a3b8" stroke-width="2" fill="none" marker-end="url(#arrow)" />`;
    })
    .join("");

  const nodeHtml = nodes
    .map((node) => {
      const position = positionById[node.id];
      return `
        <article class="graph-node kind-${escapeHtml(node.kind)} ${node.status === "error" ? "is-error" : ""} ${node.id === state.selectedNodeId ? "is-selected" : ""}" data-node-id="${escapeHtml(node.id)}" style="left: ${position.x}px; top: ${position.y}px">
          <span>${escapeHtml(node.kind || "node")}</span>
          <strong title="${escapeHtml(node.name || node.label)}">${escapeHtml(node.label || node.name)}</strong>
          <p>${markdownToHtml(node.markdown || node.detail || "")}</p>
        </article>
      `;
    })
    .join("");

  els.graphCanvas.innerHTML = `
    <div style="position: relative; width: ${width}px; height: ${height}px">
      <svg class="graph-svg" viewBox="0 0 ${width} ${height}" aria-hidden="true">
        <defs>
          <marker id="arrow" markerWidth="10" markerHeight="8" refX="8" refY="4" orient="auto">
            <path d="M 0 0 L 10 4 L 0 8 z" fill="#94a3b8"></path>
          </marker>
        </defs>
        ${lines}
      </svg>
      ${nodeHtml}
    </div>
  `;
  els.graphCanvas.querySelectorAll(".graph-node").forEach((nodeElement) => {
    nodeElement.addEventListener("click", () => selectGraphNode(nodeElement.dataset.nodeId));
  });
}

function layoutGraph(nodes) {
  return layoutGraphFromEdges(nodes, state.latestAnalysis?.edges || []);
}

function layoutGraphWithEdges(nodes, edges) {
  return Object.fromEntries(
    layoutGraphFromEdges(nodes, edges).map((position) => [
      position.id,
      {
        x: position.x,
        y: position.y,
      },
    ]),
  );
}

function layoutGraphFromEdges(nodes, edges) {
  const childrenByParent = new Map();
  const depthById = new Map([[nodes[0].id, 0]]);
  const idSet = new Set(nodes.map((node) => node.id));
  edges.forEach((edge) => {
    if (!idSet.has(edge.from) || !idSet.has(edge.to)) {
      return;
    }
    if (!childrenByParent.has(edge.from)) {
      childrenByParent.set(edge.from, []);
    }
    childrenByParent.get(edge.from).push(edge.to);
  });

  const queue = [nodes[0].id];
  while (queue.length) {
    const parent = queue.shift();
    const depth = depthById.get(parent) || 0;
    (childrenByParent.get(parent) || []).forEach((child) => {
      if (!depthById.has(child)) {
        depthById.set(child, depth + 1);
        queue.push(child);
      }
    });
  }

  const rowByDepth = new Map();
  return nodes.map((node, index) => {
    const depth = depthById.get(node.id) ?? Math.min(index, 5);
    const row = rowByDepth.get(depth) || 0;
    rowByDepth.set(depth, row + 1);
    return {
      id: node.id,
      x: 32 + depth * 330,
      y: 32 + row * 210,
    };
  });
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
  [
    ...els.demoButtons,
    els.uploadButton,
    els.stopProjectButton,
    els.sendRequestButton,
    els.analyzeTraceButton,
    els.fixTraceButton,
  ].forEach((button) => {
    button.disabled = isBusy;
  });
  if (!isBusy) {
    renderFixTraceButtonState();
  }
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

function responseEnvelope(response, payload) {
  return {
    status_code: response.status,
    body: typeof payload === "string" ? payload : JSON.stringify(payload ?? {}),
    json: typeof payload === "object" && payload !== null ? payload : null,
  };
}

function canFixCurrentTrace() {
  const trace = state.latestTrace;
  const response = state.lastResponse || {};
  if (!trace) {
    return false;
  }
  const statusCode = Number(response.status_code || trace.status_code || 0);
  return (
    statusCode >= 400 ||
    trace.outcome === "error" ||
    Boolean(trace.error) ||
    (trace.events || []).some((event) => event.status === "error" || event.error)
  );
}

function renderFixTraceButtonState() {
  els.fixTraceButton.disabled = state.busy || !canFixCurrentTrace();
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

function markdownToHtml(value) {
  return escapeHtml(value)
    .replaceAll(/`([^`]+)`/g, "<code>$1</code>")
    .replaceAll(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replaceAll(/\n/g, "<br>");
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function delay(ms) {
  return new Promise((resolve) => {
    setTimeout(resolve, ms);
  });
}

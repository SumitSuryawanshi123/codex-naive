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
  project: null,
  reactFlowRoot: null,
  selectedNodeId: null,
};

const els = {
  analysisQuery: document.querySelector("#analysisQuery"),
  analysisSummary: document.querySelector("#analysisSummary"),
  analyzeTraceButton: document.querySelector("#analyzeTraceButton"),
  appTarget: document.querySelector("#appTarget"),
  demoButtons: document.querySelectorAll("[data-demo-action]"),
  failureList: document.querySelector("#failureList"),
  flowRail: document.querySelector("#flowRail"),
  fixTraceButton: document.querySelector("#fixTraceButton"),
  fullscreenGraphButton: document.querySelector("#fullscreenGraphButton"),
  graphExitButton: document.querySelector("#graphExitButton"),
  functionList: document.querySelector("#functionList"),
  graphCanvas: document.querySelector("#graphCanvas"),
  graphPanel: document.querySelector("#graphPanel"),
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
  uploadButton: document.querySelector("#uploadButton"),
  zipInput: document.querySelector("#zipInput"),
  zipName: document.querySelector("#zipName"),
  elaborateNodeButton: document.querySelector("#elaborateNodeButton"),
};

els.demoButtons.forEach((button) => {
  button.addEventListener("click", () => runDemoAction(button.dataset.demoAction));
});
els.uploadButton.addEventListener("click", uploadProject);
els.stopProjectButton.addEventListener("click", stopProject);
els.sendRequestButton.addEventListener("click", sendProjectRequest);
els.analyzeTraceButton.addEventListener("click", analyzeCurrentTrace);
els.fixTraceButton.addEventListener("click", fixCurrentTrace);
els.fullscreenGraphButton.addEventListener("click", toggleGraphFullscreen);
els.graphExitButton.addEventListener("click", () => toggleGraphFullscreen(false));
els.elaborateNodeButton.addEventListener("click", elaborateSelectedNode);
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && els.graphPanel.classList.contains("is-fullscreen")) {
    toggleGraphFullscreen(false);
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
  state.latestTrace = trace;
  state.latestAnalysis = null;
  state.selectedNodeId = null;
  els.fixTraceButton.disabled = true;
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
    renderGraphAnalysis(analysis);
    els.fixTraceButton.disabled = false;
  } catch (error) {
    renderGraphPlaceholder(errorMessage(error));
  } finally {
    setBusy(false);
  }
}

async function fixCurrentTrace() {
  if (!state.latestTrace) {
    setPanelMessage("No trace", "Run a request before asking for a fix");
    return;
  }

  setBusy(true, "Generating fix zip");
  try {
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
  } catch (error) {
    setPanelMessage("Fix failed", errorMessage(error));
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
  const shouldOpen =
    typeof force === "boolean" ? force : !els.graphPanel.classList.contains("is-fullscreen");
  els.graphPanel.classList.toggle("is-fullscreen", shouldOpen);
  els.fullscreenGraphButton.textContent = shouldOpen ? "Exit Full Screen" : "Full Screen";
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
      reactFlow.Background ? React.createElement(reactFlow.Background, { gap: 24 }) : null,
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
  [...els.demoButtons, els.uploadButton, els.stopProjectButton, els.sendRequestButton, els.analyzeTraceButton].forEach((button) => {
    button.disabled = isBusy;
  });
  els.fixTraceButton.disabled = isBusy || !state.latestAnalysis;
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

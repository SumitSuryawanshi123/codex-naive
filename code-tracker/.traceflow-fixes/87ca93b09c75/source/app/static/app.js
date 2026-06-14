const state = {
  agents: [],
  customers: [],
  tickets: [],
  selectedTicketId: null,
};

const selectors = {
  totalTickets: document.querySelector("#totalTickets"),
  urgentTickets: document.querySelector("#urgentTickets"),
  openTickets: document.querySelector("#openTickets"),
  progressTickets: document.querySelector("#progressTickets"),
  ticketCount: document.querySelector("#ticketCount"),
  ticketList: document.querySelector("#ticketList"),
  emptyState: document.querySelector("#emptyState"),
  ticketDetail: document.querySelector("#ticketDetail"),
  detailSubject: document.querySelector("#detailSubject"),
  detailDescription: document.querySelector("#detailDescription"),
  ticketMeta: document.querySelector("#ticketMeta"),
  detailCustomer: document.querySelector("#detailCustomer"),
  detailCompany: document.querySelector("#detailCompany"),
  detailAgent: document.querySelector("#detailAgent"),
  detailDue: document.querySelector("#detailDue"),
  detailStatus: document.querySelector("#detailStatus"),
  detailPriority: document.querySelector("#detailPriority"),
  detailAgentSelect: document.querySelector("#detailAgentSelect"),
  commentsList: document.querySelector("#commentsList"),
  toast: document.querySelector("#toast"),
  newCustomer: document.querySelector("#newCustomer"),
  newAgent: document.querySelector("#newAgent"),
};

const statusClass = (status) => `status-${status.toLowerCase().replaceAll(" ", "-")}`;
const priorityClass = (priority) => `priority-${priority.toLowerCase()}`;

function formatDate(value) {
  if (!value) {
    return "Not set";
  }
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers ?? {}) },
    ...options,
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with ${response.status}`);
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

function showToast(message) {
  selectors.toast.textContent = message;
  selectors.toast.classList.remove("hidden");
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => selectors.toast.classList.add("hidden"), 2600);
}

function buildTicketUrl() {
  const params = new URLSearchParams();
  const q = document.querySelector("#searchInput").value.trim();
  const status = document.querySelector("#statusFilter").value;
  const priority = document.querySelector("#priorityFilter").value;

  if (q) params.set("q", q);
  if (status) params.set("status", status);
  if (priority) params.set("priority", priority);

  const query = params.toString();
  return `/api/tickets${query ? `?${query}` : ""}`;
}

async function loadStats() {
  const stats = await api("/api/stats");
  selectors.totalTickets.textContent = stats.total ?? 0;
  selectors.urgentTickets.textContent = stats.urgent_open ?? 0;
  selectors.openTickets.textContent = stats.by_status?.Open ?? 0;
  selectors.progressTickets.textContent = stats.by_status?.["In Progress"] ?? 0;
}

async function loadLookups() {
  const [customers, agents] = await Promise.all([api("/api/customers"), api("/api/agents")]);
  state.customers = customers;
  state.agents = agents;
  renderLookups();
}

function renderLookups() {
  selectors.newCustomer.innerHTML = state.customers
    .map((customer) => `<option value="${customer.id}">${escapeHtml(customer.company)} - ${escapeHtml(customer.name)}</option>`)
    .join("");

  const agentOptions = [
    '<option value="">Unassigned</option>',
    ...state.agents.map((agent) => `<option value="${agent.id}">${escapeHtml(agent.name)} (${escapeHtml(agent.role)})</option>`),
  ].join("");

  selectors.newAgent.innerHTML = agentOptions;
  selectors.detailAgentSelect.innerHTML = agentOptions;
}

async function loadTickets({ keepSelection = true } = {}) {
  state.tickets = await api(buildTicketUrl());
  selectors.ticketCount.textContent = state.tickets.length;
  renderTickets();

  if (!keepSelection || !state.tickets.some((ticket) => ticket.id === state.selectedTicketId)) {
    state.selectedTicketId = state.tickets[0]?.id ?? null;
  }

  if (state.selectedTicketId) {
    await loadTicketDetail(state.selectedTicketId);
  } else {
    showEmptyState();
  }
}

function renderTickets() {
  if (!state.tickets.length) {
    selectors.ticketList.innerHTML = '<div class="ticket-card"><h3>No tickets found</h3><p>Adjust filters or create a new ticket.</p></div>';
    return;
  }

  selectors.ticketList.innerHTML = state.tickets
    .map(
      (ticket) => `
        <button class="ticket-card ${ticket.id === state.selectedTicketId ? "active" : ""}" type="button" data-ticket-id="${ticket.id}">
          <div class="ticket-topline">
            <div class="pill-row">
              <span class="status-pill ${statusClass(ticket.status)}">${escapeHtml(ticket.status)}</span>
              <span class="priority-pill ${priorityClass(ticket.priority)}">${escapeHtml(ticket.priority)}</span>
            </div>
            <span>#${ticket.id}</span>
          </div>
          <h3>${escapeHtml(ticket.subject)}</h3>
          <p>${escapeHtml(ticket.customer_company)} · ${escapeHtml(ticket.agent_name || "Unassigned")}</p>
        </button>
      `
    )
    .join("");
}

function showEmptyState() {
  selectors.emptyState.classList.remove("hidden");
  selectors.ticketDetail.classList.add("hidden");
}

async function loadTicketDetail(ticketId) {
  const ticket = await api(`/api/tickets/${ticketId}`);
  state.selectedTicketId = ticket.id;
  renderTickets();
  renderTicketDetail(ticket);
}

function renderTicketDetail(ticket) {
  selectors.emptyState.classList.add("hidden");
  selectors.ticketDetail.classList.remove("hidden");

  selectors.detailSubject.textContent = ticket.subject;
  selectors.detailDescription.textContent = ticket.description;
  selectors.ticketMeta.textContent = `#${ticket.id} · ${ticket.category} · ${ticket.source}`;
  selectors.detailCustomer.textContent = `${ticket.customer_name} (${ticket.customer_tier})`;
  selectors.detailCompany.textContent = ticket.customer_company;
  selectors.detailAgent.textContent = ticket.agent_name || "Unassigned";
  selectors.detailDue.textContent = formatDate(ticket.due_at);
  selectors.detailStatus.value = ticket.status;
  selectors.detailPriority.value = ticket.priority;
  selectors.detailAgentSelect.value = ticket.agent_id ?? "";

  selectors.commentsList.innerHTML = ticket.comments.length
    ? ticket.comments
        .map(
          (comment) => `
            <article class="comment">
              <strong>${escapeHtml(comment.author)}</strong>
              <p>${escapeHtml(comment.body)}</p>
              <time datetime="${escapeHtml(comment.created_at)}">${formatDate(comment.created_at)}</time>
            </article>
          `
        )
        .join("")
    : '<p class="description">No notes yet.</p>';
}

async function refreshAll(options = {}) {
  await Promise.all([loadStats(), loadTickets(options)]);
}

document.querySelector("#ticketList").addEventListener("click", async (event) => {
  const card = event.target.closest("[data-ticket-id]");
  if (!card) {
    return;
  }
  await loadTicketDetail(Number(card.dataset.ticketId));
});

document.querySelector("#filtersForm").addEventListener("input", async () => {
  await loadTickets({ keepSelection: false });
});

document.querySelector("#refreshButton").addEventListener("click", async () => {
  await refreshAll();
  showToast("Queue refreshed");
});

document.querySelector("#createTicketForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const payload = {
    subject: document.querySelector("#newSubject").value.trim(),
    description: document.querySelector("#newDescription").value.trim(),
    customer_id: Number(document.querySelector("#newCustomer").value),
    priority: document.querySelector("#newPriority").value,
    category: document.querySelector("#newCategory").value.trim() || "General",
    agent_id: document.querySelector("#newAgent").value ? Number(document.querySelector("#newAgent").value) : null,
    source: "Portal",
  };

  const ticket = await api("/api/tickets", {
    method: "POST",
    body: JSON.stringify(payload),
  });

  form.reset();
  document.querySelector("#newCategory").value = "General";
  state.selectedTicketId = ticket.id;
  await refreshAll();
  showToast("Ticket created");
});

document.querySelector("#updateForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!state.selectedTicketId) {
    return;
  }

  await api(`/api/tickets/${state.selectedTicketId}`, {
    method: "PATCH",
    body: JSON.stringify({
      status: selectors.detailStatus.value,
      priority: selectors.detailPriority.value,
      agent_id: selectors.detailAgentSelect.value ? Number(selectors.detailAgentSelect.value) : null,
    }),
  });

  await refreshAll();
  showToast("Ticket updated");
});

document.querySelector("#commentForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!state.selectedTicketId) {
    return;
  }

  await api(`/api/tickets/${state.selectedTicketId}/comments`, {
    method: "POST",
    body: JSON.stringify({
      author: document.querySelector("#commentAuthor").value.trim(),
      body: document.querySelector("#commentBody").value.trim(),
    }),
  });

  document.querySelector("#commentBody").value = "";
  await refreshAll();
  showToast("Note added");
});

document.querySelector("#deleteTicketButton").addEventListener("click", async () => {
  if (!state.selectedTicketId || !window.confirm("Delete this ticket?")) {
    return;
  }

  await api(`/api/tickets/${state.selectedTicketId}`, { method: "DELETE" });
  state.selectedTicketId = null;
  await refreshAll({ keepSelection: false });
  showToast("Ticket deleted");
});

document.querySelector("#exportInvoiceButton").addEventListener("click", async () => {
  if (!state.selectedTicketId) {
    return;
  }

  const scenario = window.prompt(
    "Optional demo scenario: missing_config, billing_timeout (leave blank for default auth/data failure)",
    "",
  );
  const query = scenario ? `?scenario=${encodeURIComponent(scenario.trim())}` : "";
  const authorization = window.prompt(
    "Authorization header value (leave blank to trigger 403 missing bearer token)",
    "",
  );

  try {
    await api(`/api/tickets/${state.selectedTicketId}/export-invoice${query}`, {
      method: "POST",
      body: JSON.stringify({ authorization: authorization || null }),
    });
    showToast("Invoice exported");
  } catch (error) {
    showToast(`Export failed (expected for demo): ${error.message}`);
    console.error("Demo export failure:", error);
  }
});

async function start() {
  try {
    await loadLookups();
    await refreshAll({ keepSelection: false });
  } catch (error) {
    showToast(error.message);
    console.error(error);
  }
}

start();

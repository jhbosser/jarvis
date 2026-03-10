const API_BASE_STORAGE_KEY = "jarvis_api_base_url";

function normalizeApiBase(value) {
  return String(value || "").trim().replace(/\/+$/, "");
}

function getApiBase() {
  const saved = localStorage.getItem(API_BASE_STORAGE_KEY);
  return normalizeApiBase(saved);
}

function buildApiUrl(path) {
  const base = getApiBase();
  return base ? `${base}${path}` : path;
}

function setApiBaseFeedback(message, isError = false) {
  const target = document.querySelector("#api-base-feedback");
  if (!target) return;
  target.textContent = message;
  target.style.color = isError ? "#a83122" : "";
}

const api = {
  async get(path) {
    const response = await fetch(buildApiUrl(path));
    return handleResponse(response);
  },
  async post(path, body) {
    const response = await fetch(buildApiUrl(path), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    return handleResponse(response);
  },
};

function handleResponse(response) {
  if (!response.ok) {
    return response
      .json()
      .then((data) => {
        throw new Error(data.detail || "Request failed.");
      })
      .catch(() => {
        throw new Error(`HTTP ${response.status}: request failed.`);
      });
  }
  return response.json();
}

function renderCards(container, items, renderItem) {
  container.innerHTML = "";
  if (!items.length) {
    container.innerHTML = '<p class="empty-state">Nenhum item encontrado.</p>';
    return;
  }
  items.forEach((item) => {
    const element = document.createElement("article");
    element.className = "card";
    element.innerHTML = renderItem(item);
    container.appendChild(element);
  });
}

async function loadOverview() {
  const data = await api.get("/api/overview");
  renderCards(
    document.querySelector("#today-list"),
    data.today_logs,
    (entry) => `<strong>Registro</strong><span>${escapeHtml(entry)}</span>`,
  );
  document.querySelector("#working-context").textContent = data.working_context;
  renderReminders(data.pending_reminders);
}

function renderReminders(items) {
  renderCards(
    document.querySelector("#reminders-list"),
    items,
    (item) => `
      <strong>${escapeHtml(item.title)}</strong>
      <div class="reminder-meta">${escapeHtml(item.datetime)} • ${escapeHtml(item.status)}</div>
      ${
        item.status === "pending"
          ? `<button class="link-button" data-complete-id="${escapeHtml(item.id)}">Concluir</button>`
          : ""
      }
    `,
  );
}

async function refreshReminders() {
  const data = await api.get("/api/reminders");
  renderReminders(data.items);
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

async function handleLogSubmit(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const text = form.elements.text.value.trim();
  if (!text) return;

  try {
    const data = await api.post("/api/log", { text });
    document.querySelector("#log-feedback").textContent = `Salvo: ${data.entry}`;
    form.reset();
    await loadOverview();
  } catch (error) {
    document.querySelector("#log-feedback").textContent = error.message;
  }
}

async function handleReminderSubmit(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const title = form.elements.title.value.trim();
  const datetime = form.elements.datetime.value.trim();
  if (!title || !datetime) return;

  try {
    const data = await api.post("/api/reminders", { title, datetime });
    document.querySelector("#reminder-feedback").textContent =
      `Lembrete criado: ${data.title} em ${data.datetime}`;
    form.reset();
    await loadOverview();
  } catch (error) {
    document.querySelector("#reminder-feedback").textContent = error.message;
  }
}

async function handleSearchSubmit(event) {
  event.preventDefault();
  const query = event.currentTarget.elements.query.value.trim();
  if (!query) return;

  try {
    const data = await api.get(`/api/search?q=${encodeURIComponent(query)}`);
    renderCards(
      document.querySelector("#search-logs"),
      data.logs,
      (entry) => `<strong>Log</strong><span>${escapeHtml(entry)}</span>`,
    );
    renderCards(
      document.querySelector("#search-map"),
      data.memory_map,
      (entry) => `<strong>Mapa</strong><pre>${escapeHtml(entry)}</pre>`,
    );
  } catch (error) {
    document.querySelector("#search-logs").innerHTML = `<p class="empty-state">${escapeHtml(error.message)}</p>`;
    document.querySelector("#search-map").innerHTML = "";
  }
}

async function handleReminderActions(event) {
  const button = event.target.closest("[data-complete-id]");
  if (!button) return;

  try {
    await api.post(`/api/reminders/${button.dataset.completeId}/complete`, {});
    await loadOverview();
  } catch (error) {
    document.querySelector("#reminder-feedback").textContent = error.message;
  }
}

async function testApiConnection() {
  try {
    const health = await api.get("/health");
    if (health.status !== "ok") {
      throw new Error("Health endpoint respondeu sem status ok.");
    }
    const base = getApiBase();
    setApiBaseFeedback(
      base ? `Conectado em ${base}` : "Conectado em API local (mesmo dominio).",
    );
  } catch (error) {
    setApiBaseFeedback(error.message, true);
  }
}

function initializeApiBaseConfig() {
  const input = document.querySelector("#api-base-url");
  const saveButton = document.querySelector("#save-api-base");
  const testButton = document.querySelector("#test-api-base");
  if (!input || !saveButton || !testButton) return;

  input.value = getApiBase();

  saveButton.addEventListener("click", () => {
    const normalized = normalizeApiBase(input.value);
    if (normalized) {
      localStorage.setItem(API_BASE_STORAGE_KEY, normalized);
      input.value = normalized;
      setApiBaseFeedback(`URL salva: ${normalized}`);
    } else {
      localStorage.removeItem(API_BASE_STORAGE_KEY);
      setApiBaseFeedback("URL limpa. Usando API no mesmo dominio.");
    }
  });

  testButton.addEventListener("click", () => {
    testApiConnection();
  });
}

function registerScrollButtons() {
  document.querySelectorAll("[data-scroll-target]").forEach((button) => {
    button.addEventListener("click", () => {
      document.getElementById(button.dataset.scrollTarget)?.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    });
  });
}

function bootstrap() {
  initializeApiBaseConfig();
  document.querySelector("#log-form").addEventListener("submit", handleLogSubmit);
  document
    .querySelector("#reminder-form")
    .addEventListener("submit", handleReminderSubmit);
  document
    .querySelector("#search-form")
    .addEventListener("submit", handleSearchSubmit);
  document
    .querySelector("#refresh-overview")
    .addEventListener("click", () => loadOverview());
  document
    .querySelector("#refresh-reminders")
    .addEventListener("click", () => refreshReminders());
  document
    .querySelector("#reminders-list")
    .addEventListener("click", handleReminderActions);
  registerScrollButtons();
  loadOverview().catch((error) => {
    document.querySelector("#working-context").textContent = error.message;
    setApiBaseFeedback(
      "Nao foi possivel carregar o painel. Verifique a URL da API e teste a conexao.",
      true,
    );
  });
}

window.addEventListener("DOMContentLoaded", bootstrap);

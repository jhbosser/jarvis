const API_BASE_STORAGE_KEY = "jarvis_api_base_url";
const DEFAULT_REMOTE_API = "https://jarvis-twwu.onrender.com";

function normalizeApiBase(value) {
  return String(value || "").trim().replace(/\/+$/, "");
}

function isNetlifyHost() {
  return window.location.hostname.endsWith("netlify.app");
}

function getApiBase() {
  const saved = normalizeApiBase(localStorage.getItem(API_BASE_STORAGE_KEY));
  if (saved) return saved;
  if (isNetlifyHost()) return DEFAULT_REMOTE_API;
  return "";
}

function buildApiUrl(path) {
  const base = getApiBase();
  return base ? `${base}${path}` : path;
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

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function renderResponse(title, payload) {
  const container = document.querySelector("#response-log");
  const card = document.createElement("article");
  card.className = "response-item";
  card.innerHTML = `
    <h3>${escapeHtml(title)}</h3>
    <pre>${escapeHtml(JSON.stringify(payload, null, 2))}</pre>
  `;
  container.prepend(card);
}

function setStatus(message, isError = false) {
  const status = document.querySelector("#connection-status");
  status.textContent = message;
  status.style.color = isError ? "#9d1e0f" : "";
}

async function probeConnection() {
  try {
    const health = await api.get("/health");
    if (health.status !== "ok") {
      throw new Error("Health endpoint sem status ok.");
    }
    const base = getApiBase();
    setStatus(base ? `Conectado em ${base}` : "Conectado na API local.");
  } catch (error) {
    setStatus(`Falha de conexao: ${error.message}`, true);
  }
}

async function submitPrompt(rawText) {
  const text = rawText.trim();
  if (!text) return;

  if (text.toLowerCase().startsWith("/api ")) {
    const url = normalizeApiBase(text.slice(5));
    if (!url) {
      renderResponse("Erro", { detail: "Use: /api https://seu-backend" });
      return;
    }
    localStorage.setItem(API_BASE_STORAGE_KEY, url);
    await probeConnection();
    renderResponse("Config API", { api_base_url: url, saved: true });
    return;
  }

  try {
    const result = await api.post("/api/prompt", { text });
    renderResponse(result.summary || result.mode || "Resposta", result.payload || {});
  } catch (error) {
    renderResponse("Erro", { detail: error.message });
  }
}

function registerPromptInput() {
  const input = document.querySelector("#prompt-input");
  input.addEventListener("keydown", async (event) => {
    if (event.key !== "Enter" || event.shiftKey) return;
    event.preventDefault();
    const value = input.value;
    input.value = "";
    await submitPrompt(value);
  });
}

function bootstrap() {
  registerPromptInput();
  probeConnection();
  renderResponse("Dica", {
    envio: "Digite no prompt e pressione Enter.",
    quebra_linha: "Use Shift+Enter.",
    api_override: "Opcional: /api https://seu-backend",
    ajuda: "Digite help para ver comandos.",
  });
}

window.addEventListener("DOMContentLoaded", bootstrap);

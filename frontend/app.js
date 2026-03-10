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

function pushChatMessage(role, title, message) {
  const container = document.querySelector("#chat-history");
  const item = document.createElement("article");
  item.className = `chat-item ${role}`;
  item.innerHTML = `
    <h3>${escapeHtml(title)}</h3>
    <pre>${escapeHtml(message)}</pre>
  `;
  container.appendChild(item);
  container.scrollTop = container.scrollHeight;
}

function payloadToText(mode, summary, payload) {
  const lines = [];
  if (summary) {
    lines.push(summary);
  }

  if (!payload || typeof payload !== "object") {
    return lines.join("\n");
  }

  if (Array.isArray(payload.entries) && payload.entries.length) {
    lines.push("", "Registros:");
    payload.entries.forEach((entry) => lines.push(`- ${entry}`));
  }

  if (typeof payload.content === "string" && payload.content.trim()) {
    lines.push("", payload.content);
  }

  if (Array.isArray(payload.logs) && payload.logs.length) {
    lines.push("", "Log matches:");
    payload.logs.forEach((entry) => lines.push(`- ${entry}`));
  }

  if (Array.isArray(payload.memory_map) && payload.memory_map.length) {
    lines.push("", "Memory map:");
    payload.memory_map.forEach((block) => lines.push(block, ""));
  }

  if (Array.isArray(payload.items) && payload.items.length) {
    lines.push("", "Lembretes:");
    payload.items.forEach((item) => {
      lines.push(
        `- #${item.id || "?"} ${item.title || ""} | ${item.datetime || ""} | ${item.status || ""}`,
      );
    });
  }

  if (payload.item && typeof payload.item === "object") {
    const item = payload.item;
    lines.push(
      "",
      `#${item.id || "?"} ${item.title || ""} | ${item.datetime || ""} | ${item.status || ""}`,
    );
  }

  if (payload.entry) {
    lines.push("", `Entry: ${payload.entry}`);
  }

  if (payload.conversation_path) {
    lines.push("", `conversation: ${payload.conversation_path}`);
  }
  if (payload.summary_path) {
    lines.push(`summary: ${payload.summary_path}`);
  }

  if (lines.length === 1 && Object.keys(payload).length > 0) {
    lines.push("", JSON.stringify(payload, null, 2));
  }

  return lines.join("\n").trim();
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
    pushChatMessage("assistant", "Jarvis", `Falha de conexao: ${error.message}`);
  }
}

async function submitPrompt(rawText) {
  const text = rawText.trim();
  if (!text) return;
  pushChatMessage("user", "Voce", text);

  if (text.toLowerCase().startsWith("/api ")) {
    const url = normalizeApiBase(text.slice(5));
    if (!url) {
      pushChatMessage("assistant", "Jarvis", "Erro: use /api https://seu-backend");
      return;
    }
    localStorage.setItem(API_BASE_STORAGE_KEY, url);
    await probeConnection();
    pushChatMessage("assistant", "Jarvis", `API salva: ${url}`);
    return;
  }

  try {
    const result = await api.post("/api/prompt", { text });
    const responseText = payloadToText(
      result.mode || "response",
      result.summary || "",
      result.payload || {},
    );
    pushChatMessage("assistant", "Jarvis", responseText || "(Sem resposta)");
  } catch (error) {
    pushChatMessage("assistant", "Jarvis", `Erro: ${error.message}`);
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
  pushChatMessage(
    "assistant",
    "Jarvis",
    [
      "Digite sua instrucao e pressione Enter.",
      "Use Shift+Enter para quebra de linha.",
      "Comandos: help, today, context, search: termo, remind: titulo | data, done: id.",
      "Para trocar API: /api https://seu-backend",
    ].join("\n"),
  );
}

window.addEventListener("DOMContentLoaded", bootstrap);

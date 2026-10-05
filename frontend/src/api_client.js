const API_BASE = window.SONG_AI_API_BASE || "";

export function apiUrl(path) {
  return `${API_BASE}${path}`;
}

export async function readApiPayload(response, fallbackData = {}) {
  const raw = await response.text().catch(() => "");
  let payload = { ok: false, data: fallbackData, detail: raw || "API no disponible" };
  if (raw) {
    try {
      payload = JSON.parse(raw);
    } catch (_) {
      payload.detail = raw;
    }
  }
  if (!response.ok || payload.ok === false) {
    return { ok: false, data: fallbackData, detail: payload.detail || "API no disponible" };
  }
  return payload;
}

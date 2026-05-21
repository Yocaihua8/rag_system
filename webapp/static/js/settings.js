import { apiGet, apiPost } from "./api.js";

export async function loadLlmSettings() {
  return apiGet("/api/settings/llm");
}

export async function saveLlmSettings(form) {
  const data = Object.fromEntries(new FormData(form));
  return apiPost("/api/settings/llm", {
    provider: data.provider,
    api_base: data.api_base,
    model: data.model,
    api_key: data.api_key,
  });
}

export async function testLlmSettings() {
  return apiPost("/api/settings/llm/test", {});
}

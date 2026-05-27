import { apiGet, apiPost } from "./client.js";

export async function loadLlmSettings() {
  const data = await apiGet("/api/settings/llm");
  return data.settings || {};
}

export async function saveLlmSettings({ provider, apiBase, model, apiKey }) {
  const payload = {
    provider,
    api_base: apiBase,
    model,
    api_key: apiKey,
  };
  const data = await apiPost("/api/settings/llm", payload);
  return data.settings || {};
}

export async function testLlmSettings() {
  return apiPost("/api/settings/llm/test", {});
}

export async function listModelProfiles() {
  return apiGet("/api/model-profiles");
}

export async function saveModelProfile(profile) {
  const payload = {
    profile_id: profile.id || profile.profile_id || "",
    name: String(profile.name || "").trim(),
    provider: profile.provider,
    api_base: profile.apiBase,
    model: String(profile.model || "").trim(),
    temperature: profile.temperature,
    max_tokens: profile.maxTokens,
    api_key_ref: profile.apiKeyRef,
  };
  const path = payload.profile_id ? "/api/model-profiles/update" : "/api/model-profiles";
  return apiPost(path, payload);
}

export async function deleteModelProfile(profileId) {
  if (!profileId) {
    throw new Error("请选择模型 Profile");
  }
  return apiPost("/api/model-profiles/delete", { profile_id: profileId });
}

export async function setDefaultModelProfile(profileId) {
  return apiPost("/api/model-profiles/default", { profile_id: profileId || "" });
}

export async function testModelProfile(profileId) {
  if (!profileId) {
    throw new Error("请选择模型 Profile");
  }
  return apiPost("/api/model-profiles/test", { profile_id: profileId });
}

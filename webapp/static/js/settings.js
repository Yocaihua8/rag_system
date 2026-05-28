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

export async function listModelProfiles() {
  return apiGet("/api/model-profiles");
}

export async function saveModelProfile(form) {
  const data = Object.fromEntries(new FormData(form));
  const payload = {
    profile_id: data.profile_id || "",
    name: data.name,
    provider: data.provider,
    api_base: data.api_base,
    model: data.model,
    temperature: data.temperature,
    max_tokens: data.max_tokens,
    api_key_ref: data.api_key_ref,
  };
  const path = payload.profile_id ? "/api/model-profiles/update" : "/api/model-profiles";
  return apiPost(path, payload);
}

export async function deleteModelProfile(profileId) {
  return apiPost("/api/model-profiles/delete", { profile_id: profileId });
}

export async function setDefaultModelProfile(profileId) {
  return apiPost("/api/model-profiles/default", { profile_id: profileId });
}

export async function testModelProfile(profileId) {
  return apiPost("/api/model-profiles/test", { profile_id: profileId });
}

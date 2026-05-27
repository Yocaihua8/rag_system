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

export async function listPromptPresets(projectId) {
  if (!projectId) {
    throw new Error("请先创建或选择项目空间");
  }
  return apiGet(`/api/prompt-presets?project_id=${encodeURIComponent(projectId)}`);
}

export async function savePromptPreset(preset) {
  const payload = {
    project_id: preset.projectId,
    preset_id: preset.id || preset.preset_id || "",
    name: String(preset.name || "").trim(),
    description: String(preset.description || "").trim(),
    system_prompt: String(preset.systemPrompt || preset.system_prompt || "").trim(),
    answer_format: String(preset.answerFormat || preset.answer_format || "").trim(),
  };
  const path = payload.preset_id ? "/api/prompt-presets/update" : "/api/prompt-presets";
  return apiPost(path, payload);
}

export async function deletePromptPreset(presetId) {
  if (!presetId) {
    throw new Error("请选择 Prompt 预设");
  }
  return apiPost("/api/prompt-presets/delete", { preset_id: presetId });
}

export async function setDefaultPromptPreset({ projectId, presetId }) {
  if (!projectId) {
    throw new Error("请先创建或选择项目空间");
  }
  return apiPost("/api/prompt-presets/default", {
    project_id: projectId,
    preset_id: presetId || "",
  });
}

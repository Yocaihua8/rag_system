import { apiGet, apiPost } from "./client.js";

function requiredText(value, message) {
  const cleanValue = String(value || "").trim();
  if (!cleanValue) {
    throw new Error(message);
  }
  return cleanValue;
}

function requiredProjectId(projectId) {
  return requiredText(projectId, "请先创建或选择项目空间");
}

export async function startObsidianPairing({ projectId, outputRoot = "" }) {
  const payload = {
    project_id: requiredProjectId(projectId),
  };
  const cleanOutputRoot = String(outputRoot || "").trim().replace(/\/+$/, "");
  if (cleanOutputRoot) {
    payload.output_root = cleanOutputRoot;
  }
  return apiPost("/api/obsidian/pairing/start", payload);
}

export async function listObsidianConnections(projectId) {
  const query = new URLSearchParams({
    project_id: requiredProjectId(projectId),
  });
  const data = await apiGet(`/api/obsidian/connections?${query.toString()}`);
  return data.connections || [];
}

export async function revokeObsidianConnection({ projectId, connectionId }) {
  return apiPost("/api/obsidian/connections/revoke", {
    project_id: requiredProjectId(projectId),
    connection_id: requiredText(connectionId, "请选择 Obsidian 连接"),
  });
}

export async function previewObsidianPublication({
  projectId,
  artifactTypes,
  assessmentSessionIds,
  sourcePublicationId,
}) {
  const payload = {
    project_id: requiredProjectId(projectId),
  };
  if (artifactTypes !== undefined) {
    payload.artifact_types = artifactTypes;
  }
  if (assessmentSessionIds !== undefined) {
    payload.assessment_session_ids = assessmentSessionIds;
  }
  const cleanSourcePublicationId = String(sourcePublicationId || "").trim();
  if (cleanSourcePublicationId) {
    payload.source_publication_id = cleanSourcePublicationId;
  }
  const data = await apiPost("/api/obsidian/publications/preview", payload);
  return data;
}

export async function confirmObsidianPublication({ projectId, publicationId }) {
  const data = await apiPost("/api/obsidian/publications/confirm", {
    project_id: requiredProjectId(projectId),
    publication_id: requiredText(publicationId, "请选择待发布版本"),
  });
  return data;
}

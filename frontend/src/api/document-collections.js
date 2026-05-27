import { apiGet } from "./client.js";

export async function listDocumentCollections(projectId) {
  if (!projectId) {
    return [];
  }
  const params = new URLSearchParams({ project_id: projectId });
  const data = await apiGet(`/api/document-collections?${params.toString()}`);
  return data.collections || [];
}

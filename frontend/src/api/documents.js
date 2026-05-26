import { apiGet } from "./client.js";

export async function listDocuments(projectId, collectionId = "") {
  if (!projectId) {
    return [];
  }
  const params = new URLSearchParams({ project_id: projectId });
  if (collectionId) {
    params.set("collection_id", collectionId);
  }
  const data = await apiGet(`/api/documents?${params.toString()}`);
  return data.documents || [];
}

export async function getDocument(documentId) {
  if (!documentId) {
    throw new Error("请选择要预览的文档");
  }
  const data = await apiGet(`/api/document?document_id=${encodeURIComponent(documentId)}`);
  return data.document || null;
}

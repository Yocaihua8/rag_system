import { apiGet, apiPost } from "./client.js";

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

export async function deleteDocument(documentId) {
  if (!documentId) {
    throw new Error("请选择要删除的文档");
  }
  return apiPost("/api/documents/delete", { document_id: documentId });
}

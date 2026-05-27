import { apiGet, apiPost } from "./client.js";

export async function listDocumentCollections(projectId) {
  if (!projectId) {
    return [];
  }
  const params = new URLSearchParams({ project_id: projectId });
  const data = await apiGet(`/api/document-collections?${params.toString()}`);
  return data.collections || [];
}

export async function createDocumentCollection({ projectId, name }) {
  if (!projectId) {
    throw new Error("请先创建或选择项目空间");
  }
  const cleanName = name.trim();
  if (!cleanName) {
    throw new Error("请输入文档集合名称");
  }
  return apiPost("/api/document-collections", {
    project_id: projectId,
    name: cleanName,
  });
}

export async function deleteDocumentCollection(collectionId) {
  if (!collectionId) {
    throw new Error("请选择文档集合");
  }
  return apiPost("/api/document-collections/delete", { collection_id: collectionId });
}

export async function updateDocumentCollection({ collectionId, name }) {
  if (!collectionId) {
    throw new Error("请选择文档集合");
  }
  const cleanName = name.trim();
  if (!cleanName) {
    throw new Error("请输入文档集合名称");
  }
  return apiPost("/api/document-collections/update", {
    collection_id: collectionId,
    name: cleanName,
  });
}

export async function addDocumentToCollection({ collectionId, documentId }) {
  if (!collectionId) {
    throw new Error("请选择文档集合");
  }
  if (!documentId) {
    throw new Error("请选择文档");
  }
  return apiPost("/api/document-collections/items/add", {
    collection_id: collectionId,
    document_ids: [documentId],
  });
}

export async function removeDocumentFromCollection({ collectionId, documentId }) {
  if (!collectionId) {
    throw new Error("请选择文档集合");
  }
  if (!documentId) {
    throw new Error("请选择文档");
  }
  return apiPost("/api/document-collections/items/remove", {
    collection_id: collectionId,
    document_ids: [documentId],
  });
}

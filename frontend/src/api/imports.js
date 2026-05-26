import { apiGet, apiPost } from "./client.js";

export async function importPlainTextNote({ projectId, title, content }) {
  if (!projectId) {
    throw new Error("请先创建或选择项目空间");
  }
  const cleanTitle = title.trim();
  const cleanContent = content.trim();
  if (!cleanTitle) {
    throw new Error("请输入笔记标题");
  }
  if (!cleanContent) {
    throw new Error("请输入笔记正文");
  }
  return apiPost("/api/import/note", {
    project_id: projectId,
    title: cleanTitle,
    content: cleanContent,
  });
}

export async function importUrlExcerpt({ projectId, url, title, content }) {
  if (!projectId) {
    throw new Error("请先创建或选择项目空间");
  }
  const cleanUrl = url.trim();
  const cleanTitle = title.trim();
  const cleanContent = content.trim();
  if (!cleanUrl) {
    throw new Error("请输入 URL");
  }
  if (!cleanTitle) {
    throw new Error("请输入网页标题");
  }
  if (!cleanContent) {
    throw new Error("请输入网页正文或摘要");
  }
  return apiPost("/api/import/url", {
    project_id: projectId,
    url: cleanUrl,
    title: cleanTitle,
    content: cleanContent,
  });
}

export async function importBrowserFiles({ projectId, files }) {
  const uploadFiles = await buildUploadFiles(files);
  const payload = {
    source_type: "file_upload",
    files: uploadFiles,
  };
  if (projectId) {
    payload.project_id = projectId;
  } else {
    payload.project_name = "browser-upload";
  }
  return apiPost("/api/import/upload", payload);
}

export async function listImportBatches(projectId) {
  if (!projectId) {
    return [];
  }
  const params = new URLSearchParams({ project_id: projectId });
  const data = await apiGet(`/api/import/batches?${params.toString()}`);
  return data.batches || [];
}

export async function getImportBatchDetail(batchId) {
  if (!batchId) {
    throw new Error("请选择导入批次");
  }
  return apiGet(`/api/import/batches/detail?batch_id=${encodeURIComponent(batchId)}`);
}

async function buildUploadFiles(fileList) {
  const selectedFiles = Array.from(fileList || []);
  if (selectedFiles.length === 0) {
    throw new Error("请选择一个或多个本地文件");
  }
  return Promise.all(selectedFiles.map(readUploadFile));
}

async function readUploadFile(file) {
  const suffix = fileSuffix(file.name);
  if (BINARY_UPLOAD_SUFFIXES.has(suffix)) {
    return {
      relative_path: file.name,
      content_base64: await fileToBase64(file),
      size: file.size,
    };
  }
  return {
    relative_path: file.name,
    content: await file.text(),
  };
}

async function fileToBase64(file) {
  const buffer = await file.arrayBuffer();
  const bytes = new Uint8Array(buffer);
  let binary = "";
  for (const byte of bytes) {
    binary += String.fromCharCode(byte);
  }
  return btoa(binary);
}

function fileSuffix(path) {
  const index = path.lastIndexOf(".");
  return index === -1 ? "" : path.slice(index).toLowerCase();
}

const BINARY_UPLOAD_SUFFIXES = new Set([".docx", ".pdf"]);

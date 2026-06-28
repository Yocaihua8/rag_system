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

export async function syncProjectDirectory({ projectId }) {
  if (!projectId) {
    throw new Error("请先创建或选择项目空间");
  }
  return apiPost("/api/import", {
    project_id: projectId,
  });
}

export async function previewProjectImport({ projectId }) {
  if (!projectId) {
    throw new Error("请先创建或选择项目空间");
  }
  const params = new URLSearchParams({ project_id: projectId });
  const data = await apiGet(`/api/import/preview?${params.toString()}`);
  return data.preview || null;
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

export async function importBrowserFolder({ files }) {
  const normalizedFiles = buildBrowserFolderEntries(files);
  const uploadFiles = await Promise.all(normalizedFiles.map(readFolderUploadFile));
  const projectName = normalizedFiles.find((entry) => entry.projectName)?.projectName || "浏览器导入项目";
  const payload = {
    source_type: "browser_folder_upload",
    files: uploadFiles,
  };
  payload.project_name = projectName;
  return apiPost("/api/import/upload", payload);
}

export async function importNotionZip({ projectId, file }) {
  if (!projectId) {
    throw new Error("请先创建或选择项目空间");
  }
  if (!file || fileSuffix(file.name) !== ".zip") {
    throw new Error("请选择 Notion 导出的 zip 文件");
  }
  return apiPost("/api/import/notion-zip", {
    project_id: projectId,
    filename: file.name,
    content_base64: await fileToBase64(file),
  });
}

export async function importObsidianVault({ projectId, vaultPath }) {
  if (!projectId) {
    throw new Error("请先创建或选择项目空间");
  }
  const cleanVaultPath = String(vaultPath || "").trim();
  if (!cleanVaultPath) {
    throw new Error("请输入 Obsidian vault 本机目录");
  }
  return apiPost("/api/import/obsidian-vault", {
    project_id: projectId,
    vault_path: cleanVaultPath,
  });
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

function buildBrowserFolderEntries(fileList) {
  const selectedFiles = Array.from(fileList || []);
  if (selectedFiles.length === 0) {
    throw new Error("请选择一个本地项目文件夹");
  }
  return selectedFiles.map(normalizeBrowserFolderFile);
}

function normalizeBrowserFolderFile(file) {
  const rawPath = file.webkitRelativePath || file.name;
  const parts = rawPath.replace(/\\/g, "/").split("/").filter(Boolean);
  const projectName = parts.length > 1 ? parts[0] : "浏览器导入项目";
  const relativePath = parts.length > 1 ? parts.slice(1).join("/") : parts.join("/");
  return { file, rawPath, projectName, relativePath };
}

async function readFolderUploadFile(entry) {
  const suffix = fileSuffix(entry.relativePath);
  if (BINARY_UPLOAD_SUFFIXES.has(suffix)) {
    return {
      relative_path: entry.relativePath,
      content_base64: await fileToBase64(entry.file),
      size: entry.file.size,
    };
  }
  return {
    relative_path: entry.relativePath,
    content: await entry.file.text(),
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

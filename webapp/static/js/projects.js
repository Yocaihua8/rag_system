import { apiGet, apiPost } from "./api.js";
import { state } from "./state.js";

const SELECTED_PROJECT_STORAGE_KEY = "knowledge-island:selected-project-id";

export async function refreshProjects(selectEl) {
  const data = await apiGet("/api/projects");
  state.projects = data.projects;
  selectEl.innerHTML = "";
  for (const project of state.projects) {
    const option = document.createElement("option");
    option.value = project.id;
    option.textContent = project.name;
    selectEl.appendChild(option);
  }
  const restoredProjectId = chooseProjectId();
  selectEl.value = restoredProjectId;
  state.selectedProjectId = selectEl.value || "";
  persistSelectedProject(state.selectedProjectId);
}

export async function createProject(form) {
  const data = Object.fromEntries(new FormData(form));
  const response = await apiPost("/api/projects", data);
  state.selectedProjectId = response.project.id;
  persistSelectedProject(state.selectedProjectId);
  return response.project;
}

export async function importSelectedProject() {
  if (!state.selectedProjectId) {
    throw new Error("请先选择项目空间");
  }
  const selectedProject = state.projects.find((project) => project.id === state.selectedProjectId);
  if (selectedProject?.root_exists === false) {
    throw new Error("项目目录不存在，无法导入。");
  }
  return apiPost("/api/import", { project_id: state.selectedProjectId });
}

export async function importBrowserFolder(files) {
  const payload = await buildBrowserFolderPayload(files);
  const response = await apiPost("/api/import/upload", payload);
  state.selectedProjectId = response.project.id;
  persistSelectedProject(state.selectedProjectId);
  response.result.skipped += payload.clientSkippedDetails.length;
  response.result.skipped_details = [
    ...response.result.skipped_details,
    ...payload.clientSkippedDetails,
  ];
  return response;
}

export async function renameSelectedProject(name) {
  if (!state.selectedProjectId) {
    throw new Error("请先选择项目空间");
  }
  const cleanName = name.trim();
  if (!cleanName) {
    throw new Error("请输入新的项目名称");
  }
  return apiPost("/api/projects/rename", {
    project_id: state.selectedProjectId,
    name: cleanName,
  });
}

export async function deleteSelectedProject() {
  if (!state.selectedProjectId) {
    throw new Error("请先选择项目空间");
  }
  const response = await apiPost("/api/projects/delete", { project_id: state.selectedProjectId });
  state.selectedProjectId = "";
  localStorage.removeItem(SELECTED_PROJECT_STORAGE_KEY);
  return response;
}

export function selectProject(projectId) {
  state.selectedProjectId = projectId || "";
  persistSelectedProject(state.selectedProjectId);
}

export async function listDocuments() {
  if (!state.selectedProjectId) {
    return { documents: [] };
  }
  return apiGet(`/api/documents?project_id=${encodeURIComponent(state.selectedProjectId)}`);
}

export async function getDocument(documentId) {
  return apiGet(`/api/document?document_id=${encodeURIComponent(documentId)}`);
}

export async function deleteDocument(documentId) {
  return apiPost("/api/documents/delete", { document_id: documentId });
}

function chooseProjectId() {
  const savedProjectId = localStorage.getItem(SELECTED_PROJECT_STORAGE_KEY);
  if (state.projects.some((project) => project.id === savedProjectId)) {
    return savedProjectId;
  }
  if (state.projects.some((project) => project.id === state.selectedProjectId)) {
    return state.selectedProjectId;
  }
  return state.projects[0]?.id || "";
}

function persistSelectedProject(projectId) {
  if (projectId) {
    localStorage.setItem(SELECTED_PROJECT_STORAGE_KEY, projectId);
  } else {
    localStorage.removeItem(SELECTED_PROJECT_STORAGE_KEY);
  }
}

async function buildBrowserFolderPayload(fileList) {
  const files = Array.from(fileList || []);
  if (files.length === 0) {
    throw new Error("请选择一个本地项目文件夹");
  }
  const normalized = files.map(normalizeBrowserFile);
  const projectName = normalized.find((entry) => entry.projectName)?.projectName || "浏览器导入项目";
  const uploadFiles = [];
  const clientSkippedDetails = [];
  for (const entry of normalized) {
    const reason = getClientSkipReason(entry.relativePath, entry.file);
    if (reason) {
      clientSkippedDetails.push({ path: entry.relativePath || entry.rawPath, reason });
      continue;
    }
    uploadFiles.push({
      relative_path: entry.relativePath,
      content: await entry.file.text(),
    });
  }
  if (uploadFiles.length === 0) {
    throw new Error("未找到可导入的文本文件");
  }
  return {
    project_name: projectName,
    files: uploadFiles,
    clientSkippedDetails,
  };
}

function normalizeBrowserFile(file) {
  const rawPath = file.webkitRelativePath || file.name;
  const parts = rawPath.replace(/\\/g, "/").split("/").filter(Boolean);
  const projectName = parts.length > 1 ? parts[0] : "浏览器导入项目";
  const relativePath = parts.length > 1 ? parts.slice(1).join("/") : parts.join("/");
  return { file, rawPath, projectName, relativePath };
}

function getClientSkipReason(relativePath, file) {
  if (!relativePath || relativePath.includes(":") || relativePath.split("/").some((part) => part === "..")) {
    return "invalid relative path";
  }
  const parts = relativePath.split("/");
  if (parts.slice(0, -1).some((part) => IGNORED_DIR_NAMES.has(part))) {
    return "ignored directory";
  }
  if (!TEXT_SUFFIXES.has(fileSuffix(relativePath))) {
    return "unsupported file type";
  }
  if (file.size > MAX_TEXT_FILE_BYTES) {
    return "file too large";
  }
  return "";
}

function fileSuffix(path) {
  const index = path.lastIndexOf(".");
  return index === -1 ? "" : path.slice(index).toLowerCase();
}

const TEXT_SUFFIXES = new Set([
  ".cfg",
  ".css",
  ".html",
  ".ini",
  ".js",
  ".json",
  ".jsx",
  ".md",
  ".py",
  ".sql",
  ".toml",
  ".ts",
  ".tsx",
  ".txt",
  ".yaml",
  ".yml",
]);

const IGNORED_DIR_NAMES = new Set([
  ".agents",
  ".claude",
  ".codex",
  ".git",
  ".hg",
  ".idea",
  ".mypy_cache",
  ".pytest_cache",
  ".ruff_cache",
  ".svn",
  ".tox",
  ".vscode",
  ".venv",
  "build",
  "dist",
  "node_modules",
  "__pycache__",
]);

const MAX_TEXT_FILE_BYTES = 1000000;

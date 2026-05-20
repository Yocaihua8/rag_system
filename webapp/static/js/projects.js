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

import { apiGet, apiPost } from "./client.js";
import { appState } from "../state/app-state.js";

export const PROJECT_SELECTION_STORAGE_KEY = "knowledge-island:selected-project-id";

export async function listProjects() {
  const data = await apiGet("/api/projects");
  return data.projects || [];
}

export async function loadProjects() {
  const projects = await listProjects();
  appState.projects = projects;
  const restoredProjectId = restoreSelectedProjectId(projects);
  appState.selectedProjectId = restoredProjectId;
  persistSelectedProjectId(restoredProjectId);
  return projects;
}

export async function createProject(payload) {
  const response = await apiPost("/api/projects", payload);
  const project = response.project;
  appState.projects = [
    project,
    ...appState.projects.filter((item) => item.id !== project.id),
  ];
  selectProject(project.id);
  return project;
}

export async function renameProject({ projectId, name }) {
  if (!projectId) {
    throw new Error("请选择项目空间");
  }
  const cleanName = (name || "").trim();
  if (!cleanName) {
    throw new Error("请输入项目空间名称");
  }
  const response = await apiPost("/api/projects/rename", {
    project_id: projectId,
    name: cleanName,
  });
  const project = response.project;
  appState.projects = appState.projects.map((item) => (item.id === project.id ? project : item));
  return project;
}

export async function deleteProject(projectId) {
  if (!projectId) {
    throw new Error("请选择项目空间");
  }
  const response = await apiPost("/api/projects/delete", { project_id: projectId });
  appState.projects = appState.projects.filter((project) => project.id !== projectId);
  if (appState.selectedProjectId === projectId) {
    selectProject("");
  }
  return response;
}

export async function getRetrievalSettings(projectId) {
  if (!projectId) {
    return null;
  }
  const data = await apiGet(`/api/projects/retrieval-settings?project_id=${encodeURIComponent(projectId)}`);
  return data.settings || null;
}

export async function getProjectSummary(projectId) {
  if (!projectId) {
    return null;
  }
  const data = await apiGet(`/api/projects/summary?project_id=${encodeURIComponent(projectId)}`);
  return data.summary || null;
}

export async function saveRetrievalSettings({ projectId, topK, minScore, useKeyword, useVector }) {
  if (!projectId) {
    throw new Error("请先创建或选择项目空间");
  }
  const data = await apiPost("/api/projects/retrieval-settings", {
    project_id: projectId,
    top_k: Number(topK),
    min_score: Number(minScore),
    use_keyword: Boolean(useKeyword),
    use_vector: Boolean(useVector),
  });
  return data.settings || null;
}

export function selectProject(projectId) {
  appState.selectedProjectId = projectId || "";
  persistSelectedProjectId(appState.selectedProjectId);
}

export function restoreSelectedProjectId(projects) {
  const savedProjectId = readSelectedProjectId();
  if (projects.some((project) => project.id === savedProjectId)) {
    return savedProjectId;
  }
  if (projects.some((project) => project.id === appState.selectedProjectId)) {
    return appState.selectedProjectId;
  }
  return projects[0]?.id || "";
}

function readSelectedProjectId() {
  if (typeof localStorage === "undefined") {
    return "";
  }
  return localStorage.getItem(PROJECT_SELECTION_STORAGE_KEY) || "";
}

function persistSelectedProjectId(projectId) {
  if (typeof localStorage === "undefined") {
    return;
  }
  if (projectId) {
    localStorage.setItem(PROJECT_SELECTION_STORAGE_KEY, projectId);
  } else {
    localStorage.removeItem(PROJECT_SELECTION_STORAGE_KEY);
  }
}

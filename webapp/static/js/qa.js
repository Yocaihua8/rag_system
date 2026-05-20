import { apiPost } from "./api.js";
import { state } from "./state.js";

export async function ask(question) {
  if (!state.selectedProjectId) {
    throw new Error("请先创建或选择项目空间");
  }
  return apiPost("/api/answer", {
    project_id: state.selectedProjectId,
    question,
  });
}

export async function search(query) {
  if (!state.selectedProjectId) {
    throw new Error("请先创建或选择项目空间");
  }
  return apiPost("/api/search", {
    project_id: state.selectedProjectId,
    query,
  });
}

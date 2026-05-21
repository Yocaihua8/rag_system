import { apiGet, apiPost } from "./api.js";
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

export async function listChatMessages() {
  if (!state.selectedProjectId) {
    return { messages: [] };
  }
  return apiGet(`/api/chat/messages?project_id=${encodeURIComponent(state.selectedProjectId)}`);
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

export async function startAssessment() {
  if (!state.selectedProjectId) {
    throw new Error("请先创建或选择项目空间");
  }
  return apiPost("/api/assessment/start", {
    project_id: state.selectedProjectId,
  });
}

export async function submitAssessmentAnswer(answer) {
  if (!state.selectedProjectId) {
    throw new Error("请先创建或选择项目空间");
  }
  if (!state.assessmentQuestion) {
    throw new Error("请先开始评估");
  }
  return apiPost("/api/assessment/answer", {
    project_id: state.selectedProjectId,
    question: state.assessmentQuestion,
    answer,
  });
}

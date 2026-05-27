import { apiPost } from "./client.js";

export async function startAssessmentSession(projectId) {
  if (!projectId) {
    throw new Error("请先创建或选择项目空间");
  }
  return apiPost("/api/assessment/start", {
    project_id: projectId,
  });
}

export async function submitAssessmentAnswer({ projectId, question, answer }) {
  if (!projectId) {
    throw new Error("请先创建或选择项目空间");
  }
  if (!question) {
    throw new Error("请先开始评估");
  }
  const cleanAnswer = String(answer || "").trim();
  if (!cleanAnswer) {
    throw new Error("请输入评估回答");
  }
  return apiPost("/api/assessment/answer", {
    project_id: projectId,
    question,
    answer: cleanAnswer,
  });
}

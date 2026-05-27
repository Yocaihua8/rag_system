import { apiPost } from "./client.js";

export async function askQuestion({ projectId, question, toolRunId = "" }) {
  const trimmedQuestion = (question || "").trim();
  if (!projectId) {
    throw new Error("请先创建或选择项目空间");
  }
  if (!trimmedQuestion) {
    throw new Error("请输入问题");
  }
  const payload = {
    project_id: projectId,
    question: trimmedQuestion,
  };
  if (toolRunId) {
    payload.tool_run_id = toolRunId;
  }
  return apiPost("/api/answer", payload);
}

export async function submitAnswerFeedback({ projectId, messageId, rating, note = "" }) {
  if (!projectId) {
    throw new Error("请先创建或选择项目空间");
  }
  if (!messageId) {
    throw new Error("请先完成一次提问");
  }
  if (!rating) {
    throw new Error("请选择反馈类型");
  }
  return apiPost("/api/answer/feedback", {
    project_id: projectId,
    message_id: messageId,
    rating,
    note,
  });
}

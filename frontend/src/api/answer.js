import { apiPost } from "./client.js";

export async function askQuestion({ projectId, question }) {
  const trimmedQuestion = (question || "").trim();
  if (!projectId) {
    throw new Error("请先创建或选择项目空间");
  }
  if (!trimmedQuestion) {
    throw new Error("请输入问题");
  }
  return apiPost("/api/answer", {
    project_id: projectId,
    question: trimmedQuestion,
  });
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

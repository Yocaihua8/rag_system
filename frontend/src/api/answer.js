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

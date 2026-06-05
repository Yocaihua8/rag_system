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

export function streamQuestion({ projectId, question, sessionId = "", toolRunId = "", onToken, onDone, onError }) {
  const trimmedQuestion = (question || "").trim();
  if (!projectId) {
    throw new Error("请先创建或选择项目空间");
  }
  if (!trimmedQuestion) {
    throw new Error("请输入问题");
  }
  const params = new URLSearchParams();
  params.set("project_id", projectId);
  params.set("question", trimmedQuestion);
  if (sessionId) {
    params.set("session_id", sessionId);
  }
  if (toolRunId) {
    params.set("tool_run_id", toolRunId);
  }
  const source = new EventSource(`/api/answer/stream?${params.toString()}`);
  source.addEventListener("token", (event) => {
    const data = parseStreamEvent(event);
    onToken?.(data.text || "");
  });
  source.addEventListener("done", (event) => {
    const data = parseStreamEvent(event);
    source.close();
    onDone?.(data);
  });
  source.addEventListener("answer_error", (event) => {
    const data = parseStreamEvent(event);
    source.close();
    onError?.(new Error(data.error || "回答生成失败"));
  });
  source.onerror = () => {
    source.close();
    onError?.(new Error("流式回答连接失败"));
  };
  return source;
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

function parseStreamEvent(event) {
  try {
    return JSON.parse(event.data);
  } catch (error) {
    return {};
  }
}

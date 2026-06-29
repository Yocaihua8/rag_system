import { apiGet, apiPost } from "./client.js";

export async function askQuestion({ projectId, question, toolRunId = "", parentMessageId = "" }) {
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
  if (parentMessageId) {
    payload.parent_message_id = parentMessageId;
  }
  return apiPost("/api/answer", payload);
}

export function askQuestionStream({
  projectId,
  question,
  sessionId = "",
  toolRunId = "",
  parentMessageId = "",
  handlers = {},
}) {
  const trimmedQuestion = (question || "").trim();
  if (!projectId) {
    throw new Error("请先创建或选择项目空间");
  }
  if (!trimmedQuestion) {
    throw new Error("请输入问题");
  }

  const params = new URLSearchParams({
    project_id: projectId,
    question: trimmedQuestion,
  });
  if (sessionId) {
    params.set("session_id", sessionId);
  }
  if (toolRunId) {
    params.set("tool_run_id", toolRunId);
  }
  if (parentMessageId) {
    params.set("parent_message_id", parentMessageId);
  }

  const source = new EventSource(`/api/answer/stream?${params.toString()}`);
  let settled = false;
  let answer = "";
  let rejectPromise = () => {};
  const promise = new Promise((resolve, reject) => {
    rejectPromise = reject;
    source.addEventListener("token", (event) => {
      const data = parseStreamPayload(event);
      const text = String(data.text || "");
      answer += text;
      handlers.onToken?.(answer, text);
    });
    source.addEventListener("done", (event) => {
      if (settled) {
        return;
      }
      settled = true;
      source.close();
      resolve(parseStreamPayload(event));
    });
    source.addEventListener("answer_error", (event) => {
      if (settled) {
        return;
      }
      settled = true;
      source.close();
      const data = parseStreamPayload(event);
      reject(new Error(data.error || "流式问答失败"));
    });
    source.onerror = () => {
      if (settled) {
        return;
      }
      settled = true;
      source.close();
      reject(new Error("本地服务暂时不可用。请确认应用已启动后刷新页面。"));
    };
  });

  return {
    promise,
    abort() {
      if (settled) {
        return;
      }
      settled = true;
      source.close();
      const error = new DOMException("已取消本次提问", "AbortError");
      rejectPromise(error);
    },
  };
}

export async function compareAnswers({
  projectId,
  question,
  profileIds = [],
  toolRunId = "",
  parentMessageId = "",
}) {
  const trimmedQuestion = (question || "").trim();
  if (!projectId) {
    throw new Error("请先创建或选择项目空间");
  }
  if (!trimmedQuestion) {
    throw new Error("请输入问题");
  }
  if (!Array.isArray(profileIds) || profileIds.length !== 2 || new Set(profileIds).size !== 2) {
    throw new Error("请选择 2 个模型 Profile");
  }
  const payload = {
    project_id: projectId,
    question: trimmedQuestion,
    profile_ids: profileIds,
    tool_run_id: toolRunId,
    parent_message_id: parentMessageId,
  };
  return apiPost("/api/answer/compare", payload);
}

function parseStreamPayload(event) {
  try {
    return JSON.parse(event.data || "{}");
  } catch (error) {
    throw new Error("服务返回格式异常。请刷新页面后重试。");
  }
}

export async function listChatSessions(projectId) {
  if (!projectId) {
    return { sessions: [] };
  }
  return apiGet(`/api/chat/sessions?project_id=${encodeURIComponent(projectId)}`);
}

export async function createChatSession({ projectId, title = "" }) {
  if (!projectId) {
    throw new Error("请先创建或选择项目空间");
  }
  return apiPost("/api/chat/sessions", {
    project_id: projectId,
    title,
  });
}

export async function renameChatSession({ sessionId, title }) {
  if (!sessionId) {
    throw new Error("请选择会话");
  }
  if (!String(title || "").trim()) {
    throw new Error("请输入会话标题");
  }
  return apiPost("/api/chat/sessions/rename", {
    session_id: sessionId,
    title,
  });
}

export async function deleteChatSession(sessionId) {
  if (!sessionId) {
    throw new Error("请选择会话");
  }
  return apiPost("/api/chat/sessions/delete", {
    session_id: sessionId,
  });
}

export async function listChatMessages({ projectId, sessionId = "" }) {
  if (!projectId) {
    return { messages: [] };
  }
  const params = new URLSearchParams({ project_id: projectId });
  if (sessionId) {
    params.set("session_id", sessionId);
  }
  return apiGet(`/api/chat/messages?${params.toString()}`);
}

export async function deleteChatMessage(messageId) {
  if (!messageId) {
    throw new Error("请选择聊天记录");
  }
  return apiPost("/api/chat/messages/delete", { message_id: messageId });
}

export async function clearChatMessages(projectId) {
  if (!projectId) {
    throw new Error("请先创建或选择项目空间");
  }
  return apiPost("/api/chat/messages/clear", { project_id: projectId });
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

import { apiGet, apiPost } from "./client.js";

export async function listChatSessions(projectId) {
  if (!projectId) {
    return [];
  }
  const data = await apiGet(`/api/chat/sessions?project_id=${encodeURIComponent(projectId)}`);
  return data.sessions || [];
}

export async function createChatSession({ projectId, title = "" }) {
  if (!projectId) {
    throw new Error("请先创建或选择项目空间");
  }
  const payload = {
    project_id: projectId,
    title: title.trim(),
  };
  const data = await apiPost("/api/chat/sessions", payload);
  return data.session || null;
}

export async function renameChatSession({ sessionId, title }) {
  if (!sessionId) {
    throw new Error("请选择聊天会话");
  }
  const cleanTitle = (title || "").trim();
  if (!cleanTitle) {
    throw new Error("请输入会话标题");
  }
  const data = await apiPost("/api/chat/sessions/rename", {
    session_id: sessionId,
    title: cleanTitle,
  });
  return data.session || null;
}

export async function deleteChatSession(sessionId) {
  if (!sessionId) {
    throw new Error("请选择聊天会话");
  }
  return apiPost("/api/chat/sessions/delete", { session_id: sessionId });
}

export async function listChatMessages({ projectId, sessionId = "" }) {
  if (!projectId) {
    return [];
  }
  const params = new URLSearchParams({ project_id: projectId });
  if (sessionId) {
    params.set("session_id", sessionId);
  }
  const data = await apiGet(`/api/chat/messages?${params.toString()}`);
  return data.messages || [];
}

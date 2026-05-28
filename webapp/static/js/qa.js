import { apiGet, apiPost } from "./api.js";
import { state } from "./state.js";

export async function ask(question, options = {}) {
  if (!state.selectedProjectId) {
    throw new Error("请先创建或选择项目空间");
  }
  const payload = {
    project_id: state.selectedProjectId,
    question,
  };
  if (state.selectedChatSessionId) {
    payload.session_id = state.selectedChatSessionId;
  }
  if (state.currentToolContextRunId) {
    payload.tool_run_id = state.currentToolContextRunId;
  }
  return apiPost("/api/answer", payload, options);
}

export function askStream(question, handlers = {}) {
  if (!state.selectedProjectId) {
    throw new Error("请先创建或选择项目空间");
  }
  const params = new URLSearchParams({
    project_id: state.selectedProjectId,
    question,
  });
  if (state.selectedChatSessionId) {
    params.set("session_id", state.selectedChatSessionId);
  }
  if (state.currentToolContextRunId) {
    params.set("tool_run_id", state.currentToolContextRunId);
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

function parseStreamPayload(event) {
  try {
    return JSON.parse(event.data || "{}");
  } catch (error) {
    throw new Error("服务返回格式异常。请刷新页面后重试。");
  }
}

export async function listChatMessages() {
  if (!state.selectedProjectId) {
    return { messages: [] };
  }
  const params = new URLSearchParams({ project_id: state.selectedProjectId });
  if (state.selectedChatSessionId) {
    params.set("session_id", state.selectedChatSessionId);
  }
  return apiGet(`/api/chat/messages?${params.toString()}`);
}

export async function listChatSessions() {
  if (!state.selectedProjectId) {
    return { sessions: [] };
  }
  return apiGet(`/api/chat/sessions?project_id=${encodeURIComponent(state.selectedProjectId)}`);
}

export async function createChatSession(title = "") {
  if (!state.selectedProjectId) {
    throw new Error("请先创建或选择项目空间");
  }
  return apiPost("/api/chat/sessions", {
    project_id: state.selectedProjectId,
    title,
  });
}

export async function renameChatSession(sessionId, title) {
  return apiPost("/api/chat/sessions/rename", {
    session_id: sessionId,
    title,
  });
}

export async function deleteChatSession(sessionId) {
  return apiPost("/api/chat/sessions/delete", {
    session_id: sessionId,
  });
}

export async function deleteChatMessage(messageId) {
  return apiPost("/api/chat/messages/delete", { message_id: messageId });
}

export async function clearChatMessages() {
  if (!state.selectedProjectId) {
    throw new Error("请先创建或选择项目空间");
  }
  return apiPost("/api/chat/messages/clear", { project_id: state.selectedProjectId });
}

export async function submitAnswerFeedback(messageId, rating, note = "") {
  if (!state.selectedProjectId) {
    throw new Error("请先创建或选择项目空间");
  }
  if (!messageId) {
    throw new Error("请先完成一次提问");
  }
  return apiPost("/api/answer/feedback", {
    project_id: state.selectedProjectId,
    message_id: messageId,
    rating,
    note,
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

export async function searchDebug(query, parameters = {}) {
  if (!state.selectedProjectId) {
    throw new Error("请先创建或选择项目空间");
  }
  return apiPost("/api/search/debug", {
    project_id: state.selectedProjectId,
    query,
    top_k: parameters.top_k,
    min_score: parameters.min_score,
    use_keyword: parameters.use_keyword,
    use_vector: parameters.use_vector,
  });
}

export async function getRetrievalSettings() {
  if (!state.selectedProjectId) {
    return { settings: null };
  }
  return apiGet(`/api/projects/retrieval-settings?project_id=${encodeURIComponent(state.selectedProjectId)}`);
}

export async function saveRetrievalSettings(settings) {
  if (!state.selectedProjectId) {
    throw new Error("请先创建或选择项目空间");
  }
  return apiPost("/api/projects/retrieval-settings", {
    project_id: state.selectedProjectId,
    top_k: settings.top_k,
    min_score: settings.min_score,
    use_keyword: settings.use_keyword,
    use_vector: settings.use_vector,
  });
}

export async function saveRetrievalReview(query, note, parameters = {}) {
  if (!state.selectedProjectId) {
    throw new Error("请先创建或选择项目空间");
  }
  return apiPost("/api/retrieval/reviews", {
    project_id: state.selectedProjectId,
    query,
    note,
    top_k: parameters.top_k,
    min_score: parameters.min_score,
    use_keyword: parameters.use_keyword,
    use_vector: parameters.use_vector,
  });
}

export async function listRetrievalReviews() {
  if (!state.selectedProjectId) {
    return { reviews: [] };
  }
  return apiGet(`/api/retrieval/reviews?project_id=${encodeURIComponent(state.selectedProjectId)}`);
}

export async function getRetrievalReviewDetail(reviewId) {
  return apiGet(`/api/retrieval/reviews/detail?review_id=${encodeURIComponent(reviewId)}`);
}

export async function deleteRetrievalReview(reviewId) {
  return apiPost("/api/retrieval/reviews/delete", {
    review_id: reviewId,
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

import { apiGet, apiPost } from "./client.js";

const PROJECT_REQUIRED_MESSAGE = "请先创建或选择项目空间";

function requiredProjectId(projectId) {
  const cleanProjectId = String(projectId || "").trim();
  if (!cleanProjectId) {
    throw new Error(PROJECT_REQUIRED_MESSAGE);
  }
  return cleanProjectId;
}

function requiredText(value, message) {
  const cleanValue = String(value || "").trim();
  if (!cleanValue) {
    throw new Error(message);
  }
  return cleanValue;
}

function requiredVersion(value) {
  const version = Number(value);
  if (!Number.isInteger(version) || version < 1) {
    throw new Error("学习会话版本无效，请刷新后重试");
  }
  return version;
}

function projectQuery(projectId) {
  return new URLSearchParams({
    project_id: requiredProjectId(projectId),
  }).toString();
}

export async function analyzeCoachProject(projectId) {
  const data = await apiPost("/api/coach/analyze", {
    project_id: requiredProjectId(projectId),
  });
  return data.analysis || null;
}

export async function getCoachOverview(projectId) {
  const data = await apiGet(`/api/coach/overview?${projectQuery(projectId)}`);
  return data.overview || null;
}

export async function getCoachKnowledgePoints(projectId) {
  const data = await apiGet(`/api/coach/knowledge-points?${projectQuery(projectId)}`);
  return data.knowledge_points || null;
}

export async function getCoachSkills(projectId) {
  const data = await apiGet(`/api/coach/skills?${projectQuery(projectId)}`);
  return data.skills || null;
}

export async function getCoachCoverage(projectId) {
  const data = await apiGet(`/api/coach/coverage?${projectQuery(projectId)}`);
  return data.coverage || null;
}

export async function startCoachAssessment({
  projectId,
  targetType = "",
  targetId = "",
  sessionId = "",
  restart = false,
}) {
  const payload = {
    project_id: requiredProjectId(projectId),
    restart: Boolean(restart),
  };
  const cleanTargetType = String(targetType || "").trim();
  const cleanTargetId = String(targetId || "").trim();
  const cleanSessionId = String(sessionId || "").trim();
  if (cleanTargetType) {
    payload.target_type = cleanTargetType;
  }
  if (cleanTargetId) {
    payload.target_id = cleanTargetId;
  }
  if (cleanSessionId) {
    payload.session_id = cleanSessionId;
  }
  const data = await apiPost("/api/coach/assessments/start", payload);
  return data.session || null;
}

export async function answerCoachAssessment({
  projectId,
  sessionId,
  questionId,
  answer,
  evaluationMode = "auto",
}) {
  return apiPost("/api/coach/assessments/answer", {
    project_id: requiredProjectId(projectId),
    session_id: requiredText(sessionId, "请先开始评估"),
    question_id: requiredText(questionId, "请选择评估问题"),
    answer: requiredText(answer, "请输入评估回答"),
    evaluation_mode: String(evaluationMode || "auto").trim() || "auto",
  });
}

export async function startCoachLearningSession({
  projectId,
  targetType = "",
  targetId = "",
  planId = "",
  planItemId = "",
  originType = "",
}) {
  const cleanTargetType = String(targetType || "").trim();
  const cleanTargetId = String(targetId || "").trim();
  const cleanPlanId = String(planId || "").trim();
  const cleanPlanItemId = String(planItemId || "").trim();
  const hasTarget = Boolean(cleanTargetType || cleanTargetId);
  const hasPlanItem = Boolean(cleanPlanId || cleanPlanItemId);
  if (hasTarget === hasPlanItem) {
    throw new Error("请选择学习目标");
  }
  const payload = {
    project_id: requiredProjectId(projectId),
  };
  if (hasTarget) {
    payload.target_type = requiredText(cleanTargetType, "请选择学习目标类型");
    payload.target_id = requiredText(cleanTargetId, "请选择学习目标");
    const cleanOriginType = String(originType || "").trim();
    if (cleanOriginType) {
      payload.origin_type = cleanOriginType;
    }
  } else {
    payload.plan_id = requiredText(cleanPlanId, "请选择已确认的学习计划");
    payload.plan_item_id = requiredText(cleanPlanItemId, "请选择学习计划任务");
  }
  const data = await apiPost("/api/coach/learning-sessions/start", payload);
  return data.session || null;
}

export async function getCurrentCoachLearningSession({
  projectId,
  sessionId = "",
} = {}) {
  const query = new URLSearchParams({
    project_id: requiredProjectId(projectId),
  });
  const cleanSessionId = String(sessionId || "").trim();
  if (cleanSessionId) {
    query.set("session_id", cleanSessionId);
  }
  const data = await apiGet(`/api/coach/learning-sessions/current?${query.toString()}`);
  return data.session || null;
}

export async function transitionCoachLearningSession({
  projectId,
  sessionId,
  expectedVersion,
  action,
}) {
  const data = await apiPost("/api/coach/learning-sessions/transition", {
    project_id: requiredProjectId(projectId),
    session_id: requiredText(sessionId, "请先开始学习会话"),
    expected_version: requiredVersion(expectedVersion),
    action: requiredText(action, "请选择学习操作"),
  });
  return data.session || null;
}

export async function submitCoachLearningAttempt({
  projectId,
  sessionId,
  exerciseId,
  answer,
  expectedVersion,
  idempotencyKey,
}) {
  const rawAnswer = String(answer ?? "");
  if (!rawAnswer.trim()) {
    throw new Error("请输入本题答案");
  }
  return apiPost("/api/coach/learning-sessions/attempts", {
    project_id: requiredProjectId(projectId),
    session_id: requiredText(sessionId, "请先开始学习会话"),
    exercise_id: requiredText(exerciseId, "当前练习不可用，请刷新后重试"),
    answer: rawAnswer,
    expected_version: requiredVersion(expectedVersion),
    idempotency_key: requiredText(idempotencyKey, "作答请求标识无效，请重试"),
  });
}

export async function generateLearningPlan({ projectId, maxItems } = {}) {
  const payload = {
    project_id: requiredProjectId(projectId),
  };
  if (maxItems !== undefined && maxItems !== null && maxItems !== "") {
    payload.max_items = Number(maxItems);
  }
  return apiPost("/api/coach/learning-plans/generate", payload);
}

export async function getCurrentLearningPlan(projectId) {
  const data = await apiGet(`/api/coach/learning-plans/current?${projectQuery(projectId)}`);
  return data.current || null;
}

export async function updateLearningPlan({
  projectId,
  planId,
  items,
  itemStatuses,
  expectedRevision,
  expectedItemsHash,
  expectedProgressHash,
}) {
  const hasItems = items !== undefined;
  const hasItemStatuses = itemStatuses !== undefined;
  if (hasItems === hasItemStatuses) {
    throw new Error("请选择编辑计划内容或更新任务进度");
  }
  const payload = {
    project_id: requiredProjectId(projectId),
    plan_id: requiredText(planId, "请选择学习计划"),
  };
  if (hasItems) {
    payload.items = items;
  }
  if (hasItemStatuses) {
    payload.item_statuses = itemStatuses;
  }
  if (expectedRevision !== undefined && expectedRevision !== null) {
    payload.expected_revision = expectedRevision;
  }
  if (expectedItemsHash !== undefined) {
    payload.expected_items_hash = String(expectedItemsHash || "").trim();
  }
  if (expectedProgressHash !== undefined) {
    payload.expected_progress_hash = String(expectedProgressHash || "").trim();
  }
  return apiPost("/api/coach/learning-plans/update", payload);
}

export async function confirmLearningPlan({
  projectId,
  planId,
  expectedRevision,
  expectedItemsHash,
}) {
  const payload = {
    project_id: requiredProjectId(projectId),
    plan_id: requiredText(planId, "请选择学习计划"),
  };
  if (expectedRevision !== undefined && expectedRevision !== null) {
    payload.expected_revision = expectedRevision;
  }
  if (expectedItemsHash !== undefined) {
    payload.expected_items_hash = String(expectedItemsHash || "").trim();
  }
  return apiPost("/api/coach/learning-plans/confirm", payload);
}

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

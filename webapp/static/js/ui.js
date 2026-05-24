export function setStatus(message) {
  document.querySelector("#status").textContent = message;
}

export function setErrorStatus(error) {
  setStatus(formatRecoverableError(error));
}

export function setInlineErrorStatus(statusEl, error) {
  statusEl.textContent = formatRecoverableError(error);
}

export function formatRecoverableError(error) {
  const message = error?.message || String(error || "操作失败");
  const normalized = message.toLowerCase();
  if (
    message.includes("目录不存在")
    || normalized.includes("path must be an existing directory")
    || normalized.includes("root path does not exist")
  ) {
    return `${message} 当前项目目录不可访问。请改用“选择本机文件夹导入”，或在设置页重新创建可访问的项目空间。Docker 模式可填写 /workspace。`;
  }
  if (message.includes("请选择一个本地项目文件夹")) {
    return `${message} 请点击“选择本机文件夹导入”，并在浏览器弹窗中选择项目目录。`;
  }
  if (message.includes("未找到可导入的文本文件")) {
    return `${message} 请选择包含 Markdown、TXT、代码、配置、DOCX 或 PDF 文件的文件夹。`;
  }
  if (message.includes("请先创建或选择项目空间") || message.includes("请先选择项目空间")) {
    return `${message} 请先到设置页创建项目空间，或在资料库选择已有项目空间。`;
  }
  if (message.includes("请先开始评估")) {
    return `${message} 请点击“开始评估”生成题目后再提交回答。`;
  }
  if (
    message.includes("API Key")
    && (message.includes("未配置") || message.includes("missing") || message.includes("required"))
  ) {
    return `${message} 模型 API Key 未配置。请在设置页填写 API Key，或配置 RAG_LLM_API_KEY / DEEPSEEK_API_KEY。`;
  }
  if (
    message.includes("401")
    || message.includes("403")
    || message.includes("unauthorized")
    || message.includes("forbidden")
    || message.includes("鉴权")
  ) {
    return `${message} 模型服务鉴权失败。请确认 API Key 是否有效，且账号有当前模型权限。`;
  }
  if (
    message.includes("模型")
    || message.includes("LLM")
    || message.includes("Chat Completions")
    || message.includes("connection")
    || message.includes("timeout")
  ) {
    return `${message} 模型服务连接失败。请检查 API 地址、模型名称和本地网络后重试。`;
  }
  return `${message} 请检查项目空间、资料或网络后重试。`;
}

export function renderAnswer(answerEl, sourcesEl, data) {
  const modeLabel = data.mode === "api"
    ? `\n\n[真实模型：${data.provider}]`
    : data.mode === "fallback"
      ? `\n\n[模型不可用，已回退本地回答：${data.warning}]`
      : "\n\n[本地片段回答]";
  const suggestionLabel = formatToolSuggestion(data.tool_suggestion);
  const qualityLabel = formatSourceQuality(data.source_quality);
  const observabilityLabel = formatAnswerObservability(data.observability);
  answerEl.textContent = `${data.answer}${modeLabel}${qualityLabel}${observabilityLabel}${suggestionLabel}`;
  sourcesEl.innerHTML = "";
  if (data.sources.length === 0) {
    appendEmptyItem(sourcesEl, "暂无来源。请先在资料库导入文件，或换一个更贴近资料内容的问题。");
    return;
  }
  for (const source of data.sources) {
    const item = document.createElement("li");
    item.textContent = `${source.path}：${source.snippet}`;
    sourcesEl.appendChild(item);
  }
}

export function renderAnswerFeedback(feedbackEl, messageId, statusText = "") {
  feedbackEl.hidden = !messageId;
  const statusEl = feedbackEl.querySelector("#answer-feedback-status");
  if (statusEl) {
    statusEl.textContent = statusText;
  }
  for (const button of feedbackEl.querySelectorAll("[data-feedback-rating]")) {
    button.disabled = !messageId;
  }
}

export function renderSearchDebug(debugEl, data) {
  if (!data) {
    debugEl.textContent = "暂无检索诊断";
    return;
  }
  const hits = Array.isArray(data.hits) ? data.hits : [];
  const debug = data.debug || {};
  const quality = debug.quality || {};
  const parameters = debug.parameters || {};
  debugEl.textContent = [
    `查询：${debug.query || ""}`,
    `来源质量：${quality.label || "未知"}（${quality.level || "unknown"}）`,
    `原因：${quality.reason || ""}`,
    `文档/分块：${debug.document_count ?? 0} / ${debug.chunk_count ?? 0}`,
    `向量可用：${debug.vector_available ? "是" : "否"}`,
    `参数：top_k=${parameters.top_k ?? ""} min_score=${parameters.min_score ?? ""} keyword=${parameters.use_keyword ? "on" : "off"} vector=${parameters.use_vector ? "on" : "off"}`,
    ...hits.map((hit, index) => [
      `${index + 1}. ${hit.path}`,
      `score=${formatScore(hit.score)} keyword=${formatScore(hit.keyword_score)} vector=${formatScore(hit.vector_score)} retrieval=${hit.retrieval}`,
      `chunk=${hit.chunk_index ?? "n/a"} provider=${hit.vector_provider || "local"} model=${hit.vector_model || "hashing-96"}`,
      hit.snippet,
    ].join("\n")),
  ].join("\n\n");
}

export function renderRetrievalReviews(reviewsEl, reviews, onShowDetail = null, onDelete = null) {
  reviewsEl.innerHTML = "";
  if (reviews.length === 0) {
    appendEmptyItem(reviewsEl, "暂无检索复盘");
    return;
  }
  for (const review of reviews) {
    const item = document.createElement("li");
    const summary = document.createElement("span");
    const quality = review.source_quality || {};
    const parameters = review.parameters || {};
    summary.textContent = [
      `${review.query} / ${quality.label || "来源质量未知"} / 命中 ${review.hit_count ?? 0}`,
      `top_k=${parameters.top_k ?? ""} min_score=${parameters.min_score ?? ""}`,
      review.note ? `备注：${review.note}` : "备注：无",
    ].join("\n");
    item.appendChild(summary);
    if (onShowDetail) {
      const detailButton = document.createElement("button");
      detailButton.type = "button";
      detailButton.textContent = "查看详情";
      detailButton.addEventListener("click", () => onShowDetail(review.id));
      item.appendChild(detailButton);
    }
    if (onDelete) {
      const deleteButton = document.createElement("button");
      deleteButton.type = "button";
      deleteButton.textContent = "删除";
      deleteButton.addEventListener("click", () => onDelete(review.id));
      item.appendChild(deleteButton);
    }
    reviewsEl.appendChild(item);
  }
}

export function renderRetrievalReviewDetail(detailEl, review) {
  if (!review) {
    detailEl.textContent = "请选择一条检索复盘查看详情";
    return;
  }
  const parameters = review.parameters || {};
  const quality = review.source_quality || {};
  const hits = Array.isArray(review.hits) ? review.hits : [];
  detailEl.textContent = [
    `查询：${review.query || ""}`,
    `时间：${review.created_at || ""}`,
    `来源质量：${quality.label || quality.level || "未知"}`,
    `原因：${quality.reason || ""}`,
    `参数：top_k=${parameters.top_k ?? ""} min_score=${parameters.min_score ?? ""} keyword=${parameters.use_keyword ? "on" : "off"} vector=${parameters.use_vector ? "on" : "off"}`,
    `备注：${review.note || "无"}`,
    "命中来源：",
    ...hits.map((hit, index) => [
      `${index + 1}. ${hit.path || ""}`,
      `score=${formatScore(hit.score)} keyword=${formatScore(hit.keyword_score)} vector=${formatScore(hit.vector_score)} retrieval=${hit.retrieval || ""}`,
      hit.snippet || "",
    ].join("\n")),
  ].join("\n\n");
}

export function renderToolSuggestionAction(buttonEl, toolSuggestion) {
  buttonEl.hidden = !toolSuggestion;
  buttonEl.disabled = !toolSuggestion;
  buttonEl.textContent = toolSuggestion
    ? `运行建议工具：${toolSuggestion.tool || "search_sources"}`
    : "运行建议工具";
}

export function renderToolContextNotice(noticeEl, toolContext) {
  noticeEl.textContent = toolContext
    ? `使用工具来源：${toolContext.query || "search_sources"}${toolContext.tool_run_id ? `（运行 ID：${toolContext.tool_run_id}）` : ""}`
    : "";
}

export function renderUseToolResultAction(buttonEl, run) {
  const usable = Boolean(run && run.tool_name === "search_sources" && run.status === "success");
  buttonEl.hidden = !usable;
  buttonEl.disabled = !usable;
  buttonEl.textContent = usable
    ? `使用工具结果作为下一问上下文（运行 ID：${run.id}）`
    : "使用工具结果作为下一问上下文";
}

function formatToolSuggestion(toolSuggestion) {
  if (!toolSuggestion) {
    return "";
  }
  const toolName = toolSuggestion.tool || "search_sources";
  const query = toolSuggestion.arguments?.query || "";
  const reason = toolSuggestion.reason || "当前来源不足，可先扩大来源检索。";
  return `\n\n[建议工具：${toolName}]\n${reason}\n查询：${query}`;
}

function formatSourceQuality(sourceQuality) {
  if (!sourceQuality) {
    return "";
  }
  return `\n\n[来源质量：${sourceQuality.label || "未知"}]\n${sourceQuality.reason || ""}`;
}

function formatAnswerObservability(observability) {
  if (!observability) {
    return "";
  }
  const retrieval = observability.retrieval || {};
  const model = observability.model || {};
  return [
    "\n\n[问答观测]",
    `检索：top_k=${retrieval.top_k ?? ""} min_score=${retrieval.min_score ?? ""} keyword=${retrieval.use_keyword ? "on" : "off"} vector=${retrieval.use_vector ? "on" : "off"}`,
    `命中来源：${retrieval.hit_count ?? 0}`,
    `模型：${model.mode || "unknown"} / ${model.provider || "unknown"}`,
    `耗时：${observability.elapsed_ms ?? 0}ms`,
  ].join("\n");
}

function formatScore(score) {
  const value = Number(score);
  return Number.isFinite(value) ? value.toFixed(3) : "0.000";
}

function formatToolParameters(tool) {
  const parameters = tool.parameters_schema || tool.parameters || tool.arguments || tool.input_schema || tool.schema || {};
  if (typeof parameters === "string") {
    return parameters || "无";
  }
  if (parameters.properties && typeof parameters.properties === "object") {
    const required = Array.isArray(parameters.required) ? parameters.required : [];
    const schemaEntries = Object.entries(parameters.properties);
    if (schemaEntries.length === 0) {
      return "无参数";
    }
    return schemaEntries
      .map(([name, value]) => `${name}: ${formatParameterValue(value)}${required.includes(name) ? "，必填" : ""}`)
      .join("；");
  }
  const entries = Object.entries(parameters);
  if (entries.length === 0) {
    return "无";
  }
  return entries.map(([name, value]) => `${name}: ${formatParameterValue(value)}`).join("，");
}

function formatParameterValue(value) {
  if (typeof value === "string") {
    return value;
  }
  if (value && typeof value === "object") {
    return value.description || value.type || JSON.stringify(value);
  }
  return String(value);
}

function formatToolScenarios(tool) {
  const scenarios = tool.scenarios || tool.use_cases || tool.applicable_scenarios || tool.when_to_use;
  if (Array.isArray(scenarios)) {
    return scenarios.join("，") || "参考工具说明";
  }
  return scenarios || tool.description || "参考工具说明";
}

function formatJsonBlock(value) {
  return JSON.stringify(value, null, 2);
}

export function renderChatHistory(historyEl, messages, onDelete = null) {
  historyEl.innerHTML = "";
  if (messages.length === 0) {
    appendEmptyItem(historyEl, "暂无对话记录");
    return;
  }
  for (const message of messages) {
    const item = document.createElement("li");
    const question = document.createElement("p");
    const answer = document.createElement("p");
    const meta = document.createElement("span");
    question.className = "chat-question";
    answer.className = "chat-answer";
    meta.className = "chat-meta";
    question.textContent = `问：${message.question}`;
    answer.textContent = `答：${message.answer}`;
    meta.textContent = `${message.mode || "local"} / ${message.provider || "local"} / 来源 ${message.sources?.length || 0}`;
    item.appendChild(question);
    item.appendChild(answer);
    item.appendChild(meta);
    if (onDelete) {
      const deleteButton = document.createElement("button");
      deleteButton.type = "button";
      deleteButton.textContent = "删除";
      deleteButton.addEventListener("click", () => onDelete(message.id));
      item.appendChild(deleteButton);
    }
    historyEl.appendChild(item);
  }
}

export function renderChatSessions(selectEl, sessions, selectedSessionId = "") {
  selectEl.innerHTML = "";
  const defaultOption = document.createElement("option");
  defaultOption.value = "";
  defaultOption.textContent = "默认会话";
  selectEl.appendChild(defaultOption);
  for (const session of sessions) {
    const option = document.createElement("option");
    option.value = session.id;
    option.textContent = session.title || "未命名会话";
    selectEl.appendChild(option);
  }
  selectEl.value = selectedSessionId;
}

export function renderAgentToolResult(resultEl, data) {
  if (!data) {
    resultEl.textContent = "暂无工具结果";
    return;
  }
  const result = data.result || {};
  if (data.run?.tool_name === "search_sources") {
    const hits = Array.isArray(result.hits) ? result.hits : [];
    resultEl.textContent = [
      `工具：${data.run.tool_name}`,
      `运行 ID：${data.run.id}`,
      `状态：${data.run.status}`,
      `查询：${result.query || ""}`,
      `命中：${result.hit_count ?? hits.length}`,
      ...hits.map((hit, index) => `${index + 1}. ${hit.path}：${hit.snippet}`),
    ].join("\n");
    return;
  }
  resultEl.textContent = [
    `工具：${data.run?.tool_name || "project_overview"}`,
    `运行 ID：${data.run?.id || ""}`,
    `状态：${data.run?.status || "success"}`,
    `项目：${result.project_name || "未知"}`,
    `文档：${result.document_count ?? 0}`,
    `分块：${result.chunk_count ?? 0}`,
    `向量：${result.vector_count ?? 0}`,
    `对话：${result.chat_message_count ?? 0}`,
  ].join("\n");
}

export function renderAgentTools(toolsEl, tools, onRunTool = null) {
  toolsEl.innerHTML = "";
  if (tools.length === 0) {
    appendEmptyItem(toolsEl, "暂无可用只读工具");
    return;
  }
  for (const tool of tools) {
    const item = document.createElement("li");
    const title = document.createElement("strong");
    const description = document.createElement("p");
    const parameters = document.createElement("p");
    const scenario = document.createElement("p");
    title.textContent = tool.label || tool.title || tool.name || "未命名工具";
    description.textContent = tool.description || tool.name || "暂无工具说明";
    parameters.textContent = `参数：${formatToolParameters(tool)}`;
    scenario.textContent = `适用场景：${formatToolScenarios(tool)}`;
    item.appendChild(title);
    item.appendChild(description);
    item.appendChild(parameters);
    item.appendChild(scenario);
    if (onRunTool) {
      const runButton = document.createElement("button");
      runButton.type = "button";
      runButton.setAttribute("data-tool-name", tool.name || "");
      runButton.textContent = `${tool.label || tool.title || tool.name || "工具"}：运行`;
      runButton.addEventListener("click", () => onRunTool(tool.name));
      item.appendChild(runButton);
    }
    toolsEl.appendChild(item);
  }
}

export function renderAgentToolRuns(runsEl, runs, onShowDetail = null) {
  runsEl.innerHTML = "";
  if (runs.length === 0) {
    appendEmptyItem(runsEl, "暂无工具运行历史");
    return;
  }
  for (const run of runs) {
    const item = document.createElement("li");
    const summary = document.createElement("span");
    const query = run.arguments?.query ? ` / ${run.arguments.query}` : "";
    const error = run.error ? ` / ${run.error}` : "";
    summary.textContent = `${run.tool_name} / ${run.status}${query}${error}`;
    item.appendChild(summary);
    if (onShowDetail) {
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = "查看详情";
      button.addEventListener("click", () => onShowDetail(run.id));
      item.appendChild(button);
    }
    runsEl.appendChild(item);
  }
}

export function renderAgentToolRunDetail(detailEl, run) {
  if (!run) {
    detailEl.textContent = "请选择一条工具运行查看详情";
    return;
  }
  detailEl.textContent = [
    `工具：${run.tool_name || ""}`,
    `状态：${run.status || ""}`,
    `时间：${run.created_at || ""}`,
    `arguments：${formatJsonBlock(run.arguments || {})}`,
    `result：${formatJsonBlock(run.result || {})}`,
    `error：${run.error || "无"}`,
  ].join("\n");
}

export function renderSearchResults(resultsEl, hits, onSelect) {
  resultsEl.innerHTML = "";
  if (hits.length === 0) {
    appendEmptyItem(resultsEl, "暂无检索结果。请换一个关键词，或先到资料库导入文件。");
    return;
  }
  for (const hit of hits) {
    const item = document.createElement("li");
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = `${hit.path}｜${hit.snippet}`;
    button.addEventListener("click", () => onSelect(hit.document_id));
    item.appendChild(button);
    resultsEl.appendChild(item);
  }
}

export function renderSkippedDetails(detailsEl, details) {
  detailsEl.innerHTML = "";
  if (details.length === 0) {
    appendEmptyItem(detailsEl, "本次没有跳过文件。");
    return;
  }
  appendEmptyItem(detailsEl, "以下文件没有导入，通常是格式不支持、文件过大，或属于系统自动忽略的目录。");
  for (const detail of details) {
    const item = document.createElement("li");
    item.textContent = `未导入：${detail.path}：${detail.reason}`;
    detailsEl.appendChild(item);
  }
}

export function renderImportErrors(errorsEl, errors) {
  errorsEl.innerHTML = "";
  if (errors.length === 0) {
    appendEmptyItem(errorsEl, "没有读取失败的文件。");
    return;
  }
  for (const error of errors) {
    const item = document.createElement("li");
    item.textContent = `读取失败：${error}`;
    errorsEl.appendChild(item);
  }
}

export function renderDocuments(
  documentsEl,
  documents,
  onSelect,
  onDelete,
  emptyMessage = "暂无导入文件。点击“选择本机文件夹导入”开始。",
) {
  documentsEl.innerHTML = "";
  if (documents.length === 0) {
    appendEmptyItem(documentsEl, emptyMessage);
    return;
  }
  for (const entry of documents) {
    const item = document.createElement("li");
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = entry.relative_path;
    button.addEventListener("click", () => onSelect(entry.id));
    item.appendChild(button);
    const deleteButton = document.createElement("button");
    deleteButton.type = "button";
    deleteButton.textContent = "移除";
    deleteButton.addEventListener("click", () => onDelete(entry.id));
    item.appendChild(deleteButton);
    documentsEl.appendChild(item);
  }
}

export function renderDocumentCount(countEl, visibleCount, totalCount) {
  countEl.textContent = `${visibleCount} / ${totalCount} 个文件`;
}

export function renderProjectHealthSummary(metricsEl, retrievalHealthEl, summary) {
  metricsEl.innerHTML = "";
  retrievalHealthEl.innerHTML = "";
  if (!summary) {
    appendEmptyMetric(metricsEl, "暂无项目健康概览");
    appendEmptyItem(retrievalHealthEl, "请选择项目空间后查看检索健康。");
    return;
  }
  const metrics = [
    ["文档数", summary.document_count ?? 0],
    ["Chunk 数", summary.chunk_count ?? 0],
    ["向量数", summary.vector_count ?? 0],
    ["聊天数", summary.chat_message_count ?? 0],
    ["工具运行数", summary.agent_tool_run_count ?? 0],
    ["检索复盘数", summary.retrieval_review_count ?? 0],
    ["最近活动时间", summary.last_activity_at || "暂无"],
  ];
  for (const [label, value] of metrics) {
    const item = document.createElement("div");
    const term = document.createElement("dt");
    const description = document.createElement("dd");
    term.textContent = label;
    description.textContent = value;
    item.appendChild(term);
    item.appendChild(description);
    metricsEl.appendChild(item);
  }

  renderRetrievalHealthItem(retrievalHealthEl, summary.chunk_count > 0, "已生成 Chunk", "还没有 Chunk，请先导入资料。");
  renderRetrievalHealthItem(retrievalHealthEl, summary.vector_count > 0, "已有向量", "还没有向量，导入完成后再检查。");
  renderRetrievalHealthItem(
    retrievalHealthEl,
    summary.retrieval_review_count > 0,
    "已有检索复盘",
    "还没有检索复盘，可在工作台运行检索诊断后保存。",
  );
}

export function renderProjectHealthStatus(statusEl, summary) {
  statusEl.textContent = summary ? "已读取" : "等待项目";
}

export function renderProjectHealthError(statusEl) {
  statusEl.textContent = "健康概览读取失败";
}

export function renderProjectRoot(rootEl, project) {
  if (!project) {
    rootEl.textContent = "未选择项目空间";
    return;
  }
  rootEl.textContent = project.root_exists
    ? `目录：${project.root_path}`
    : `目录：${project.root_path}（目录不存在）`;
}

export function renderDocumentPreview(previewEl, document) {
  previewEl.textContent = document
    ? `${document.relative_path}\n\n${document.content}`
    : "请选择左侧文件查看内容";
}

export function renderAssessmentQuestion(questionEl, question) {
  if (!question) {
    questionEl.textContent = "请先在资料库导入文件，再开始评估。";
    return;
  }
  questionEl.textContent = `${question.prompt}\n\n来源：${question.source_path}\n参考片段：${question.reference_snippet}`;
}

export function renderAssessmentResult(resultEl, result) {
  if (!result) {
    resultEl.textContent = "";
    return;
  }
  resultEl.textContent = [
    `结果：${result.status}`,
    `得分：${result.score}`,
    `命中：${result.matched_points.join("、") || "无"}`,
    `待补充：${result.missing_points.join("、") || "无"}`,
    `建议阅读：${result.source_path}`,
    result.feedback,
  ].join("\n");
}

export function renderAssessmentOverview(overviewEl, result) {
  const radarPolygon = overviewEl.querySelector("#assessment-radar-polygon");
  const statusEl = overviewEl.querySelector("#assessment-overview-status");
  const scoreRingEl = overviewEl.querySelector("#assessment-score-ring");
  const scoreValueEl = overviewEl.querySelector("#assessment-score-value");
  const scoreTitleEl = overviewEl.querySelector("#assessment-score-title");
  const scoreSummaryEl = overviewEl.querySelector("#assessment-score-summary");
  const matchedListEl = overviewEl.querySelector("#assessment-matched-points");
  const missingListEl = overviewEl.querySelector("#assessment-missing-points");
  const sourcePathEl = overviewEl.querySelector("#assessment-source-path");

  if (!result) {
    overviewEl.classList.add("is-empty");
    radarPolygon.setAttribute("points", buildRadarPoints([0, 0, 0, 0, 0]));
    scoreRingEl.style.setProperty("--score-percent", "0%");
    statusEl.textContent = "等待评估";
    scoreValueEl.textContent = "0%";
    scoreTitleEl.textContent = "暂无结果";
    scoreSummaryEl.textContent = "提交回答后显示得分、命中点和待补充点。";
    renderPointTags(matchedListEl, [], "暂无命中要点");
    renderPointTags(missingListEl, [], "暂无待补充要点");
    sourcePathEl.textContent = "暂无";
    return;
  }

  const score = clampScore(Number(result.score));
  const scorePercent = Math.round(score * 100);
  const matchedPoints = Array.isArray(result.matched_points) ? result.matched_points : [];
  const missingPoints = Array.isArray(result.missing_points) ? result.missing_points : [];
  const totalPoints = Math.max(1, matchedPoints.length + missingPoints.length);
  const hitRatio = matchedPoints.length / totalPoints;
  const completionRatio = missingPoints.length === 0 ? 1 : Math.max(0.12, 1 - missingPoints.length / totalPoints);
  const expressionRatio = Math.min(1, 0.35 + score * 0.65);
  const sourceRatio = result.source_path ? Math.max(0.35, score) : 0.2;

  overviewEl.classList.remove("is-empty");
  radarPolygon.setAttribute("points", buildRadarPoints([
    score,
    hitRatio,
    expressionRatio,
    sourceRatio,
    completionRatio,
  ]));
  scoreRingEl.style.setProperty("--score-percent", `${scorePercent}%`);
  statusEl.textContent = result.status;
  scoreValueEl.textContent = `${scorePercent}%`;
  scoreTitleEl.textContent = result.status;
  scoreSummaryEl.textContent = `命中 ${matchedPoints.length} / ${totalPoints} 个参考要点`;
  renderPointTags(matchedListEl, matchedPoints, "暂无命中要点");
  renderPointTags(missingListEl, missingPoints, "暂无待补充要点");
  sourcePathEl.textContent = result.source_path || "暂无";
}

function buildRadarPoints(values) {
  const centerX = 120;
  const centerY = 105;
  const radius = 83;
  return values
    .map((value, index) => {
      const angle = -Math.PI / 2 + index * (Math.PI * 2 / values.length);
      const pointRadius = radius * clampScore(value);
      const x = centerX + Math.cos(angle) * pointRadius;
      const y = centerY + Math.sin(angle) * pointRadius;
      return `${Math.round(x)},${Math.round(y)}`;
    })
    .join(" ");
}

function renderPointTags(listEl, points, emptyMessage) {
  listEl.innerHTML = "";
  if (points.length === 0) {
    appendEmptyItem(listEl, emptyMessage);
    return;
  }
  for (const point of points) {
    const item = document.createElement("li");
    item.textContent = point;
    listEl.appendChild(item);
  }
}

function clampScore(value) {
  if (!Number.isFinite(value)) {
    return 0;
  }
  return Math.max(0, Math.min(1, value));
}

function appendEmptyItem(listEl, message) {
  const item = document.createElement("li");
  item.textContent = message;
  listEl.appendChild(item);
}

function appendEmptyMetric(metricsEl, message) {
  const item = document.createElement("div");
  const term = document.createElement("dt");
  const description = document.createElement("dd");
  term.textContent = "状态";
  description.textContent = message;
  item.appendChild(term);
  item.appendChild(description);
  metricsEl.appendChild(item);
}

function renderRetrievalHealthItem(listEl, ok, okText, missingText) {
  const item = document.createElement("li");
  item.className = ok ? "is-ok" : "is-missing";
  item.textContent = ok ? okText : missingText;
  listEl.appendChild(item);
}

export function setStatus(message) {
  document.querySelector("#status").textContent = message;
}

export function renderAnswer(answerEl, sourcesEl, data) {
  const modeLabel = data.mode === "api"
    ? `\n\n[真实模型：${data.provider}]`
    : data.mode === "fallback"
      ? `\n\n[模型不可用，已回退本地回答：${data.warning}]`
      : "\n\n[本地片段回答]";
  answerEl.textContent = `${data.answer}${modeLabel}`;
  sourcesEl.innerHTML = "";
  if (data.sources.length === 0) {
    appendEmptyItem(sourcesEl, "暂无来源");
    return;
  }
  for (const source of data.sources) {
    const item = document.createElement("li");
    item.textContent = `${source.path}：${source.snippet}`;
    sourcesEl.appendChild(item);
  }
}

export function renderChatHistory(historyEl, messages) {
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
    historyEl.appendChild(item);
  }
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
      `状态：${data.run.status}`,
      `查询：${result.query || ""}`,
      `命中：${result.hit_count ?? hits.length}`,
      ...hits.map((hit, index) => `${index + 1}. ${hit.path}：${hit.snippet}`),
    ].join("\n");
    return;
  }
  resultEl.textContent = [
    `工具：${data.run?.tool_name || "project_overview"}`,
    `状态：${data.run?.status || "success"}`,
    `项目：${result.project_name || "未知"}`,
    `文档：${result.document_count ?? 0}`,
    `分块：${result.chunk_count ?? 0}`,
    `向量：${result.vector_count ?? 0}`,
    `对话：${result.chat_message_count ?? 0}`,
  ].join("\n");
}

export function renderSearchResults(resultsEl, hits, onSelect) {
  resultsEl.innerHTML = "";
  if (hits.length === 0) {
    appendEmptyItem(resultsEl, "暂无检索结果");
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
    appendEmptyItem(detailsEl, "暂无跳过文件");
    return;
  }
  for (const detail of details) {
    const item = document.createElement("li");
    item.textContent = `${detail.path}：${detail.reason}`;
    detailsEl.appendChild(item);
  }
}

export function renderImportErrors(errorsEl, errors) {
  errorsEl.innerHTML = "";
  if (errors.length === 0) {
    appendEmptyItem(errorsEl, "暂无导入错误");
    return;
  }
  for (const error of errors) {
    const item = document.createElement("li");
    item.textContent = error;
    errorsEl.appendChild(item);
  }
}

export function renderDocuments(documentsEl, documents, onSelect, onDelete, emptyMessage = "暂无导入文件") {
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
    questionEl.textContent = "请先导入文件，再开始评估。";
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

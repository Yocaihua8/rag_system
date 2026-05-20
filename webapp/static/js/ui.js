export function setStatus(message) {
  document.querySelector("#status").textContent = message;
}

export function renderAnswer(answerEl, sourcesEl, data) {
  answerEl.textContent = data.answer;
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

function appendEmptyItem(listEl, message) {
  const item = document.createElement("li");
  item.textContent = message;
  listEl.appendChild(item);
}

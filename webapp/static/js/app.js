import {
  createProject,
  deleteDocument,
  deleteSelectedProject,
  getDocument,
  importBrowserFolder,
  importSelectedProject,
  listDocuments,
  refreshProjects,
  renameSelectedProject,
  selectProject,
} from "./projects.js";
import { runAgentTool } from "./agent.js";
import { ask, listChatMessages, search, startAssessment, submitAssessmentAnswer } from "./qa.js";
import { loadLlmSettings, saveLlmSettings, testLlmSettings } from "./settings.js";
import { state } from "./state.js";
import {
  renderAnswer,
  renderDocumentCount,
  renderDocumentPreview,
  renderDocuments,
  renderImportErrors,
  renderProjectRoot,
  renderAssessmentQuestion,
  renderAssessmentResult,
  renderAssessmentOverview,
  renderAgentToolResult,
  renderChatHistory,
  renderSearchResults,
  renderSkippedDetails,
  setStatus,
} from "./ui.js";

const projectForm = document.querySelector("#project-form");
const projectSelect = document.querySelector("#project-select");
const projectRootEl = document.querySelector("#project-root");
const importButton = document.querySelector("#import-button");
const folderImportButton = document.querySelector("#folder-import-button");
const folderImportInput = document.querySelector("#folder-import-input");
const renameProjectButton = document.querySelector("#rename-project-button");
const deleteProjectButton = document.querySelector("#delete-project-button");
const askButton = document.querySelector("#ask-button");
const agentOverviewButton = document.querySelector("#agent-overview-button");
const agentSearchButton = document.querySelector("#agent-search-button");
const agentSearchQueryInput = document.querySelector("#agent-search-query");
const agentToolResultEl = document.querySelector("#agent-tool-result");
const searchButton = document.querySelector("#search-button");
const answerEl = document.querySelector("#answer");
const sourcesEl = document.querySelector("#sources");
const chatHistoryEl = document.querySelector("#chat-history");
const documentsEl = document.querySelector("#documents");
const documentFilterInput = document.querySelector("#document-filter");
const documentCountEl = document.querySelector("#document-count");
const documentPreviewEl = document.querySelector("#document-preview");
const searchResultsEl = document.querySelector("#search-results");
const skippedDetailsEl = document.querySelector("#skipped-details");
const importErrorsEl = document.querySelector("#import-errors");
const startAssessmentButton = document.querySelector("#start-assessment-button");
const assessmentQuestionEl = document.querySelector("#assessment-question");
const assessmentAnswerInput = document.querySelector("#assessment-answer");
const assessmentAnswerButton = document.querySelector("#assessment-answer-button");
const assessmentResultEl = document.querySelector("#assessment-result");
const assessmentOverviewEl = document.querySelector("#assessment-overview");
const llmSettingsForm = document.querySelector("#llm-settings-form");
const llmProviderSelect = document.querySelector("#llm-provider");
const llmApiBaseInput = document.querySelector("#llm-api-base");
const llmApiModelInput = document.querySelector("#llm-api-model");
const llmApiKeyInput = document.querySelector("#llm-api-key");
const llmSettingsStatusEl = document.querySelector("#llm-settings-status");
const llmTestButton = document.querySelector("#llm-test-button");
const viewNavButtons = Array.from(document.querySelectorAll("[data-view-target]"));
const workspaceViews = Array.from(document.querySelectorAll(".workspace-view"));

for (const button of viewNavButtons) {
  button.addEventListener("click", () => showView(button.dataset.viewTarget));
}

showView("workbench-view");

projectSelect.addEventListener("change", async () => {
  selectProject(projectSelect.value);
  renderSelectedProjectRoot();
  await refreshDocuments();
  await refreshChatHistory();
});

projectForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    setStatus("正在创建项目空间...");
    await createProject(projectForm);
    await refreshProjects(projectSelect);
    projectSelect.value = state.selectedProjectId;
    renderSelectedProjectRoot();
    state.documents = [];
    state.chatMessages = [];
    renderFilteredDocuments();
    renderChatHistory(chatHistoryEl, state.chatMessages);
    renderAgentToolResult(agentToolResultEl, null);
    renderDocumentPreview(documentPreviewEl, null);
    renderSearchResults(searchResultsEl, [], previewDocument);
    renderSkippedDetails(skippedDetailsEl, []);
    renderImportErrors(importErrorsEl, []);
    setStatus("项目空间已创建，可点击导入。");
  } catch (error) {
    setStatus(error.message);
  }
});

importButton.addEventListener("click", async () => {
  try {
    setStatus("正在导入文本资料...");
    const data = await importSelectedProject();
    state.documents = data.documents;
    renderFilteredDocuments();
    renderDocumentPreview(documentPreviewEl, null);
    renderSearchResults(searchResultsEl, [], previewDocument);
    renderSkippedDetails(skippedDetailsEl, data.result.skipped_details);
    renderImportErrors(importErrorsEl, data.result.errors);
    setStatus(
      `导入完成：新增 ${data.result.created}，更新 ${data.result.updated}，未变更 ${data.result.unchanged}，删除 ${data.result.deleted}，跳过 ${data.result.skipped}。`,
    );
  } catch (error) {
    setStatus(error.message);
  }
});

folderImportButton.addEventListener("click", () => {
  folderImportInput.click();
});

folderImportInput.addEventListener("change", async () => {
  try {
    setStatus("正在读取浏览器选择的文件夹...");
    const data = await importBrowserFolder(folderImportInput.files);
    state.documents = data.documents;
    await refreshProjects(projectSelect);
    projectSelect.value = state.selectedProjectId;
    renderSelectedProjectRoot();
    renderFilteredDocuments();
    renderDocumentPreview(documentPreviewEl, null);
    renderSearchResults(searchResultsEl, [], previewDocument);
    renderSkippedDetails(skippedDetailsEl, data.result.skipped_details);
    renderImportErrors(importErrorsEl, data.result.errors);
    setStatus(
      `浏览器导入完成：新增 ${data.result.created}，更新 ${data.result.updated}，未变更 ${data.result.unchanged}，删除 ${data.result.deleted}，跳过 ${data.result.skipped}。`,
    );
  } catch (error) {
    setStatus(error.message);
  } finally {
    folderImportInput.value = "";
  }
});

renameProjectButton.addEventListener("click", async () => {
  const currentProject = state.projects.find((project) => project.id === state.selectedProjectId);
  const nextName = prompt("输入新的项目名称", currentProject?.name || "");
  if (nextName === null) {
    return;
  }
  try {
    setStatus("正在修改项目名称...");
    await renameSelectedProject(nextName);
    await refreshProjects(projectSelect);
    projectSelect.value = state.selectedProjectId;
    renderSelectedProjectRoot();
    setStatus("项目名称已更新。");
  } catch (error) {
    setStatus(error.message);
  }
});

deleteProjectButton.addEventListener("click", async () => {
  if (!confirm("确认删除当前项目空间？此操作会删除该项目空间下的文档记录。")) {
    return;
  }
  try {
    setStatus("正在删除项目空间...");
    await deleteSelectedProject();
    await refreshProjects(projectSelect);
    renderSelectedProjectRoot();
    await refreshDocuments();
    await refreshChatHistory();
    setStatus("项目空间已删除。");
  } catch (error) {
    setStatus(error.message);
  }
});

documentFilterInput.addEventListener("input", () => {
  state.documentFilter = documentFilterInput.value.trim();
  renderFilteredDocuments();
});

searchButton.addEventListener("click", async () => {
  const query = document.querySelector("#search-query").value.trim();
  if (!query) {
    setStatus("请输入检索关键词。");
    return;
  }
  try {
    setStatus("正在检索文件片段...");
    const data = await search(query);
    renderSearchResults(searchResultsEl, data.hits, previewDocument);
    setStatus(`找到 ${data.hits.length} 条结果。`);
  } catch (error) {
    setStatus(error.message);
  }
});

agentOverviewButton.addEventListener("click", async () => {
  try {
    setStatus("正在运行只读项目概览工具...");
    const data = await runAgentTool("project_overview");
    renderAgentToolResult(agentToolResultEl, data);
    setStatus("项目概览工具已完成。");
  } catch (error) {
    setStatus(error.message);
  }
});

agentSearchButton.addEventListener("click", async () => {
  const query = agentSearchQueryInput.value.trim();
  if (!query) {
    setStatus("请输入 Agent 来源检索词。");
    return;
  }
  try {
    setStatus("正在运行只读来源检索工具...");
    const data = await runAgentTool("search_sources", { query });
    renderAgentToolResult(agentToolResultEl, data);
    setStatus(`来源检索工具已完成：${data.result.hit_count} 条。`);
  } catch (error) {
    setStatus(error.message);
  }
});

askButton.addEventListener("click", async () => {
  const question = document.querySelector("#question").value.trim();
  if (!question) {
    setStatus("请输入问题。");
    return;
  }
  try {
    setStatus("正在检索资料...");
    const data = await ask(question);
    renderAnswer(answerEl, sourcesEl, data);
    if (data.message) {
      state.chatMessages = [...state.chatMessages, data.message];
      renderChatHistory(chatHistoryEl, state.chatMessages);
    }
    setStatus("已返回答案。");
  } catch (error) {
    setStatus(error.message);
  }
});

startAssessmentButton.addEventListener("click", async () => {
  try {
    setStatus("正在生成评估题...");
    const data = await startAssessment();
    state.assessmentSession = data.session;
    state.assessmentQuestion = data.session.questions[0] || null;
    assessmentAnswerInput.value = "";
    renderAssessmentQuestion(assessmentQuestionEl, state.assessmentQuestion);
    renderAssessmentResult(assessmentResultEl, null);
    renderAssessmentOverview(assessmentOverviewEl, null);
    setStatus("评估题已生成。");
  } catch (error) {
    setStatus(error.message);
  }
});

assessmentAnswerButton.addEventListener("click", async () => {
  const answer = assessmentAnswerInput.value.trim();
  if (!answer) {
    setStatus("请输入评估回答。");
    return;
  }
  try {
    setStatus("正在评估回答...");
    const data = await submitAssessmentAnswer(answer);
    renderAssessmentResult(assessmentResultEl, data.result);
    renderAssessmentOverview(assessmentOverviewEl, data.result);
    setStatus("评估反馈已生成。");
  } catch (error) {
    setStatus(error.message);
  }
});

llmSettingsForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    llmSettingsStatusEl.textContent = "正在保存模型设置...";
    const data = await saveLlmSettings(llmSettingsForm);
    renderLlmSettings(data.settings);
    llmApiKeyInput.value = "";
    llmSettingsStatusEl.textContent = "模型设置已保存。";
  } catch (error) {
    llmSettingsStatusEl.textContent = error.message;
  }
});

llmTestButton.addEventListener("click", async () => {
  try {
    llmSettingsStatusEl.textContent = "正在测试模型连接...";
    const data = await testLlmSettings();
    llmSettingsStatusEl.textContent = `连接成功：${data.provider}`;
  } catch (error) {
    llmSettingsStatusEl.textContent = error.message;
  }
});

async function refreshDocuments() {
  const data = await listDocuments();
  state.documents = data.documents;
  renderFilteredDocuments();
  renderDocumentPreview(documentPreviewEl, null);
  renderSearchResults(searchResultsEl, [], previewDocument);
  renderSkippedDetails(skippedDetailsEl, []);
  renderImportErrors(importErrorsEl, []);
  state.assessmentSession = null;
  state.assessmentQuestion = null;
  renderAssessmentQuestion(assessmentQuestionEl, null);
  renderAssessmentResult(assessmentResultEl, null);
  renderAssessmentOverview(assessmentOverviewEl, null);
}

async function refreshChatHistory() {
  const data = await listChatMessages();
  state.chatMessages = data.messages;
  renderChatHistory(chatHistoryEl, state.chatMessages);
}

function renderLlmSettings(settings) {
  llmProviderSelect.value = settings.provider || "api";
  llmApiBaseInput.value = settings.api_base || "";
  llmApiModelInput.value = settings.model || "";
  const keyLabel = settings.has_api_key
    ? settings.api_key_source === "environment"
      ? "已从环境变量读取 API Key"
      : "已保存 API Key"
    : "未配置 API Key";
  llmSettingsStatusEl.textContent = keyLabel;
}

function renderFilteredDocuments() {
  const filterText = state.documentFilter.toLowerCase();
  const documents = filterText
    ? state.documents.filter((document) => document.relative_path.toLowerCase().includes(filterText))
    : state.documents;
  const emptyMessage = state.documents.length === 0 ? "暂无导入文件" : "没有匹配文件";
  renderDocuments(documentsEl, documents, previewDocument, removeDocument, emptyMessage);
  renderDocumentCount(documentCountEl, documents.length, state.documents.length);
}

function renderSelectedProjectRoot() {
  const project = state.projects.find((entry) => entry.id === state.selectedProjectId);
  renderProjectRoot(projectRootEl, project);
}

async function removeDocument(documentId) {
  if (!confirm("确认从当前项目空间移除这个文档记录？源文件不会被删除。")) {
    return;
  }
  try {
    setStatus("正在移除文档记录...");
    const data = await deleteDocument(documentId);
    state.documents = data.documents;
    renderFilteredDocuments();
    renderDocumentPreview(documentPreviewEl, null);
    renderSearchResults(searchResultsEl, [], previewDocument);
    setStatus("文档记录已移除。");
  } catch (error) {
    setStatus(error.message);
  }
}

async function previewDocument(documentId) {
  try {
    setStatus("正在读取文件预览...");
    const data = await getDocument(documentId);
    renderDocumentPreview(documentPreviewEl, data.document);
    showView("library-view");
    setStatus("已显示文件预览。");
  } catch (error) {
    setStatus(error.message);
  }
}

function showView(viewId) {
  for (const view of workspaceViews) {
    const isActive = view.id === viewId;
    view.hidden = !isActive;
    view.classList.toggle("active", isActive);
  }
  for (const button of viewNavButtons) {
    const isActive = button.dataset.viewTarget === viewId;
    button.classList.toggle("active", isActive);
    if (isActive) {
      button.setAttribute("aria-current", "page");
    } else {
      button.removeAttribute("aria-current");
    }
  }
}

refreshProjects(projectSelect)
  .then(() => {
    renderSelectedProjectRoot();
    renderAssessmentOverview(assessmentOverviewEl, null);
    loadLlmSettings()
      .then((data) => renderLlmSettings(data.settings))
      .catch((error) => {
        llmSettingsStatusEl.textContent = error.message;
      });
    return refreshDocuments();
  })
  .then(() => refreshChatHistory())
  .catch((error) => setStatus(error.message));

import {
  createProject,
  addDocumentToCollection,
  createDocumentCollection,
  deleteDocumentCollection,
  deleteDocument,
  deleteSelectedProject,
  getDocument,
  getImportBatchDetail,
  getProjectSummary,
  importBrowserFolder,
  importBrowserFiles,
  importPlainTextNote,
  importUrlExcerpt,
  importSelectedProject,
  listDocumentCollections,
  listDocuments,
  listImportBatches,
  removeDocumentFromCollection,
  refreshProjects,
  renameSelectedProject,
  selectProject,
} from "./projects.js";
import { getAgentToolRunDetail, listAgentToolRuns, listAgentTools, runAgentTool } from "./agent.js";
import {
  askStream,
  clearChatMessages,
  createChatSession,
  deleteChatMessage,
  deleteChatSession,
  deleteRetrievalReview,
  getRetrievalSettings,
  getRetrievalReviewDetail,
  listChatMessages,
  listChatSessions,
  listRetrievalReviews,
  renameChatSession,
  saveRetrievalSettings,
  saveRetrievalReview,
  search,
  searchDebug,
  startAssessment,
  submitAnswerFeedback,
  submitAssessmentAnswer,
} from "./qa.js";
import {
  deleteModelProfile,
  listModelProfiles,
  loadLlmSettings,
  saveLlmSettings,
  saveModelProfile,
  setDefaultModelProfile,
  testLlmSettings,
  testModelProfile,
} from "./settings.js";
import { apiGet, apiPost } from "./api.js";
import { state } from "./state.js";
import {
  renderAnswer,
  renderDocumentCount,
  renderDocumentCollections,
  renderDocumentPreview,
  renderDocuments,
  renderImportErrors,
  renderImportBatchDetail,
  renderImportBatches,
  renderProjectHealthError,
  renderProjectHealthStatus,
  renderProjectHealthSummary,
  renderProjectRoot,
  renderAssessmentQuestion,
  renderAssessmentResult,
  renderAssessmentOverview,
  renderAssessmentProgress,
  renderAssessmentResultHistory,
  renderAssessmentMissedQuestions,
  renderAgentToolResult,
  renderAgentToolRunDetail,
  renderAgentToolRuns,
  renderAgentTools,
  renderChatHistory,
  renderChatSessions,
  renderAnswerFeedback,
  renderSearchResults,
  renderSearchDebug,
  renderRetrievalReviews,
  renderRetrievalReviewDetail,
  renderSkippedDetails,
  renderStreamingAnswer,
  renderToolContextNotice,
  renderToolSuggestionAction,
  renderUseToolResultAction,
  setErrorStatus,
  setInlineErrorStatus,
  setStatus,
} from "./ui.js";

const projectForm = document.querySelector("#project-form");
const projectSelect = document.querySelector("#project-select");
const projectRootEl = document.querySelector("#project-root");
const projectHealthStatusEl = document.querySelector("#project-health-status");
const projectHealthMetricsEl = document.querySelector("#project-health-metrics");
const retrievalHealthListEl = document.querySelector("#retrieval-health-list");
const importButton = document.querySelector("#import-button");
const folderImportButton = document.querySelector("#folder-import-button");
const folderImportInput = document.querySelector("#folder-import-input");
const fileImportButton = document.querySelector("#file-import-button");
const fileImportInput = document.querySelector("#file-import-input");
const noteTitleInput = document.querySelector("#note-title");
const noteContentInput = document.querySelector("#note-content");
const noteImportButton = document.querySelector("#note-import-button");
const clipboardTitleInput = document.querySelector("#clipboard-title");
const clipboardContentInput = document.querySelector("#clipboard-content");
const clipboardImportButton = document.querySelector("#clipboard-import-button");
const urlExcerptUrlInput = document.querySelector("#url-excerpt-url");
const urlExcerptTitleInput = document.querySelector("#url-excerpt-title");
const urlExcerptContentInput = document.querySelector("#url-excerpt-content");
const urlExcerptImportButton = document.querySelector("#url-excerpt-import-button");
const renameProjectButton = document.querySelector("#rename-project-button");
const deleteProjectButton = document.querySelector("#delete-project-button");
const askButton = document.querySelector("#ask-button");
const askCancelButton = document.querySelector("#ask-cancel-button");
const toolContextNoticeEl = document.querySelector("#tool-context-notice");
const agentOverviewButton = document.querySelector("#agent-overview-button");
const agentSearchButton = document.querySelector("#agent-search-button");
const agentSearchQueryInput = document.querySelector("#agent-search-query");
const agentToolsListEl = document.querySelector("#agent-tools-list");
const agentToolResultEl = document.querySelector("#agent-tool-result");
const useToolResultButton = document.querySelector("#use-tool-result-button");
const agentToolRunsEl = document.querySelector("#agent-tool-runs");
const agentToolRunDetailEl = document.querySelector("#agent-tool-run-detail");
const searchButton = document.querySelector("#search-button");
const searchDebugButton = document.querySelector("#search-debug-button");
const ragTopKInput = document.querySelector("#rag-top-k");
const ragMinScoreInput = document.querySelector("#rag-min-score");
const ragUseKeywordInput = document.querySelector("#rag-use-keyword");
const ragUseVectorInput = document.querySelector("#rag-use-vector");
const retrievalReviewNoteInput = document.querySelector("#retrieval-review-note");
const saveRagDefaultsButton = document.querySelector("#save-rag-defaults-button");
const ragSettingsStatusEl = document.querySelector("#rag-settings-status");
const saveRetrievalReviewButton = document.querySelector("#save-retrieval-review-button");
const retrievalReviewsEl = document.querySelector("#retrieval-reviews");
const retrievalReviewDetailEl = document.querySelector("#retrieval-review-detail");
const answerEl = document.querySelector("#answer");
const answerFeedbackEl = document.querySelector("#answer-feedback");
const answerFeedbackButtons = Array.from(document.querySelectorAll("[data-feedback-rating]"));
const applyToolSuggestionButton = document.querySelector("#apply-tool-suggestion-button");
const sourcesEl = document.querySelector("#sources");
const chatHistoryEl = document.querySelector("#chat-history");
const chatSessionSelect = document.querySelector("#chat-session-select");
const newChatSessionButton = document.querySelector("#new-chat-session-button");
const renameChatSessionButton = document.querySelector("#rename-chat-session-button");
const deleteChatSessionButton = document.querySelector("#delete-chat-session-button");
const clearChatHistoryButton = document.querySelector("#clear-chat-history-button");
const documentsEl = document.querySelector("#documents");
const documentFilterInput = document.querySelector("#document-filter");
const documentCollectionFilterEl = document.querySelector("#document-collection-filter");
const documentCollectionNameInput = document.querySelector("#document-collection-name");
const createDocumentCollectionButton = document.querySelector("#document-collection-create-button");
const documentCollectionsEl = document.querySelector("#document-collections");
const documentCountEl = document.querySelector("#document-count");
const documentPreviewEl = document.querySelector("#document-preview");
const searchResultsEl = document.querySelector("#search-results");
const searchDebugResultsEl = document.querySelector("#search-debug-results");
const skippedDetailsEl = document.querySelector("#skipped-details");
const importErrorsEl = document.querySelector("#import-errors");
const importBatchesEl = document.querySelector("#import-batches");
const importBatchDetailEl = document.querySelector("#import-batch-detail");
const startAssessmentButton = document.querySelector("#start-assessment-button");
const assessmentQuestionEl = document.querySelector("#assessment-question");
const assessmentAnswerInput = document.querySelector("#assessment-answer");
const assessmentAnswerButton = document.querySelector("#assessment-answer-button");
const assessmentNextButton = document.querySelector("#assessment-next-button");
const assessmentResultEl = document.querySelector("#assessment-result");
const assessmentOverviewEl = document.querySelector("#assessment-overview");
const assessmentProgressEl = document.querySelector("#assessment-progress");
const assessmentResultHistoryEl = document.querySelector("#assessment-result-history");
const assessmentMissedQuestionsEl = document.querySelector("#assessment-missed-questions");
const llmSettingsForm = document.querySelector("#llm-settings-form");
const llmProviderSelect = document.querySelector("#llm-provider");
const llmApiBaseInput = document.querySelector("#llm-api-base");
const llmApiModelInput = document.querySelector("#llm-api-model");
const llmApiKeyInput = document.querySelector("#llm-api-key");
const llmSettingsStatusEl = document.querySelector("#llm-settings-status");
const llmSaveButton = llmSettingsForm.querySelector('button[type="submit"]');
const llmTestButton = document.querySelector("#llm-test-button");
const modelProfileForm = document.querySelector("#model-profile-form");
const modelProfileIdInput = document.querySelector("#model-profile-id");
const modelProfileNameInput = document.querySelector("#model-profile-name");
const modelProfileProviderSelect = document.querySelector("#model-profile-provider");
const modelProfileApiBaseInput = document.querySelector("#model-profile-api-base");
const modelProfileModelInput = document.querySelector("#model-profile-model");
const modelProfileTemperatureInput = document.querySelector("#model-profile-temperature");
const modelProfileMaxTokensInput = document.querySelector("#model-profile-max-tokens");
const modelProfileApiKeyRefSelect = document.querySelector("#model-profile-api-key-ref");
const modelProfileStatusEl = document.querySelector("#model-profile-status");
const modelProfileListEl = document.querySelector("#model-profile-list");
const currentModelProfileLabelEl = document.querySelector("#current-model-profile-label");
const clearDefaultModelProfileButton = document.querySelector("#clear-default-model-profile-button");
const resetModelProfileFormButton = document.querySelector("#reset-model-profile-form-button");
const modelProfileSaveButton = modelProfileForm.querySelector('button[type="submit"]');
const promptPresetForm = document.querySelector("#prompt-preset-form");
const promptPresetIdInput = document.querySelector("#prompt-preset-id");
const promptPresetNameInput = document.querySelector("#prompt-preset-name");
const promptPresetDescriptionInput = document.querySelector("#prompt-preset-description");
const promptPresetSystemInput = document.querySelector("#prompt-preset-system");
const promptPresetFormatInput = document.querySelector("#prompt-preset-format");
const promptPresetStatusEl = document.querySelector("#prompt-preset-status");
const promptPresetListEl = document.querySelector("#prompt-preset-list");
const promptPresetTemplateListEl = document.querySelector("#prompt-preset-template-list");
const currentPromptPresetLabelEl = document.querySelector("#current-prompt-preset-label");
const clearDefaultPromptPresetButton = document.querySelector("#clear-default-prompt-preset-button");
const resetPromptPresetFormButton = document.querySelector("#reset-prompt-preset-form-button");
const promptPresetSaveButton = promptPresetForm.querySelector('button[type="submit"]');
const viewNavButtons = Array.from(document.querySelectorAll("[data-view-target]"));
const workspaceViews = Array.from(document.querySelectorAll(".workspace-view"));
const themeToggleButton = document.querySelector("#theme-toggle-button");
const THEME_STORAGE_KEY = "knowledge-island:theme";
const themeMediaQuery = window.matchMedia("(prefers-color-scheme: dark)");

initializeTheme();

for (const button of viewNavButtons) {
  button.addEventListener("click", () => showView(button.dataset.viewTarget));
}

showView("workbench-view");

themeToggleButton.addEventListener("click", () => {
  const theme = currentTheme() === "dark" ? "light" : "dark";
  applyTheme(theme, { persist: true });
});

themeMediaQuery.addEventListener("change", () => {
  if (!readStoredTheme()) {
    applyTheme(currentSystemTheme());
  }
});

window.addEventListener("error", handleGlobalFrontendError);
window.addEventListener("unhandledrejection", handleGlobalFrontendError);

function handleGlobalFrontendError(event) {
  const reason = event.reason || event.error || event.message || "未知错误";
  const message = reason.message || String(reason);
  setErrorStatus(new Error(`前端出现未处理错误：${message}`));
}

function initializeTheme() {
  applyTheme(readStoredTheme() || currentSystemTheme());
}

function readStoredTheme() {
  const storedTheme = localStorage.getItem(THEME_STORAGE_KEY);
  return storedTheme === "light" || storedTheme === "dark" ? storedTheme : "";
}

function currentSystemTheme() {
  return themeMediaQuery.matches ? "dark" : "light";
}

function currentTheme() {
  return document.documentElement.dataset.theme || currentSystemTheme();
}

function applyTheme(theme, options = {}) {
  document.documentElement.dataset.theme = theme;
  themeToggleButton.textContent = theme === "dark" ? "浅色" : "深色";
  themeToggleButton.setAttribute("aria-pressed", theme === "dark" ? "true" : "false");
  if (options.persist) {
    localStorage.setItem(THEME_STORAGE_KEY, theme);
  }
}

projectSelect.addEventListener("change", async () => {
  selectProject(projectSelect.value);
  clearToolSuggestion();
  clearToolContext();
  clearAnswerFeedback();
  renderSelectedProjectRoot();
  refreshProjectSummary();
  await refreshRetrievalSettings();
  await refreshPromptPresets();
  await refreshChatSessions();
  await refreshDocumentCollections();
  await refreshDocuments();
  await refreshImportBatches();
  await refreshChatHistory();
  state.selectedAgentToolRun = null;
  renderAgentToolRunDetail(agentToolRunDetailEl, null);
  await refreshAgentToolRuns();
  await refreshRetrievalReviews();
  state.selectedRetrievalReview = null;
  renderRetrievalReviewDetail(retrievalReviewDetailEl, null);
});

projectForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    setStatus("正在创建项目空间...");
    await createProject(projectForm);
    await refreshProjects(projectSelect);
    projectSelect.value = state.selectedProjectId;
    renderSelectedProjectRoot();
    refreshProjectSummary();
    await refreshRetrievalSettings();
    await refreshPromptPresets();
    await refreshDocumentCollections();
    state.documents = [];
    state.documentCollections = [];
    state.selectedDocumentCollectionId = "";
    state.importBatches = [];
    state.selectedImportBatch = null;
    renderDocumentCollections(
      documentCollectionsEl,
      documentCollectionFilterEl,
      state.documentCollections,
      state.selectedDocumentCollectionId,
      selectDocumentCollection,
      removeDocumentCollection,
    );
    state.chatMessages = [];
    state.chatSessions = [];
    state.selectedChatSessionId = "";
    renderChatSessions(chatSessionSelect, state.chatSessions, state.selectedChatSessionId);
    renderFilteredDocuments();
    renderChatHistory(chatHistoryEl, state.chatMessages, removeChatMessage);
    renderAgentToolResult(agentToolResultEl, null);
    clearUsableToolResult();
    renderAgentToolRunDetail(agentToolRunDetailEl, null);
    state.agentToolRuns = [];
    state.selectedAgentToolRun = null;
    renderAgentToolRuns(agentToolRunsEl, state.agentToolRuns, showAgentToolRunDetail);
    state.retrievalReviews = [];
    state.selectedRetrievalReview = null;
    renderRetrievalReviews(retrievalReviewsEl, state.retrievalReviews, showRetrievalReviewDetail, removeRetrievalReview);
    renderRetrievalReviewDetail(retrievalReviewDetailEl, null);
    clearToolSuggestion();
    clearToolContext();
    clearAnswerFeedback();
    clearSearchDebug();
    renderDocumentPreview(documentPreviewEl, null);
    renderSearchResults(searchResultsEl, [], previewDocument);
    renderSkippedDetails(skippedDetailsEl, []);
    renderImportErrors(importErrorsEl, []);
    renderImportBatches(importBatchesEl, state.importBatches, showImportBatchDetail);
    renderImportBatchDetail(importBatchDetailEl, null);
    setStatus("项目空间已创建，可点击导入。");
  } catch (error) {
    setErrorStatus(error);
  }
});

importButton.addEventListener("click", async () => {
  await withBusyButton(importButton, "同步中...", async () => {
    try {
      setStatus("正在导入文本资料...");
      const data = await importSelectedProject();
      state.documents = data.documents;
      await refreshProjectSummary();
      renderFilteredDocuments();
      renderDocumentPreview(documentPreviewEl, null);
      renderSearchResults(searchResultsEl, [], previewDocument);
      clearSearchDebug();
      renderSkippedDetails(skippedDetailsEl, data.result.skipped_details);
      renderImportErrors(importErrorsEl, data.result.errors);
      await refreshImportBatches();
      setStatus(
        `导入完成：新增 ${data.result.created}，更新 ${data.result.updated}，未变更 ${data.result.unchanged}，删除 ${data.result.deleted}，跳过 ${data.result.skipped}。`,
      );
    } catch (error) {
      setErrorStatus(error);
    }
  });
});

folderImportButton.addEventListener("click", async () => {
  await withBusyButton(folderImportButton, "选择中...", async () => {
    folderImportInput.click();
  });
});

folderImportInput.addEventListener("change", async () => {
  await withBusyButton(folderImportButton, "导入中...", async () => {
    try {
      setStatus("正在读取浏览器选择的文件夹...");
      const data = await importBrowserFolder(folderImportInput.files);
      state.documents = data.documents;
      await refreshProjects(projectSelect);
      projectSelect.value = state.selectedProjectId;
      renderSelectedProjectRoot();
      await refreshProjectSummary();
      await refreshPromptPresets();
      await refreshDocumentCollections();
      renderFilteredDocuments();
      renderDocumentPreview(documentPreviewEl, null);
      renderSearchResults(searchResultsEl, [], previewDocument);
      clearSearchDebug();
      renderSkippedDetails(skippedDetailsEl, data.result.skipped_details);
      renderImportErrors(importErrorsEl, data.result.errors);
      await refreshImportBatches();
      setStatus(
        `浏览器导入完成：新增 ${data.result.created}，更新 ${data.result.updated}，未变更 ${data.result.unchanged}，删除 ${data.result.deleted}，跳过 ${data.result.skipped}。`,
      );
    } catch (error) {
      setErrorStatus(error);
    } finally {
      folderImportInput.value = "";
    }
  });
});

fileImportButton.addEventListener("click", async () => {
  await withBusyButton(fileImportButton, "选择中...", async () => {
    fileImportInput.click();
  });
});

fileImportInput.addEventListener("change", async () => {
  await withBusyButton(fileImportButton, "导入中...", async () => {
    try {
      const targetLabel = state.selectedProjectId ? "当前项目空间" : "新的 browser-upload 项目空间";
      setStatus(`正在读取选择的文件，并导入到${targetLabel}...`);
      const data = await importBrowserFiles(fileImportInput.files);
      state.documents = data.documents;
      await refreshProjects(projectSelect);
      projectSelect.value = state.selectedProjectId;
      renderSelectedProjectRoot();
      await refreshProjectSummary();
      await refreshPromptPresets();
      await refreshDocumentCollections();
      renderFilteredDocuments();
      renderDocumentPreview(documentPreviewEl, null);
      renderSearchResults(searchResultsEl, [], previewDocument);
      clearSearchDebug();
      renderSkippedDetails(skippedDetailsEl, data.result.skipped_details);
      renderImportErrors(importErrorsEl, data.result.errors);
      await refreshImportBatches();
      setStatus(
        `文件上传导入完成：新增 ${data.result.created}，更新 ${data.result.updated}，未变更 ${data.result.unchanged}，删除 ${data.result.deleted}，跳过 ${data.result.skipped}。`,
      );
    } catch (error) {
      setErrorStatus(error);
    } finally {
      fileImportInput.value = "";
    }
  });
});

noteImportButton.addEventListener("click", async () => {
  await withBusyButton(noteImportButton, "导入中...", async () => {
    try {
      setStatus("正在导入文本笔记...");
      const data = await importPlainTextNote(noteTitleInput.value, noteContentInput.value);
      state.documents = data.documents;
      await refreshProjectSummary();
      renderFilteredDocuments();
      renderDocumentPreview(documentPreviewEl, data.document);
      renderSearchResults(searchResultsEl, [], previewDocument);
      clearSearchDebug();
      renderSkippedDetails(skippedDetailsEl, data.result.skipped_details);
      renderImportErrors(importErrorsEl, data.result.errors);
      await refreshImportBatches();
      noteContentInput.value = "";
      setStatus(
        `文本笔记已导入：新增 ${data.result.created}，更新 ${data.result.updated}，未变更 ${data.result.unchanged}。`,
      );
    } catch (error) {
      setErrorStatus(error);
    }
  });
});

clipboardImportButton.addEventListener("click", async () => {
  await withBusyButton(clipboardImportButton, "导入中...", async () => {
    try {
      setStatus("正在导入剪贴板文本...");
      const data = await importPlainTextNote(clipboardTitleInput.value, clipboardContentInput.value);
      state.documents = data.documents;
      await refreshProjectSummary();
      renderFilteredDocuments();
      renderDocumentPreview(documentPreviewEl, data.document);
      renderSearchResults(searchResultsEl, [], previewDocument);
      clearSearchDebug();
      renderSkippedDetails(skippedDetailsEl, data.result.skipped_details);
      renderImportErrors(importErrorsEl, data.result.errors);
      await refreshImportBatches();
      clipboardContentInput.value = "";
      setStatus(
        `剪贴板文本已导入：新增 ${data.result.created}，更新 ${data.result.updated}，未变更 ${data.result.unchanged}。`,
      );
    } catch (error) {
      setErrorStatus(error);
    }
  });
});

urlExcerptImportButton.addEventListener("click", async () => {
  await withBusyButton(urlExcerptImportButton, "导入中...", async () => {
    try {
      setStatus("正在导入 URL 摘录...");
      const data = await importUrlExcerpt(
        urlExcerptUrlInput.value,
        urlExcerptTitleInput.value,
        urlExcerptContentInput.value,
      );
      state.documents = data.documents;
      await refreshProjectSummary();
      renderFilteredDocuments();
      renderDocumentPreview(documentPreviewEl, data.document);
      renderSearchResults(searchResultsEl, [], previewDocument);
      clearSearchDebug();
      renderSkippedDetails(skippedDetailsEl, data.result.skipped_details);
      renderImportErrors(importErrorsEl, data.result.errors);
      await refreshImportBatches();
      urlExcerptContentInput.value = "";
      setStatus(
        `URL 摘录已导入：新增 ${data.result.created}，更新 ${data.result.updated}，未变更 ${data.result.unchanged}。`,
      );
    } catch (error) {
      setErrorStatus(error);
    }
  });
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
    refreshProjectSummary();
    await refreshRetrievalSettings();
    await refreshPromptPresets();
    await refreshChatSessions();
    setStatus("项目名称已更新。");
  } catch (error) {
    setErrorStatus(error);
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
    clearToolSuggestion();
    clearToolContext();
    clearAnswerFeedback();
    state.selectedAgentToolRun = null;
    renderAgentToolRunDetail(agentToolRunDetailEl, null);
    renderSelectedProjectRoot();
    refreshProjectSummary();
    await refreshPromptPresets();
    await refreshDocumentCollections();
    await refreshDocuments();
    await refreshImportBatches();
    await refreshChatHistory();
    await refreshAgentToolRuns();
    await refreshRetrievalReviews();
    state.selectedRetrievalReview = null;
    renderRetrievalReviewDetail(retrievalReviewDetailEl, null);
    setStatus("项目空间已删除。");
  } catch (error) {
    setErrorStatus(error);
  }
});

documentFilterInput.addEventListener("input", () => {
  state.documentFilter = documentFilterInput.value.trim();
  renderFilteredDocuments();
});

documentCollectionFilterEl.addEventListener("change", async () => {
  state.selectedDocumentCollectionId = documentCollectionFilterEl.value;
  await refreshDocuments();
});

createDocumentCollectionButton.addEventListener("click", async () => {
  const name = documentCollectionNameInput.value.trim();
  if (!name) {
    setStatus("请输入文档集合名称。");
    return;
  }
  try {
    setStatus("正在新建文档集合...");
    await createDocumentCollection(name);
    documentCollectionNameInput.value = "";
    await refreshDocumentCollections();
    setStatus("文档集合已创建。");
  } catch (error) {
    setErrorStatus(error);
  }
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
    setErrorStatus(error);
  }
});

searchDebugButton.addEventListener("click", async () => {
  const query = document.querySelector("#search-query").value.trim();
  if (!query) {
    setStatus("请输入检索关键词。");
    return;
  }
  try {
    setStatus("正在生成检索诊断...");
    const data = await searchDebug(query, {
      top_k: Number(ragTopKInput.value),
      min_score: Number(ragMinScoreInput.value),
      use_keyword: ragUseKeywordInput.checked,
      use_vector: ragUseVectorInput.checked,
    });
    state.searchDebugResult = data;
    renderSearchDebug(searchDebugResultsEl, data);
    setStatus(`检索诊断完成：${data.hits.length} 条来源。`);
  } catch (error) {
    setErrorStatus(error);
  }
});

saveRagDefaultsButton.addEventListener("click", async () => {
  await withBusyButton(saveRagDefaultsButton, "保存中...", async () => {
    try {
      const data = await saveRetrievalSettings(currentRetrievalSettingsFromInputs());
      state.retrievalSettings = data.settings;
      applyRetrievalSettingsToInputs(data.settings);
      ragSettingsStatusEl.textContent = "默认值已保存。";
      setStatus("检索默认值已保存。");
    } catch (error) {
      setInlineErrorStatus(ragSettingsStatusEl, error);
    }
  });
});

saveRetrievalReviewButton.addEventListener("click", async () => {
  if (!state.searchDebugResult) {
    setStatus("请先运行一次检索诊断。");
    return;
  }
  try {
    const debug = state.searchDebugResult.debug || {};
    setStatus("正在保存检索复盘...");
    const data = await saveRetrievalReview(
      debug.query || "",
      retrievalReviewNoteInput.value,
      debug.parameters || {},
    );
    state.retrievalReviews = [data.review, ...state.retrievalReviews];
    renderRetrievalReviews(retrievalReviewsEl, state.retrievalReviews, showRetrievalReviewDetail, removeRetrievalReview);
    await refreshProjectSummary();
    retrievalReviewNoteInput.value = "";
    setStatus("检索复盘已保存。");
  } catch (error) {
    setErrorStatus(error);
  }
});

clearChatHistoryButton.addEventListener("click", async () => {
  if (!confirm("确认清空当前项目的全部聊天记录？此操作不会删除文档、检索复盘或工具运行记录。")) {
    return;
  }
  try {
    setStatus("正在清空聊天记录...");
    const data = await clearChatMessages();
    state.chatMessages = data.messages;
    renderChatHistory(chatHistoryEl, state.chatMessages, removeChatMessage);
    await refreshProjectSummary();
    setStatus(`已清空 ${data.deleted} 条聊天记录。`);
  } catch (error) {
    setErrorStatus(error);
  }
});

chatSessionSelect.addEventListener("change", async () => {
  state.selectedChatSessionId = chatSessionSelect.value;
  clearAnswerFeedback();
  await refreshChatHistory();
});

newChatSessionButton.addEventListener("click", async () => {
  const title = prompt("会话标题", "新会话");
  if (title === null) {
    return;
  }
  try {
    const data = await createChatSession(title);
    state.selectedChatSessionId = data.session.id;
    await refreshChatSessions();
    await refreshChatHistory();
    setStatus("聊天会话已创建。");
  } catch (error) {
    setErrorStatus(error);
  }
});

renameChatSessionButton.addEventListener("click", async () => {
  if (!state.selectedChatSessionId) {
    setStatus("默认会话不能改名，请先选择一个已创建的会话。");
    return;
  }
  const current = state.chatSessions.find((session) => session.id === state.selectedChatSessionId);
  const title = prompt("新的会话标题", current?.title || "");
  if (title === null) {
    return;
  }
  try {
    await renameChatSession(state.selectedChatSessionId, title);
    await refreshChatSessions();
    setStatus("聊天会话已改名。");
  } catch (error) {
    setErrorStatus(error);
  }
});

deleteChatSessionButton.addEventListener("click", async () => {
  if (!state.selectedChatSessionId) {
    setStatus("默认会话不能删除。");
    return;
  }
  if (!confirm("确认删除当前聊天会话？此操作会删除该会话内的聊天记录。")) {
    return;
  }
  try {
    const data = await deleteChatSession(state.selectedChatSessionId);
    state.chatSessions = data.sessions;
    state.selectedChatSessionId = "";
    renderChatSessions(chatSessionSelect, state.chatSessions, state.selectedChatSessionId);
    await refreshChatHistory();
    await refreshProjectSummary();
    setStatus("聊天会话已删除。");
  } catch (error) {
    setErrorStatus(error);
  }
});

agentOverviewButton.addEventListener("click", async () => {
  await runAgentToolFromPanel("project_overview");
});

agentSearchButton.addEventListener("click", async () => {
  await runAgentToolFromPanel("search_sources");
});

askButton.addEventListener("click", async () => {
  const question = document.querySelector("#question").value.trim();
  if (!question) {
    setStatus("请输入问题。");
    return;
  }
  state.currentAnswerAbortController = null;
  askCancelButton.hidden = false;
  askCancelButton.disabled = false;
  await withBusyButton(askButton, "提问中...", async () => {
    try {
      setStatus("正在检索资料...");
      renderStreamingAnswer(answerEl, "");
      clearAnswerFeedback();
      const stream = askStream(question, {
        onToken: (answer) => {
          renderStreamingAnswer(answerEl, answer);
          setStatus("正在生成答案...");
        },
      });
      state.currentAnswerAbortController = stream;
      const data = await stream.promise;
      renderAnswer(answerEl, sourcesEl, data);
      renderToolContextNotice(toolContextNoticeEl, data.tool_context || null);
      if (data.tool_context) {
        consumeToolContext();
      }
      state.currentToolSuggestion = data.tool_suggestion || null;
      renderToolSuggestionAction(applyToolSuggestionButton, state.currentToolSuggestion);
      if (data.message) {
        state.lastAnswerMessageId = data.message.id;
        renderAnswerFeedback(answerFeedbackEl, state.lastAnswerMessageId);
        state.chatMessages = [...state.chatMessages, data.message];
        renderChatHistory(chatHistoryEl, state.chatMessages, removeChatMessage);
        if (state.selectedChatSessionId) {
          await refreshChatSessions();
        }
        await refreshProjectSummary();
      } else {
        clearAnswerFeedback();
      }
      setStatus("已返回答案。");
    } catch (error) {
      if (error.name === "AbortError") {
        setStatus("已取消本次提问。");
      } else {
        setErrorStatus(error);
      }
    } finally {
      state.currentAnswerAbortController = null;
      askCancelButton.hidden = true;
      askCancelButton.disabled = false;
    }
  });
});

askCancelButton.addEventListener("click", () => {
  if (!state.currentAnswerAbortController) {
    return;
  }
  askCancelButton.disabled = true;
  setStatus("正在取消本次提问...");
  state.currentAnswerAbortController.abort();
});

for (const button of answerFeedbackButtons) {
  button.addEventListener("click", async () => {
    const rating = button.dataset.feedbackRating || "";
    await withBusyButton(button, "保存中...", async () => {
      try {
        const data = await submitAnswerFeedback(state.lastAnswerMessageId, rating);
        renderAnswerFeedback(answerFeedbackEl, state.lastAnswerMessageId, `已保存：${formatFeedbackRating(data.feedback.rating)}`);
        setStatus("回答反馈已保存。");
      } catch (error) {
        setErrorStatus(error);
      }
    });
  });
}

applyToolSuggestionButton.addEventListener("click", async () => {
  if (!state.currentToolSuggestion) {
    setStatus("暂无可运行的建议工具。");
    return;
  }
  if (state.currentToolSuggestion.tool !== "search_sources") {
    setStatus("当前只支持运行 search_sources 建议工具。");
    return;
  }
  try {
    const argumentsPayload = state.currentToolSuggestion.arguments || {};
    agentSearchQueryInput.value = argumentsPayload.query || "";
    setStatus("正在按建议运行只读来源检索工具...");
    const data = await runAgentTool("search_sources", state.currentToolSuggestion.arguments);
    renderAgentToolResult(agentToolResultEl, data);
    setLastUsableToolRun(data);
    await refreshAgentToolRuns();
    await refreshProjectSummary();
    setStatus(`建议工具已完成：${data.result.hit_count} 条。`);
  } catch (error) {
    setErrorStatus(error);
  }
});

useToolResultButton.addEventListener("click", () => {
  const runId = state.lastUsableToolRun?.id || "";
  if (!runId) {
    setStatus("暂无可引用的工具结果。");
    return;
  }
  state.currentToolContextRunId = runId;
  renderToolContextNotice(toolContextNoticeEl, {
    tool_run_id: runId,
    query: state.lastUsableToolRun.result?.query || state.lastUsableToolRun.tool_name,
  });
  setStatus(`下一问将引用工具运行 ID：${runId}`);
});

startAssessmentButton.addEventListener("click", async () => {
  await withBusyButton(startAssessmentButton, "生成中...", async () => {
    try {
      setStatus("正在生成评估题...");
      const data = await startAssessment();
      initializeAssessmentSession(data.session);
      setStatus(`评估题已生成，共 ${(data.session.questions || []).length} 题。`);
    } catch (error) {
      setErrorStatus(error);
    }
  });
});

assessmentAnswerButton.addEventListener("click", async () => {
  if (state.assessmentAnsweredCurrent) {
    setStatus("请先进入下一题，或重新开始评估。");
    return;
  }
  const answer = assessmentAnswerInput.value.trim();
  if (!answer) {
    setStatus("请输入评估回答。");
    return;
  }
  let submitted = false;
  await withBusyButton(assessmentAnswerButton, "评估中...", async () => {
    try {
      setStatus("正在评估回答...");
      const data = await submitAssessmentAnswer(answer);
      const entry = {
        question: state.assessmentQuestion,
        result: data.result,
        answer,
      };
      state.assessmentResults.push(entry);
      state.assessmentMissedQuestions = state.assessmentResults.filter((item) => item.result?.status !== "已掌握");
      state.assessmentAnsweredCurrent = true;
      renderAssessmentResult(assessmentResultEl, data.result);
      renderAssessmentOverview(assessmentOverviewEl, data.result);
      renderAssessmentProgress(assessmentProgressEl, state.assessmentSession, state.assessmentQuestionIndex, state.assessmentResults);
      renderAssessmentResultHistory(assessmentResultHistoryEl, state.assessmentResults);
      renderAssessmentMissedQuestions(assessmentMissedQuestionsEl, state.assessmentMissedQuestions);
      assessmentNextButton.hidden = false;
      assessmentNextButton.textContent = hasNextAssessmentQuestion() ? "下一题" : "完成评估";
      setStatus(hasNextAssessmentQuestion() ? "评估反馈已生成，可进入下一题。" : "最后一题反馈已生成，可完成评估。");
      submitted = true;
    } catch (error) {
      setErrorStatus(error);
    }
  });
  if (submitted) {
    setAssessmentInputEnabled(false);
  }
});

assessmentNextButton.addEventListener("click", () => {
  advanceAssessmentQuestion();
});

llmSettingsForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  await withBusyButton(llmSaveButton, "保存中...", async () => {
    try {
      llmSettingsStatusEl.textContent = "正在保存模型设置...";
      const data = await saveLlmSettings(llmSettingsForm);
      renderLlmSettings(data.settings);
      llmApiKeyInput.value = "";
      llmSettingsStatusEl.textContent = `模型设置已保存。${formatLlmSettingsSummary(data.settings)}`;
    } catch (error) {
      setInlineErrorStatus(llmSettingsStatusEl, error);
    }
  });
});

llmTestButton.addEventListener("click", async () => {
  await withBusyButton(llmTestButton, "测试中...", async () => {
    try {
      llmSettingsStatusEl.textContent = "正在测试模型连接...";
      const data = await testLlmSettings();
      llmSettingsStatusEl.textContent = `连接成功：${data.provider}。${formatLlmSettingsSummary(data.settings || currentLlmSettings())}`;
    } catch (error) {
      setInlineErrorStatus(llmSettingsStatusEl, error);
    }
  });
});

modelProfileForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  await withBusyButton(modelProfileSaveButton, "保存中...", async () => {
    try {
      modelProfileStatusEl.textContent = "正在保存模型 Profile...";
      const data = await saveModelProfile(modelProfileForm);
      resetModelProfileForm();
      await refreshModelProfiles();
      modelProfileStatusEl.textContent = `模型 Profile 已保存：${data.profile.name}`;
    } catch (error) {
      setInlineErrorStatus(modelProfileStatusEl, error);
    }
  });
});

clearDefaultModelProfileButton.addEventListener("click", async () => {
  try {
    await setDefaultModelProfile("");
    await refreshModelProfiles();
    modelProfileStatusEl.textContent = "已清空默认模型 Profile。";
  } catch (error) {
    setInlineErrorStatus(modelProfileStatusEl, error);
  }
});

resetModelProfileFormButton.addEventListener("click", () => {
  resetModelProfileForm();
  modelProfileStatusEl.textContent = "已取消编辑。";
});

promptPresetForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  await withBusyButton(promptPresetSaveButton, "保存中...", async () => {
    try {
      const payload = currentPromptPresetFormData();
      const path = payload.preset_id ? "/api/prompt-presets/update" : "/api/prompt-presets";
      const data = await apiPost(path, payload);
      resetPromptPresetForm();
      await refreshPromptPresets();
      promptPresetStatusEl.textContent = `Prompt 预设已保存：${data.preset.name}`;
    } catch (error) {
      setInlineErrorStatus(promptPresetStatusEl, error);
    }
  });
});

clearDefaultPromptPresetButton.addEventListener("click", async () => {
  if (!state.selectedProjectId) {
    promptPresetStatusEl.textContent = "请先选择项目空间。";
    return;
  }
  try {
    await apiPost("/api/prompt-presets/default", {
      project_id: state.selectedProjectId,
      preset_id: "",
    });
    await refreshPromptPresets();
    promptPresetStatusEl.textContent = "已清空默认 Prompt 预设。";
  } catch (error) {
    setInlineErrorStatus(promptPresetStatusEl, error);
  }
});

resetPromptPresetFormButton.addEventListener("click", () => {
  resetPromptPresetForm();
  promptPresetStatusEl.textContent = "已取消编辑。";
});

function initializeAssessmentSession(session) {
  state.assessmentSession = session;
  state.assessmentQuestionIndex = 0;
  state.assessmentResults = [];
  state.assessmentMissedQuestions = [];
  state.assessmentAnsweredCurrent = false;
  state.assessmentQuestion = currentAssessmentQuestion();
  assessmentAnswerInput.value = "";
  assessmentNextButton.hidden = true;
  setAssessmentInputEnabled(Boolean(state.assessmentQuestion));
  renderAssessmentQuestion(assessmentQuestionEl, state.assessmentQuestion);
  renderAssessmentResult(assessmentResultEl, null);
  renderAssessmentOverview(assessmentOverviewEl, null);
  renderAssessmentProgress(assessmentProgressEl, state.assessmentSession, state.assessmentQuestionIndex, state.assessmentResults);
  renderAssessmentResultHistory(assessmentResultHistoryEl, state.assessmentResults);
  renderAssessmentMissedQuestions(assessmentMissedQuestionsEl, state.assessmentMissedQuestions);
}

function advanceAssessmentQuestion() {
  if (!state.assessmentSession) {
    setStatus("请先开始评估。");
    return;
  }
  if (!hasNextAssessmentQuestion()) {
    completeAssessmentSession();
    return;
  }
  state.assessmentQuestionIndex += 1;
  state.assessmentQuestion = currentAssessmentQuestion();
  state.assessmentAnsweredCurrent = false;
  assessmentAnswerInput.value = "";
  assessmentNextButton.hidden = true;
  setAssessmentInputEnabled(true);
  renderAssessmentQuestion(assessmentQuestionEl, state.assessmentQuestion);
  renderAssessmentResult(assessmentResultEl, null);
  renderAssessmentOverview(assessmentOverviewEl, null);
  renderAssessmentProgress(assessmentProgressEl, state.assessmentSession, state.assessmentQuestionIndex, state.assessmentResults);
  setStatus(`进入第 ${state.assessmentQuestionIndex + 1} 题。`);
}

function completeAssessmentSession() {
  const total = state.assessmentSession?.questions?.length || 0;
  state.assessmentQuestion = null;
  state.assessmentAnsweredCurrent = true;
  assessmentNextButton.hidden = true;
  setAssessmentInputEnabled(false);
  assessmentQuestionEl.textContent = `本轮评估已完成，共 ${state.assessmentResults.length} / ${total} 题。`;
  renderAssessmentProgress(assessmentProgressEl, state.assessmentSession, total - 1, state.assessmentResults);
  renderAssessmentResultHistory(assessmentResultHistoryEl, state.assessmentResults);
  renderAssessmentMissedQuestions(assessmentMissedQuestionsEl, state.assessmentMissedQuestions);
  setStatus("本轮评估已完成，可查看答题记录和待复测题目。");
}

function resetAssessmentState() {
  state.assessmentSession = null;
  state.assessmentQuestion = null;
  state.assessmentQuestionIndex = 0;
  state.assessmentResults = [];
  state.assessmentMissedQuestions = [];
  state.assessmentAnsweredCurrent = false;
  assessmentAnswerInput.value = "";
  assessmentNextButton.hidden = true;
  setAssessmentInputEnabled(true);
  renderAssessmentQuestion(assessmentQuestionEl, null);
  renderAssessmentResult(assessmentResultEl, null);
  renderAssessmentOverview(assessmentOverviewEl, null);
  renderAssessmentProgress(assessmentProgressEl, null, 0, []);
  renderAssessmentResultHistory(assessmentResultHistoryEl, []);
  renderAssessmentMissedQuestions(assessmentMissedQuestionsEl, []);
}

function currentAssessmentQuestion() {
  const questions = Array.isArray(state.assessmentSession?.questions)
    ? state.assessmentSession.questions
    : [];
  return questions[state.assessmentQuestionIndex] || null;
}

function hasNextAssessmentQuestion() {
  const questions = Array.isArray(state.assessmentSession?.questions)
    ? state.assessmentSession.questions
    : [];
  return state.assessmentQuestionIndex + 1 < questions.length;
}

function setAssessmentInputEnabled(enabled) {
  assessmentAnswerInput.disabled = !enabled;
  assessmentAnswerButton.disabled = !enabled;
}

async function refreshDocuments() {
  const data = await listDocuments();
  state.documents = data.documents;
  renderFilteredDocuments();
  renderDocumentPreview(documentPreviewEl, null);
  renderSearchResults(searchResultsEl, [], previewDocument);
  clearSearchDebug();
  renderSkippedDetails(skippedDetailsEl, []);
  renderImportErrors(importErrorsEl, []);
  resetAssessmentState();
}

async function refreshDocumentCollections() {
  const data = await listDocumentCollections();
  state.documentCollections = data.collections;
  if (
    state.selectedDocumentCollectionId
    && state.selectedDocumentCollectionId !== "unassigned"
    && !state.documentCollections.some((collection) => collection.id === state.selectedDocumentCollectionId)
  ) {
    state.selectedDocumentCollectionId = "";
  }
  renderDocumentCollections(
    documentCollectionsEl,
    documentCollectionFilterEl,
    state.documentCollections,
    state.selectedDocumentCollectionId,
    selectDocumentCollection,
    removeDocumentCollection,
  );
}

async function refreshImportBatches() {
  const data = await listImportBatches();
  state.importBatches = data.batches;
  state.selectedImportBatch = null;
  renderImportBatches(importBatchesEl, state.importBatches, showImportBatchDetail);
  renderImportBatchDetail(importBatchDetailEl, null);
}

async function showImportBatchDetail(batchId) {
  try {
    setStatus("正在读取导入批次详情...");
    const data = await getImportBatchDetail(batchId);
    state.selectedImportBatch = data.batch;
    renderImportBatchDetail(importBatchDetailEl, data.batch, data.items || []);
    setStatus("已显示导入批次详情。");
  } catch (error) {
    setErrorStatus(error);
  }
}

async function refreshRetrievalSettings() {
  try {
    const data = await getRetrievalSettings();
    state.retrievalSettings = data.settings;
    applyRetrievalSettingsToInputs(data.settings);
    ragSettingsStatusEl.textContent = data.settings ? "已加载当前项目默认值。" : "请选择项目空间。";
  } catch (error) {
    state.retrievalSettings = null;
    setInlineErrorStatus(ragSettingsStatusEl, error);
  }
}

function applyRetrievalSettingsToInputs(settings) {
  const values = settings || {
    top_k: 5,
    min_score: 0,
    use_keyword: true,
    use_vector: true,
  };
  ragTopKInput.value = values.top_k ?? 5;
  ragMinScoreInput.value = values.min_score ?? 0;
  ragUseKeywordInput.checked = Boolean(values.use_keyword);
  ragUseVectorInput.checked = Boolean(values.use_vector);
}

function currentRetrievalSettingsFromInputs() {
  return {
    top_k: Number(ragTopKInput.value),
    min_score: Number(ragMinScoreInput.value),
    use_keyword: ragUseKeywordInput.checked,
    use_vector: ragUseVectorInput.checked,
  };
}

async function refreshPromptPresets() {
  if (!state.selectedProjectId) {
    state.promptPresets = [];
    state.promptPresetTemplates = [];
    state.selectedPromptPresetId = "";
    renderPromptPresetList();
    renderPromptPresetTemplates();
    return;
  }
  try {
    const data = await apiGet(`/api/prompt-presets?project_id=${encodeURIComponent(state.selectedProjectId)}`);
    state.promptPresets = data.presets || [];
    state.promptPresetTemplates = data.templates || [];
    state.selectedPromptPresetId = data.default_preset_id || "";
    renderPromptPresetList();
    renderPromptPresetTemplates();
    promptPresetStatusEl.textContent = "已加载当前项目 Prompt 预设。";
  } catch (error) {
    state.promptPresets = [];
    state.selectedPromptPresetId = "";
    renderPromptPresetList();
    renderPromptPresetTemplates();
    setInlineErrorStatus(promptPresetStatusEl, error);
  }
}

function renderPromptPresetList() {
  promptPresetListEl.innerHTML = "";
  updateCurrentPromptPresetLabel();
  if (!state.selectedProjectId) {
    appendPromptPresetLine(promptPresetListEl, "请选择项目空间后管理 Prompt 预设。");
    return;
  }
  if (state.promptPresets.length === 0) {
    appendPromptPresetLine(promptPresetListEl, "暂无 Prompt 预设，可从模板复制后保存。");
    return;
  }
  for (const preset of state.promptPresets) {
    const item = document.createElement("li");
    const title = document.createElement("strong");
    title.textContent = preset.id === state.selectedPromptPresetId ? `${preset.name}（默认）` : preset.name;
    const desc = document.createElement("span");
    desc.textContent = preset.description || "无说明";
    const actions = document.createElement("div");
    actions.className = "project-actions compact";
    const editButton = document.createElement("button");
    editButton.type = "button";
    editButton.textContent = "编辑";
    editButton.addEventListener("click", () => editPromptPreset(preset));
    const defaultButton = document.createElement("button");
    defaultButton.type = "button";
    defaultButton.textContent = "设为默认";
    defaultButton.addEventListener("click", () => setDefaultPromptPreset(preset.id));
    const deleteButton = document.createElement("button");
    deleteButton.type = "button";
    deleteButton.textContent = "删除";
    deleteButton.addEventListener("click", () => deletePromptPreset(preset.id));
    actions.append(editButton, defaultButton, deleteButton);
    item.append(title, desc, actions);
    promptPresetListEl.appendChild(item);
  }
}

function renderPromptPresetTemplates() {
  promptPresetTemplateListEl.innerHTML = "";
  if (state.promptPresetTemplates.length === 0) {
    appendPromptPresetLine(promptPresetTemplateListEl, "暂无内置模板。");
    return;
  }
  for (const template of state.promptPresetTemplates) {
    const item = document.createElement("li");
    const title = document.createElement("strong");
    title.textContent = template.name;
    const desc = document.createElement("span");
    desc.textContent = template.description || "";
    const copyButton = document.createElement("button");
    copyButton.type = "button";
    copyButton.textContent = "复制模板";
    copyButton.addEventListener("click", () => copyPromptPresetTemplate(template));
    item.append(title, desc, copyButton);
    promptPresetTemplateListEl.appendChild(item);
  }
}

function appendPromptPresetLine(listEl, text) {
  const item = document.createElement("li");
  item.textContent = text;
  listEl.appendChild(item);
}

function updateCurrentPromptPresetLabel() {
  const preset = state.promptPresets.find((entry) => entry.id === state.selectedPromptPresetId);
  currentPromptPresetLabelEl.textContent = preset ? preset.name : "未选择";
}

function currentPromptPresetFormData() {
  if (!state.selectedProjectId) {
    throw new Error("请先选择项目空间");
  }
  return {
    project_id: state.selectedProjectId,
    preset_id: promptPresetIdInput.value,
    name: promptPresetNameInput.value,
    description: promptPresetDescriptionInput.value,
    system_prompt: promptPresetSystemInput.value,
    answer_format: promptPresetFormatInput.value,
  };
}

function editPromptPreset(preset) {
  state.editingPromptPresetId = preset.id;
  promptPresetIdInput.value = preset.id;
  promptPresetNameInput.value = preset.name || "";
  promptPresetDescriptionInput.value = preset.description || "";
  promptPresetSystemInput.value = preset.system_prompt || "";
  promptPresetFormatInput.value = preset.answer_format || "";
  promptPresetStatusEl.textContent = `正在编辑 Prompt 预设：${preset.name}`;
}

function copyPromptPresetTemplate(template) {
  state.editingPromptPresetId = "";
  promptPresetIdInput.value = "";
  promptPresetNameInput.value = template.name || "";
  promptPresetDescriptionInput.value = template.description || "";
  promptPresetSystemInput.value = template.system_prompt || "";
  promptPresetFormatInput.value = template.answer_format || "";
  promptPresetStatusEl.textContent = `已复制模板：${template.name}`;
}

function resetPromptPresetForm() {
  state.editingPromptPresetId = "";
  promptPresetForm.reset();
  promptPresetIdInput.value = "";
}

async function setDefaultPromptPreset(presetId) {
  try {
    await apiPost("/api/prompt-presets/default", {
      project_id: state.selectedProjectId,
      preset_id: presetId,
    });
    await refreshPromptPresets();
    promptPresetStatusEl.textContent = "默认 Prompt 预设已更新。";
  } catch (error) {
    setInlineErrorStatus(promptPresetStatusEl, error);
  }
}

async function deletePromptPreset(presetId) {
  if (!confirm("确认删除这个 Prompt 预设？")) {
    return;
  }
  try {
    await apiPost("/api/prompt-presets/delete", { preset_id: presetId });
    resetPromptPresetForm();
    await refreshPromptPresets();
    promptPresetStatusEl.textContent = "Prompt 预设已删除。";
  } catch (error) {
    setInlineErrorStatus(promptPresetStatusEl, error);
  }
}

function clearToolSuggestion() {
  state.currentToolSuggestion = null;
  renderToolSuggestionAction(applyToolSuggestionButton, state.currentToolSuggestion);
}

function clearAnswerFeedback() {
  state.lastAnswerMessageId = "";
  renderAnswerFeedback(answerFeedbackEl, state.lastAnswerMessageId);
}

function formatFeedbackRating(rating) {
  return {
    useful: "有用",
    not_useful: "无用",
    source_wrong: "来源不准",
    need_more_context: "需要更多上下文",
  }[rating] || rating;
}

function setToolContext(data) {
  if (data.run?.tool_name === "search_sources" && data.run.status === "success") {
    state.currentToolContextRunId = data.run.id;
    renderToolContextNotice(toolContextNoticeEl, data.result || null);
  }
}

function setLastUsableToolRun(data) {
  state.lastUsableToolRun = data.run?.tool_name === "search_sources" && data.run.status === "success"
    ? data.run
    : null;
  renderUseToolResultAction(useToolResultButton, state.lastUsableToolRun);
}

function clearUsableToolResult() {
  state.lastUsableToolRun = null;
  renderUseToolResultAction(useToolResultButton, null);
}

function clearToolContext() {
  state.currentToolContextRunId = "";
  renderToolContextNotice(toolContextNoticeEl, null);
}

function consumeToolContext() {
  state.currentToolContextRunId = "";
}

function clearSearchDebug() {
  state.searchDebugResult = null;
  renderSearchDebug(searchDebugResultsEl, null);
}

async function refreshChatHistory() {
  const data = await listChatMessages();
  state.chatMessages = data.messages;
  renderChatHistory(chatHistoryEl, state.chatMessages, removeChatMessage);
}

async function refreshChatSessions() {
  const data = await listChatSessions();
  state.chatSessions = data.sessions;
  if (state.selectedChatSessionId && !state.chatSessions.some((session) => session.id === state.selectedChatSessionId)) {
    state.selectedChatSessionId = "";
  }
  renderChatSessions(chatSessionSelect, state.chatSessions, state.selectedChatSessionId);
}

async function removeChatMessage(messageId) {
  if (!confirm("确认删除这条聊天记录？此操作不会删除来源文档。")) {
    return;
  }
  try {
    setStatus("正在删除聊天记录...");
    const data = await deleteChatMessage(messageId);
    state.chatMessages = data.messages;
    renderChatHistory(chatHistoryEl, state.chatMessages, removeChatMessage);
    await refreshProjectSummary();
    setStatus("聊天记录已删除。");
  } catch (error) {
    setErrorStatus(error);
  }
}

async function refreshAgentToolRuns() {
  const data = await listAgentToolRuns();
  state.agentToolRuns = data.runs;
  renderAgentToolRuns(agentToolRunsEl, state.agentToolRuns, showAgentToolRunDetail);
}

async function refreshAgentTools() {
  const data = await listAgentTools();
  state.agentTools = data.tools;
  renderAgentTools(agentToolsListEl, state.agentTools, runAgentToolFromPanel);
}

async function runAgentToolFromPanel(toolName) {
  try {
    if (toolName === "project_overview") {
      setStatus("正在运行只读项目概览工具...");
      const data = await runAgentTool("project_overview", {});
      renderAgentToolResult(agentToolResultEl, data);
      setLastUsableToolRun(data);
      await refreshAgentToolRuns();
      await refreshProjectSummary();
      setStatus("项目概览工具已完成。");
      return;
    }
    if (toolName === "search_sources") {
      const query = agentSearchQueryInput.value.trim();
      if (!query) {
        setStatus("请输入 Agent 工具参数 query。");
        return;
      }
      setStatus("正在运行只读来源检索工具...");
      const data = await runAgentTool("search_sources", { query });
      renderAgentToolResult(agentToolResultEl, data);
      setLastUsableToolRun(data);
      await refreshAgentToolRuns();
      await refreshProjectSummary();
      setStatus(`来源检索工具已完成：${data.result.hit_count} 条。`);
      return;
    }
    setStatus("当前只支持只读白名单工具。");
  } catch (error) {
    setErrorStatus(error);
  }
}

async function showAgentToolRunDetail(runId) {
  try {
    agentToolRunDetailEl.textContent = "正在读取工具运行详情...";
    const data = await getAgentToolRunDetail(runId);
    state.selectedAgentToolRun = data.run;
    renderAgentToolRunDetail(agentToolRunDetailEl, state.selectedAgentToolRun);
  } catch (error) {
    state.selectedAgentToolRun = null;
    setInlineErrorStatus(agentToolRunDetailEl, error);
  }
}

async function refreshRetrievalReviews() {
  const data = await listRetrievalReviews();
  state.retrievalReviews = data.reviews;
  renderRetrievalReviews(retrievalReviewsEl, state.retrievalReviews, showRetrievalReviewDetail, removeRetrievalReview);
}

async function showRetrievalReviewDetail(reviewId) {
  try {
    retrievalReviewDetailEl.textContent = "正在读取检索复盘详情...";
    const data = await getRetrievalReviewDetail(reviewId);
    state.selectedRetrievalReview = data.review;
    renderRetrievalReviewDetail(retrievalReviewDetailEl, state.selectedRetrievalReview);
  } catch (error) {
    state.selectedRetrievalReview = null;
    setInlineErrorStatus(retrievalReviewDetailEl, error);
  }
}

async function removeRetrievalReview(reviewId) {
  if (!confirm("确认删除这条检索复盘？此操作只会删除复盘记录，不会调整检索参数或资料。")) {
    return;
  }
  try {
    setStatus("正在删除检索复盘...");
    const data = await deleteRetrievalReview(reviewId);
    state.retrievalReviews = data.reviews || state.retrievalReviews.filter((review) => review.id !== reviewId);
    if (state.selectedRetrievalReview?.id === reviewId) {
      state.selectedRetrievalReview = null;
      renderRetrievalReviewDetail(retrievalReviewDetailEl, null);
    }
    renderRetrievalReviews(retrievalReviewsEl, state.retrievalReviews, showRetrievalReviewDetail, removeRetrievalReview);
    await refreshProjectSummary();
    setStatus("检索复盘已删除。");
  } catch (error) {
    setErrorStatus(error);
  }
}

async function refreshProjectSummary() {
  try {
    const data = await getProjectSummary();
    state.projectSummary = data.summary;
    renderProjectHealthSummary(projectHealthMetricsEl, retrievalHealthListEl, state.projectSummary);
    renderProjectHealthStatus(projectHealthStatusEl, state.projectSummary);
  } catch (error) {
    state.projectSummary = null;
    renderProjectHealthSummary(projectHealthMetricsEl, retrievalHealthListEl, null);
    renderProjectHealthError(projectHealthStatusEl);
    setInlineErrorStatus(projectHealthStatusEl, error);
  }
}

function renderLlmSettings(settings) {
  llmProviderSelect.value = settings.provider || "api";
  llmApiBaseInput.value = settings.api_base || "";
  llmApiModelInput.value = settings.model || "";
  llmSettingsStatusEl.textContent = formatLlmSettingsSummary(settings);
}

function currentLlmSettings() {
  return {
    provider: llmProviderSelect.value,
    api_base: llmApiBaseInput.value,
    model: llmApiModelInput.value,
    has_api_key: Boolean(llmApiKeyInput.value),
  };
}

function formatLlmSettingsSummary(settings) {
  const providerText = settings.provider || "api";
  const baseText = settings.api_base || "未填写";
  const modelText = settings.model || "未填写";
  const keyLabel = settings.has_api_key
    ? settings.api_key_source === "environment"
      ? "已从环境变量读取 API Key"
      : "已保存 API Key"
    : "未配置 API Key";
  return `模型服务：${providerText} / API 地址：${baseText} / 模型名称：${modelText} / API Key：${keyLabel}`;
}

async function refreshModelProfiles() {
  try {
    const data = await listModelProfiles();
    state.modelProfiles = data.profiles || [];
    state.defaultModelProfileId = data.default_profile_id || "";
    renderModelProfileList();
    modelProfileStatusEl.textContent = "已加载模型 Profile。";
  } catch (error) {
    state.modelProfiles = [];
    state.defaultModelProfileId = "";
    renderModelProfileList();
    setInlineErrorStatus(modelProfileStatusEl, error);
  }
}

function renderModelProfileList() {
  modelProfileListEl.innerHTML = "";
  updateCurrentModelProfileLabel();
  if (state.modelProfiles.length === 0) {
    appendModelProfileLine("暂无模型 Profile，可保存当前常用模型配置。");
    return;
  }
  for (const profile of state.modelProfiles) {
    const item = document.createElement("li");
    const title = document.createElement("strong");
    title.textContent = profile.id === state.defaultModelProfileId ? `${profile.name}（默认）` : profile.name;
    const desc = document.createElement("span");
    const keyText = profile.has_api_key ? `Key：${profile.api_key_source || "已配置"}` : "Key：未配置";
    desc.textContent = `${profile.provider} / ${profile.api_base || "无 API 地址"} / ${profile.model} / ${keyText}`;
    const actions = document.createElement("div");
    actions.className = "project-actions compact";
    const editButton = document.createElement("button");
    editButton.type = "button";
    editButton.textContent = "编辑";
    editButton.addEventListener("click", () => editModelProfile(profile));
    const defaultButton = document.createElement("button");
    defaultButton.type = "button";
    defaultButton.textContent = "设为默认";
    defaultButton.addEventListener("click", () => updateDefaultModelProfile(profile.id));
    const testButton = document.createElement("button");
    testButton.type = "button";
    testButton.textContent = "测试";
    testButton.addEventListener("click", () => runModelProfileTest(profile.id));
    const deleteButton = document.createElement("button");
    deleteButton.type = "button";
    deleteButton.textContent = "删除";
    deleteButton.addEventListener("click", () => removeModelProfile(profile.id));
    actions.append(editButton, defaultButton, testButton, deleteButton);
    item.append(title, desc, actions);
    modelProfileListEl.appendChild(item);
  }
}

function appendModelProfileLine(text) {
  const item = document.createElement("li");
  item.textContent = text;
  modelProfileListEl.appendChild(item);
}

function updateCurrentModelProfileLabel() {
  const profile = state.modelProfiles.find((entry) => entry.id === state.defaultModelProfileId);
  currentModelProfileLabelEl.textContent = profile ? profile.name : "未选择";
}

function editModelProfile(profile) {
  state.editingModelProfileId = profile.id;
  modelProfileIdInput.value = profile.id;
  modelProfileNameInput.value = profile.name || "";
  modelProfileProviderSelect.value = profile.provider || "api";
  modelProfileApiBaseInput.value = profile.api_base || "";
  modelProfileModelInput.value = profile.model || "";
  modelProfileTemperatureInput.value = profile.temperature ?? 0.7;
  modelProfileMaxTokensInput.value = profile.max_tokens ?? 2048;
  modelProfileApiKeyRefSelect.value = profile.api_key_ref || "";
  modelProfileStatusEl.textContent = `正在编辑模型 Profile：${profile.name}`;
}

function resetModelProfileForm() {
  state.editingModelProfileId = "";
  modelProfileForm.reset();
  modelProfileIdInput.value = "";
  modelProfileTemperatureInput.value = 0.7;
  modelProfileMaxTokensInput.value = 2048;
}

async function updateDefaultModelProfile(profileId) {
  try {
    await setDefaultModelProfile(profileId);
    await refreshModelProfiles();
    modelProfileStatusEl.textContent = "默认模型 Profile 已更新。";
  } catch (error) {
    setInlineErrorStatus(modelProfileStatusEl, error);
  }
}

async function runModelProfileTest(profileId) {
  try {
    modelProfileStatusEl.textContent = "正在测试模型 Profile...";
    const data = await testModelProfile(profileId);
    modelProfileStatusEl.textContent = `连接成功：${data.provider}。${data.message || ""}`;
  } catch (error) {
    setInlineErrorStatus(modelProfileStatusEl, error);
  }
}

async function removeModelProfile(profileId) {
  if (!confirm("确认删除这个模型 Profile？不会删除 API Key。")) {
    return;
  }
  try {
    await deleteModelProfile(profileId);
    resetModelProfileForm();
    await refreshModelProfiles();
    modelProfileStatusEl.textContent = "模型 Profile 已删除。";
  } catch (error) {
    setInlineErrorStatus(modelProfileStatusEl, error);
  }
}

function renderFilteredDocuments() {
  const filterText = state.documentFilter.toLowerCase();
  const documents = filterText
    ? state.documents.filter((document) => document.relative_path.toLowerCase().includes(filterText))
    : state.documents;
  const emptyMessage = state.documents.length === 0
    ? "暂无导入文件。点击“选择本机文件夹导入”开始。"
    : "没有匹配文件";
  renderDocuments(
    documentsEl,
    documents,
    previewDocument,
    removeDocument,
    state.documentCollections,
    state.selectedDocumentCollectionId,
    addDocumentToCollectionAndRefresh,
    removeDocumentFromCollectionAndRefresh,
    emptyMessage,
  );
  renderDocumentCount(documentCountEl, documents.length, state.documents.length);
}

function renderSelectedProjectRoot() {
  const project = state.projects.find((entry) => entry.id === state.selectedProjectId);
  renderProjectRoot(projectRootEl, project);
}

async function selectDocumentCollection(collectionId) {
  state.selectedDocumentCollectionId = collectionId;
  await refreshDocuments();
  renderDocumentCollections(
    documentCollectionsEl,
    documentCollectionFilterEl,
    state.documentCollections,
    state.selectedDocumentCollectionId,
    selectDocumentCollection,
    removeDocumentCollection,
  );
}

async function removeDocumentCollection(collectionId) {
  if (!confirm("确认删除这个文档集合？集合内文档不会被删除。")) {
    return;
  }
  try {
    setStatus("正在删除文档集合...");
    await deleteDocumentCollection(collectionId);
    if (state.selectedDocumentCollectionId === collectionId) {
      state.selectedDocumentCollectionId = "";
    }
    await refreshDocumentCollections();
    await refreshDocuments();
    setStatus("文档集合已删除，文档记录已保留。");
  } catch (error) {
    setErrorStatus(error);
  }
}

async function addDocumentToCollectionAndRefresh(collectionId, documentId) {
  if (!collectionId) {
    setStatus("请先选择要加入的文档集合。");
    return;
  }
  try {
    setStatus("正在把文档加入集合...");
    await addDocumentToCollection(collectionId, documentId);
    await refreshDocumentCollections();
    await refreshDocuments();
    setStatus("文档已加入集合。");
  } catch (error) {
    setErrorStatus(error);
  }
}

async function removeDocumentFromCollectionAndRefresh(collectionId, documentId) {
  try {
    setStatus("正在从集合移出文档...");
    await removeDocumentFromCollection(collectionId, documentId);
    await refreshDocumentCollections();
    await refreshDocuments();
    setStatus("文档已从集合移出。");
  } catch (error) {
    setErrorStatus(error);
  }
}

async function removeDocument(documentId) {
  if (!confirm("确认从当前项目空间移除这个文档记录？源文件不会被删除。")) {
    return;
  }
  try {
    setStatus("正在移除文档记录...");
    const data = await deleteDocument(documentId);
    state.documents = data.documents;
    await refreshDocumentCollections();
    await refreshProjectSummary();
    renderFilteredDocuments();
    renderDocumentPreview(documentPreviewEl, null);
    renderSearchResults(searchResultsEl, [], previewDocument);
    clearSearchDebug();
    setStatus("文档记录已移除。");
  } catch (error) {
    setErrorStatus(error);
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
    setErrorStatus(error);
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

async function withBusyButton(button, busyText, action) {
  const originalText = button.textContent;
  button.disabled = true;
  button.textContent = busyText;
  try {
    return await action();
  } finally {
    button.disabled = false;
    button.textContent = originalText;
  }
}

refreshProjects(projectSelect)
  .then(() => {
    renderSelectedProjectRoot();
    refreshProjectSummary();
    refreshAgentTools().catch((error) => setInlineErrorStatus(agentToolRunDetailEl, error));
    renderAssessmentOverview(assessmentOverviewEl, null);
    loadLlmSettings()
      .then((data) => renderLlmSettings(data.settings))
      .catch((error) => {
        setInlineErrorStatus(llmSettingsStatusEl, error);
      });
    refreshModelProfiles().catch((error) => setInlineErrorStatus(modelProfileStatusEl, error));
    return refreshDocumentCollections();
  })
  .then(() => refreshDocuments())
  .then(() => refreshImportBatches())
  .then(() => refreshRetrievalSettings())
  .then(() => refreshPromptPresets())
  .then(() => refreshChatSessions())
  .then(() => refreshChatHistory())
  .then(() => refreshAgentToolRuns())
  .then(() => refreshRetrievalReviews())
  .catch((error) => setErrorStatus(error));

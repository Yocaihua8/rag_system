import {
  createProject,
  deleteDocument,
  deleteSelectedProject,
  getDocument,
  getProjectSummary,
  importBrowserFolder,
  importBrowserFiles,
  importPlainTextNote,
  importUrlExcerpt,
  importSelectedProject,
  listDocuments,
  refreshProjects,
  renameSelectedProject,
  selectProject,
} from "./projects.js";
import { getAgentToolRunDetail, listAgentToolRuns, listAgentTools, runAgentTool } from "./agent.js";
import {
  ask,
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
import { loadLlmSettings, saveLlmSettings, testLlmSettings } from "./settings.js";
import { apiGet, apiPost } from "./api.js";
import { state } from "./state.js";
import {
  renderAnswer,
  renderDocumentCount,
  renderDocumentPreview,
  renderDocuments,
  renderImportErrors,
  renderProjectHealthError,
  renderProjectHealthStatus,
  renderProjectHealthSummary,
  renderProjectRoot,
  renderAssessmentQuestion,
  renderAssessmentResult,
  renderAssessmentOverview,
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
const documentCountEl = document.querySelector("#document-count");
const documentPreviewEl = document.querySelector("#document-preview");
const searchResultsEl = document.querySelector("#search-results");
const searchDebugResultsEl = document.querySelector("#search-debug-results");
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
const llmSaveButton = llmSettingsForm.querySelector('button[type="submit"]');
const llmTestButton = document.querySelector("#llm-test-button");
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

for (const button of viewNavButtons) {
  button.addEventListener("click", () => showView(button.dataset.viewTarget));
}

showView("workbench-view");

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
  await refreshDocuments();
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
    state.documents = [];
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
      renderFilteredDocuments();
      renderDocumentPreview(documentPreviewEl, null);
      renderSearchResults(searchResultsEl, [], previewDocument);
      clearSearchDebug();
      renderSkippedDetails(skippedDetailsEl, data.result.skipped_details);
      renderImportErrors(importErrorsEl, data.result.errors);
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
      renderFilteredDocuments();
      renderDocumentPreview(documentPreviewEl, null);
      renderSearchResults(searchResultsEl, [], previewDocument);
      clearSearchDebug();
      renderSkippedDetails(skippedDetailsEl, data.result.skipped_details);
      renderImportErrors(importErrorsEl, data.result.errors);
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
    await refreshDocuments();
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
  await withBusyButton(askButton, "提问中...", async () => {
    try {
      setStatus("正在检索资料...");
      const data = await ask(question);
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
      setErrorStatus(error);
    }
  });
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
      state.assessmentSession = data.session;
      state.assessmentQuestion = data.session.questions[0] || null;
      assessmentAnswerInput.value = "";
      renderAssessmentQuestion(assessmentQuestionEl, state.assessmentQuestion);
      renderAssessmentResult(assessmentResultEl, null);
      renderAssessmentOverview(assessmentOverviewEl, null);
      setStatus("评估题已生成。");
    } catch (error) {
      setErrorStatus(error);
    }
  });
});

assessmentAnswerButton.addEventListener("click", async () => {
  const answer = assessmentAnswerInput.value.trim();
  if (!answer) {
    setStatus("请输入评估回答。");
    return;
  }
  await withBusyButton(assessmentAnswerButton, "评估中...", async () => {
    try {
      setStatus("正在评估回答...");
      const data = await submitAssessmentAnswer(answer);
      renderAssessmentResult(assessmentResultEl, data.result);
      renderAssessmentOverview(assessmentOverviewEl, data.result);
      setStatus("评估反馈已生成。");
    } catch (error) {
      setErrorStatus(error);
    }
  });
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

async function refreshDocuments() {
  const data = await listDocuments();
  state.documents = data.documents;
  renderFilteredDocuments();
  renderDocumentPreview(documentPreviewEl, null);
  renderSearchResults(searchResultsEl, [], previewDocument);
  clearSearchDebug();
  renderSkippedDetails(skippedDetailsEl, []);
  renderImportErrors(importErrorsEl, []);
  state.assessmentSession = null;
  state.assessmentQuestion = null;
  renderAssessmentQuestion(assessmentQuestionEl, null);
  renderAssessmentResult(assessmentResultEl, null);
  renderAssessmentOverview(assessmentOverviewEl, null);
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

function renderFilteredDocuments() {
  const filterText = state.documentFilter.toLowerCase();
  const documents = filterText
    ? state.documents.filter((document) => document.relative_path.toLowerCase().includes(filterText))
    : state.documents;
  const emptyMessage = state.documents.length === 0
    ? "暂无导入文件。点击“选择本机文件夹导入”开始。"
    : "没有匹配文件";
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
    return refreshDocuments();
  })
  .then(() => refreshRetrievalSettings())
  .then(() => refreshPromptPresets())
  .then(() => refreshChatSessions())
  .then(() => refreshChatHistory())
  .then(() => refreshAgentToolRuns())
  .then(() => refreshRetrievalReviews())
  .catch((error) => setErrorStatus(error));

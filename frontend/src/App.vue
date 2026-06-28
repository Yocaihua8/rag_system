<template>
  <AppShell :current-view="appState.currentView" @change-view="showView">
    <component
      :is="currentViewComponent"
      :status-message="statusMessage"
      :projects="appState.projects"
      :selected-project-id="appState.selectedProjectId"
      :projects-loading="appState.projectsLoading"
      :project-load-error="appState.projectLoadError"
      :project-form-submitting="appState.projectFormSubmitting"
      :project-form-error="appState.projectFormError"
      :project-form-status="projectFormStatus"
      :project-rename-submitting="appState.projectRenameSubmitting"
      :project-delete-submitting="appState.projectDeleteSubmitting"
      :project-mutation-error="appState.projectMutationError"
      :project-mutation-status="appState.projectMutationStatus"
      :project-status-message="projectStatusMessage"
      :first-run-visible="firstRunWizardVisible"
      :ollama-status="appState.ollamaStatus"
      :ollama-status-loading="appState.ollamaStatusLoading"
      :ollama-status-error="appState.ollamaStatusError"
      :ollama-pulling-model="appState.ollamaPullingModel"
      :ollama-pull-progress="appState.ollamaPullProgress"
      :ollama-pull-status="appState.ollamaPullStatus"
      :ollama-pull-error="appState.ollamaPullError"
      :import-submitting="appState.importSubmitting"
      :import-error="appState.importError"
      :import-status="appState.importStatus"
      :import-preview="appState.importPreview"
      :import-preview-loading="appState.importPreviewLoading"
      :import-preview-error="appState.importPreviewError"
      :answer-result="appState.answerResult"
      :answer-loading="appState.answerLoading"
      :answer-error="appState.answerError"
      :answer-status="appState.answerStatus"
      :last-answer-message-id="appState.lastAnswerMessageId"
      :answer-feedback-submitting="appState.answerFeedbackSubmitting"
      :answer-feedback-status="appState.answerFeedbackStatus"
      :answer-feedback-error="appState.answerFeedbackError"
      :current-tool-suggestion="appState.currentToolSuggestion"
      :last-usable-tool-run="appState.lastUsableToolRun"
      :current-tool-context-run-id="appState.currentToolContextRunId"
      :search-debug-result="appState.searchDebugResult"
      :search-debug-loading="appState.searchDebugLoading"
      :search-debug-error="appState.searchDebugError"
      :search-debug-status="appState.searchDebugStatus"
      :retrieval-settings="appState.retrievalSettings"
      :retrieval-settings-loading="appState.retrievalSettingsLoading"
      :retrieval-settings-saving="appState.retrievalSettingsSaving"
      :retrieval-settings-status="appState.retrievalSettingsStatus"
      :retrieval-settings-error="appState.retrievalSettingsError"
      :retrieval-reviews="appState.retrievalReviews"
      :retrieval-reviews-loading="appState.retrievalReviewsLoading"
      :retrieval-reviews-error="appState.retrievalReviewsError"
      :retrieval-review-saving="appState.retrievalReviewSaving"
      :retrieval-review-error="appState.retrievalReviewError"
      :retrieval-review-status="appState.retrievalReviewStatus"
      :selected-retrieval-review="appState.selectedRetrievalReview"
      :retrieval-review-detail-loading="appState.retrievalReviewDetailLoading"
      :retrieval-review-detail-error="appState.retrievalReviewDetailError"
      :deleting-retrieval-review-id="appState.deletingRetrievalReviewId"
      :agent-tools="appState.agentTools"
      :agent-tools-loading="appState.agentToolsLoading"
      :agent-tools-error="appState.agentToolsError"
      :agent-tool-runs="appState.agentToolRuns"
      :agent-tool-runs-loading="appState.agentToolRunsLoading"
      :agent-tool-runs-error="appState.agentToolRunsError"
      :selected-agent-tool-run="appState.selectedAgentToolRun"
      :agent-tool-result="appState.agentToolResult"
      :agent-tool-status="appState.agentToolStatus"
      :agent-tool-error="appState.agentToolError"
      :agent-tool-submitting-name="appState.agentToolSubmittingName"
      :agent-tool-detail-loading="appState.agentToolDetailLoading"
      :agent-tool-detail-error="appState.agentToolDetailError"
      :documents="appState.documents"
      :documents-loading="appState.documentsLoading"
      :documents-load-error="appState.documentsLoadError"
      :document-collections="appState.documentCollections"
      :selected-document-collection-id="appState.selectedDocumentCollectionId"
      :document-collections-loading="appState.documentCollectionsLoading"
      :document-collections-load-error="appState.documentCollectionsLoadError"
      :collection-form-submitting="appState.collectionFormSubmitting"
      :collection-form-error="appState.collectionFormError"
      :collection-form-status="appState.collectionFormStatus"
      :collection-rename-submitting="appState.collectionRenameSubmitting"
      :collection-rename-error="appState.collectionRenameError"
      :collection-rename-status="appState.collectionRenameStatus"
      :deleting-collection-id="appState.deletingCollectionId"
      :collection-item-submitting-id="appState.collectionItemSubmittingId"
      :collection-item-error="appState.collectionItemError"
      :collection-item-status="appState.collectionItemStatus"
      :deleting-document-id="appState.deletingDocumentId"
      :document-delete-error="appState.documentDeleteError"
      :document-delete-status="appState.documentDeleteStatus"
      :selected-document-id="appState.selectedDocumentId"
      :selected-document="appState.selectedDocument"
      :document-preview-loading="appState.documentPreviewLoading"
      :document-preview-error="appState.documentPreviewError"
      :import-batches="appState.importBatches"
      :import-batches-loading="appState.importBatchesLoading"
      :import-batches-load-error="appState.importBatchesLoadError"
      :selected-import-batch="appState.selectedImportBatch"
      :selected-import-batch-items="appState.selectedImportBatchItems"
      :import-batch-detail-loading="appState.importBatchDetailLoading"
      :import-batch-detail-error="appState.importBatchDetailError"
      :llm-settings="appState.llmSettings"
      :llm-settings-loading="appState.llmSettingsLoading"
      :llm-settings-submitting="appState.llmSettingsSubmitting"
      :llm-settings-testing="appState.llmSettingsTesting"
      :llm-settings-error="appState.llmSettingsError"
      :llm-settings-status="appState.llmSettingsStatus"
      :model-profiles="appState.modelProfiles"
      :default-model-profile-id="appState.defaultModelProfileId"
      :model-profiles-loading="appState.modelProfilesLoading"
      :model-profile-load-error="appState.modelProfileLoadError"
      :model-profile-submitting="appState.modelProfileSubmitting"
      :model-profile-testing-id="appState.modelProfileTestingId"
      :model-profile-deleting-id="appState.modelProfileDeletingId"
      :model-profile-default-submitting="appState.modelProfileDefaultSubmitting"
      :model-profile-mutation-error="appState.modelProfileMutationError"
      :model-profile-status="appState.modelProfileStatus"
      :prompt-presets="appState.promptPresets"
      :prompt-preset-templates="appState.promptPresetTemplates"
      :selected-prompt-preset-id="appState.selectedPromptPresetId"
      :prompt-presets-loading="appState.promptPresetsLoading"
      :prompt-preset-load-error="appState.promptPresetLoadError"
      :prompt-preset-submitting="appState.promptPresetSubmitting"
      :prompt-preset-deleting-id="appState.promptPresetDeletingId"
      :prompt-preset-default-submitting="appState.promptPresetDefaultSubmitting"
      :prompt-preset-mutation-error="appState.promptPresetMutationError"
      :prompt-preset-status="appState.promptPresetStatus"
      :assessment-session="appState.assessmentSession"
      :assessment-question="appState.assessmentQuestion"
      :assessment-question-index="appState.assessmentQuestionIndex"
      :assessment-results="appState.assessmentResults"
      :assessment-missed-questions="appState.assessmentMissedQuestions"
      :assessment-answered-current="appState.assessmentAnsweredCurrent"
      :assessment-loading="appState.assessmentLoading"
      :assessment-submitting="appState.assessmentSubmitting"
      :assessment-error="appState.assessmentError"
      :assessment-status="appState.assessmentStatus"
      @check-health="checkHealth"
      @refresh-projects="loadProjectSpaces"
      @select-project="handleSelectProject"
      @create-project="handleCreateProject"
      @rename-project="handleRenameProject"
      @delete-project="handleDeleteProject"
      @submit-question="handleSubmitQuestion"
      @refresh-ollama-status="loadOllamaStatus"
      @pull-ollama-model="handlePullOllamaModel"
      @dismiss-first-run="dismissFirstRunWizard"
      @submit-answer-feedback="handleSubmitAnswerFeedback"
      @run-tool-suggestion="handleRunToolSuggestion"
      @use-tool-result-context="handleUseToolResultContext"
      @clear-tool-context="clearToolContextState"
      @run-search-debug="handleRunSearchDebug"
      @save-retrieval-settings="handleSaveRetrievalSettings"
      @save-retrieval-review="handleSaveRetrievalReview"
      @select-retrieval-review="handleSelectRetrievalReview"
      @delete-retrieval-review="handleDeleteRetrievalReview"
      @load-agent-tools="loadAgentTools"
      @run-agent-tool="handleRunAgentTool"
      @load-agent-tool-runs="loadAgentToolRuns"
      @select-agent-tool-run="handleSelectAgentToolRun"
      @refresh-documents="loadLibraryDocuments"
      @select-document="handleSelectDocument"
      @refresh-collections="loadDocumentCollections"
      @select-collection="handleSelectDocumentCollection"
      @create-collection="handleCreateDocumentCollection"
      @delete-collection="handleDeleteDocumentCollection"
      @update-collection="handleUpdateDocumentCollection"
      @add-document-to-collection="handleAddDocumentToCollection"
      @remove-document-from-collection="handleRemoveDocumentFromCollection"
      @delete-document="handleDeleteDocument"
      @import-note="handleImportNote"
      @import-url="handleImportUrl"
      @import-files="handleImportFiles"
      @import-folder="handleImportFolder"
      @sync-directory="handleSyncDirectory"
      @preview-import="handlePreviewImport"
      @refresh-batches="loadImportBatches"
      @select-batch="handleSelectImportBatch"
      @load-settings="loadSettingsPage"
      @save-llm-settings="handleSaveLlmSettings"
      @test-llm-settings="handleTestLlmSettings"
      @load-model-profiles="loadModelProfiles"
      @save-model-profile="handleSaveModelProfile"
      @delete-model-profile="handleDeleteModelProfile"
      @set-default-model-profile="handleSetDefaultModelProfile"
      @test-model-profile="handleTestModelProfile"
      @load-prompt-presets="loadPromptPresets"
      @save-prompt-preset="handleSavePromptPreset"
      @delete-prompt-preset="handleDeletePromptPreset"
      @set-default-prompt-preset="handleSetDefaultPromptPreset"
      @start-assessment="handleStartAssessment"
      @submit-assessment-answer="handleSubmitAssessmentAnswer"
      @next-assessment-question="handleNextAssessmentQuestion"
      @reset-assessment="resetAssessmentState"
    />
  </AppShell>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";

import {
  getAgentToolRunDetail,
  listAgentToolRuns,
  listAgentTools,
  runAgentTool,
} from "./api/agent.js";
import { askQuestion, submitAnswerFeedback } from "./api/answer.js";
import { startAssessmentSession, submitAssessmentAnswer } from "./api/assessment.js";
import { apiGet } from "./api/client.js";
import { getOllamaStatus, pullOllamaModel } from "./api/ollama.js";
import {
  addDocumentToCollection,
  createDocumentCollection,
  deleteDocumentCollection,
  listDocumentCollections,
  removeDocumentFromCollection,
  updateDocumentCollection,
} from "./api/document-collections.js";
import { deleteDocument, getDocument, listDocuments } from "./api/documents.js";
import {
  getImportBatchDetail,
  importBrowserFolder,
  importBrowserFiles,
  importPlainTextNote,
  importUrlExcerpt,
  listImportBatches,
  previewProjectImport,
  syncProjectDirectory,
} from "./api/imports.js";
import {
  createProject,
  deleteProject,
  getRetrievalSettings,
  loadProjects,
  renameProject,
  restoreSelectedProjectId,
  saveRetrievalSettings,
  selectProject,
} from "./api/projects.js";
import {
  deleteModelProfile,
  deletePromptPreset,
  listModelProfiles,
  listPromptPresets,
  loadLlmSettings,
  saveLlmSettings,
  saveModelProfile,
  savePromptPreset,
  setDefaultModelProfile,
  setDefaultPromptPreset,
  testLlmSettings,
  testModelProfile,
} from "./api/settings.js";
import {
  deleteRetrievalReview,
  getRetrievalReviewDetail,
  listRetrievalReviews,
  runSearchDebug,
  saveRetrievalReview,
} from "./api/search.js";
import AppShell from "./components/AppShell.vue";
import { appState, showView } from "./state/app-state.js";
import AssessmentView from "./views/AssessmentView.vue";
import LibraryView from "./views/LibraryView.vue";
import SettingsView from "./views/SettingsView.vue";
import WorkbenchView from "./views/WorkbenchView.vue";

const viewComponents = {
  workbench: WorkbenchView,
  library: LibraryView,
  assessment: AssessmentView,
  settings: SettingsView,
};

const statusMessage = ref("等待检查");
const projectFormStatus = ref("");

const currentViewComponent = computed(() => {
  return viewComponents[appState.currentView] || WorkbenchView;
});

const projectStatusMessage = computed(() => {
  if (appState.projectsLoading) {
    return "正在读取项目空间...";
  }
  if (appState.projectLoadError) {
    return appState.projectLoadError;
  }
  if (!appState.selectedProjectId) {
    return "未选择项目空间";
  }
  const selectedProject = appState.projects.find((project) => project.id === appState.selectedProjectId);
  return selectedProject ? `当前项目：${selectedProject.name}` : "未选择项目空间";
});

const firstRunWizardVisible = computed(() => {
  if (appState.firstRunWizardDismissed) {
    return false;
  }
  if (!appState.selectedProjectId) {
    return true;
  }
  if (!appState.ollamaStatus) {
    return true;
  }
  return appState.ollamaStatus.available === false || (appState.ollamaStatus.models || []).length === 0;
});

onMounted(() => {
  loadOllamaStatus();
  loadProjectSpaces();
  loadSettingsPage();
  loadAgentTools();
});

async function checkHealth() {
  statusMessage.value = "检查中...";
  try {
    const data = await apiGet("/api/health");
    statusMessage.value = data.status === "ok" ? "本地服务正常" : "服务状态异常";
  } catch (error) {
    statusMessage.value = "本地服务暂时不可用";
  }
}

async function loadOllamaStatus() {
  appState.ollamaStatusLoading = true;
  appState.ollamaStatusError = "";
  try {
    const data = await getOllamaStatus();
    appState.ollamaStatus = data;
    appState.ollamaStatusError = data.available ? "" : data.error || "Ollama 不可用";
  } catch (error) {
    appState.ollamaStatus = null;
    appState.ollamaStatusError = error.message || "Ollama 检测失败";
  } finally {
    appState.ollamaStatusLoading = false;
  }
}

async function handlePullOllamaModel(model) {
  appState.ollamaPullingModel = model;
  appState.ollamaPullProgress = null;
  appState.ollamaPullStatus = `正在下载模型：${model}`;
  appState.ollamaPullError = "";
  try {
    await pullOllamaModel({
      model,
      handlers: {
        onProgress(data) {
          appState.ollamaPullProgress = data;
          appState.ollamaPullStatus = formatOllamaPullStatus(data);
        },
        onDone(data) {
          appState.ollamaPullProgress = data;
          appState.ollamaPullStatus = "模型下载完成";
        },
        onError(data) {
          appState.ollamaPullError = data.error || "模型下载失败";
        },
      },
    });
    await loadOllamaStatus();
  } catch (error) {
    appState.ollamaPullError = error.message || "模型下载失败";
    appState.ollamaPullStatus = "模型下载失败";
  } finally {
    appState.ollamaPullingModel = "";
  }
}

function dismissFirstRunWizard() {
  appState.firstRunWizardDismissed = true;
}

function formatOllamaPullStatus(data) {
  if (typeof data.progress === "number") {
    return `${data.status || "下载中"}：${Math.round(data.progress * 100)}%`;
  }
  return data.status || "正在下载模型";
}

async function loadSettingsPage() {
  await Promise.all([loadModelSettings(), loadModelProfiles(), loadPromptPresets()]);
}

async function loadModelSettings() {
  appState.llmSettingsLoading = true;
  appState.llmSettingsError = "";
  try {
    appState.llmSettings = await loadLlmSettings();
    appState.llmSettingsStatus = formatLlmSettingsStatus(appState.llmSettings);
  } catch (error) {
    appState.llmSettingsError = error.message || "模型设置读取失败";
  } finally {
    appState.llmSettingsLoading = false;
  }
}

async function handleSaveLlmSettings(payload) {
  appState.llmSettingsSubmitting = true;
  appState.llmSettingsError = "";
  appState.llmSettingsStatus = "";
  try {
    appState.llmSettings = await saveLlmSettings(payload);
    appState.llmSettingsStatus = "模型设置已保存";
  } catch (error) {
    appState.llmSettingsError = error.message || "模型设置保存失败";
  } finally {
    appState.llmSettingsSubmitting = false;
  }
}

async function handleTestLlmSettings() {
  appState.llmSettingsTesting = true;
  appState.llmSettingsError = "";
  appState.llmSettingsStatus = "";
  try {
    const data = await testLlmSettings();
    appState.llmSettingsStatus = data.message || "模型连接测试通过";
  } catch (error) {
    appState.llmSettingsError = error.message || "模型连接测试失败";
  } finally {
    appState.llmSettingsTesting = false;
  }
}

async function loadModelProfiles() {
  appState.modelProfilesLoading = true;
  appState.modelProfileLoadError = "";
  try {
    const data = await listModelProfiles();
    appState.modelProfiles = data.profiles || [];
    appState.defaultModelProfileId = data.default_profile_id || "";
  } catch (error) {
    appState.modelProfileLoadError = error.message || "模型 Profile 读取失败";
  } finally {
    appState.modelProfilesLoading = false;
  }
}

async function handleSaveModelProfile(payload) {
  appState.modelProfileSubmitting = true;
  appState.modelProfileMutationError = "";
  appState.modelProfileStatus = "";
  try {
    await saveModelProfile(payload);
    appState.modelProfileStatus = "模型 Profile 已保存";
    await loadModelProfiles();
  } catch (error) {
    appState.modelProfileMutationError = error.message || "模型 Profile 保存失败";
  } finally {
    appState.modelProfileSubmitting = false;
  }
}

async function handleDeleteModelProfile(profileId) {
  if (!window.confirm("确认删除这个模型 Profile？不会删除 API Key。")) {
    return;
  }
  appState.modelProfileDeletingId = profileId;
  appState.modelProfileMutationError = "";
  appState.modelProfileStatus = "";
  try {
    await deleteModelProfile(profileId);
    appState.modelProfileStatus = "模型 Profile 已删除";
    await loadModelProfiles();
  } catch (error) {
    appState.modelProfileMutationError = error.message || "模型 Profile 删除失败";
  } finally {
    appState.modelProfileDeletingId = "";
  }
}

async function handleSetDefaultModelProfile(profileId) {
  appState.modelProfileDefaultSubmitting = true;
  appState.modelProfileMutationError = "";
  appState.modelProfileStatus = "";
  try {
    const data = await setDefaultModelProfile(profileId);
    appState.defaultModelProfileId = data.default_profile_id || "";
    appState.modelProfileStatus = "默认模型 Profile 已更新";
  } catch (error) {
    appState.modelProfileMutationError = error.message || "默认模型 Profile 更新失败";
  } finally {
    appState.modelProfileDefaultSubmitting = false;
  }
}

async function handleTestModelProfile(profileId) {
  appState.modelProfileTestingId = profileId;
  appState.modelProfileMutationError = "";
  appState.modelProfileStatus = "";
  try {
    const data = await testModelProfile(profileId);
    appState.modelProfileStatus = data.message || "模型 Profile 测试通过";
  } catch (error) {
    appState.modelProfileMutationError = error.message || "模型 Profile 测试失败";
  } finally {
    appState.modelProfileTestingId = "";
  }
}

async function loadPromptPresets() {
  if (!appState.selectedProjectId) {
    clearPromptPresetState();
    appState.promptPresetStatus = "请选择项目空间后管理 Prompt 预设";
    return;
  }

  appState.promptPresetsLoading = true;
  appState.promptPresetLoadError = "";
  try {
    const data = await listPromptPresets(appState.selectedProjectId);
    appState.promptPresets = data.presets || [];
    appState.promptPresetTemplates = data.templates || [];
    appState.selectedPromptPresetId = data.default_preset_id || "";
    appState.promptPresetStatus = "已加载当前项目 Prompt 预设";
  } catch (error) {
    appState.promptPresets = [];
    appState.promptPresetTemplates = [];
    appState.selectedPromptPresetId = "";
    appState.promptPresetLoadError = error.message || "Prompt 预设读取失败";
  } finally {
    appState.promptPresetsLoading = false;
  }
}

async function handleSavePromptPreset(payload) {
  appState.promptPresetSubmitting = true;
  appState.promptPresetMutationError = "";
  appState.promptPresetStatus = "";
  try {
    await savePromptPreset({
      ...payload,
      projectId: appState.selectedProjectId,
    });
    await loadPromptPresets();
    appState.promptPresetStatus = "Prompt 预设已保存";
  } catch (error) {
    appState.promptPresetMutationError = error.message || "Prompt 预设保存失败";
  } finally {
    appState.promptPresetSubmitting = false;
  }
}

async function handleDeletePromptPreset(presetId) {
  if (!window.confirm("确认删除这个 Prompt 预设？")) {
    return;
  }
  appState.promptPresetDeletingId = presetId;
  appState.promptPresetMutationError = "";
  appState.promptPresetStatus = "";
  try {
    await deletePromptPreset(presetId);
    await loadPromptPresets();
    appState.promptPresetStatus = "Prompt 预设已删除";
  } catch (error) {
    appState.promptPresetMutationError = error.message || "Prompt 预设删除失败";
  } finally {
    appState.promptPresetDeletingId = "";
  }
}

async function handleSetDefaultPromptPreset(presetId) {
  appState.promptPresetDefaultSubmitting = true;
  appState.promptPresetMutationError = "";
  appState.promptPresetStatus = "";
  try {
    const data = await setDefaultPromptPreset({
      projectId: appState.selectedProjectId,
      presetId,
    });
    appState.selectedPromptPresetId = data.default_preset_id || "";
    await loadPromptPresets();
    appState.promptPresetStatus = "默认 Prompt 预设已更新";
  } catch (error) {
    appState.promptPresetMutationError = error.message || "默认 Prompt 预设更新失败";
  } finally {
    appState.promptPresetDefaultSubmitting = false;
  }
}

async function handleStartAssessment() {
  appState.assessmentLoading = true;
  appState.assessmentError = "";
  appState.assessmentStatus = "正在生成评估题...";
  try {
    const data = await startAssessmentSession(appState.selectedProjectId);
    appState.assessmentSession = data.session;
    appState.assessmentQuestionIndex = 0;
    appState.assessmentResults = [];
    appState.assessmentMissedQuestions = [];
    appState.assessmentAnsweredCurrent = false;
    appState.assessmentQuestion = currentAssessmentQuestion();
    appState.assessmentStatus = "评估题已生成";
  } catch (error) {
    appState.assessmentError = error.message || "评估题生成失败";
    appState.assessmentStatus = "评估题生成失败";
  } finally {
    appState.assessmentLoading = false;
  }
}

async function handleSubmitAssessmentAnswer(answer) {
  appState.assessmentSubmitting = true;
  appState.assessmentError = "";
  appState.assessmentStatus = "正在评估回答...";
  try {
    const data = await submitAssessmentAnswer({
      projectId: appState.selectedProjectId,
      question: appState.assessmentQuestion,
      answer,
    });
    const entry = {
      question: appState.assessmentQuestion,
      result: data.result,
    };
    appState.assessmentResults = [...appState.assessmentResults, entry];
    appState.assessmentMissedQuestions = appState.assessmentResults.filter((item) => item.result?.status !== "已掌握");
    appState.assessmentAnsweredCurrent = true;
    appState.assessmentStatus = "评估反馈已生成";
  } catch (error) {
    appState.assessmentError = error.message || "评估回答失败";
    appState.assessmentStatus = "评估回答失败";
  } finally {
    appState.assessmentSubmitting = false;
  }
}

function handleNextAssessmentQuestion() {
  if (!appState.assessmentSession) {
    appState.assessmentStatus = "请先开始评估";
    return;
  }
  if (!hasNextAssessmentQuestion()) {
    appState.assessmentQuestion = null;
    appState.assessmentAnsweredCurrent = true;
    appState.assessmentStatus = "本轮评估已完成";
    return;
  }
  appState.assessmentQuestionIndex += 1;
  appState.assessmentQuestion = currentAssessmentQuestion();
  appState.assessmentAnsweredCurrent = false;
  appState.assessmentStatus = `进入第 ${appState.assessmentQuestionIndex + 1} 题`;
}

function currentAssessmentQuestion() {
  const questions = Array.isArray(appState.assessmentSession?.questions)
    ? appState.assessmentSession.questions
    : [];
  return questions[appState.assessmentQuestionIndex] || null;
}

function hasNextAssessmentQuestion() {
  const questions = Array.isArray(appState.assessmentSession?.questions)
    ? appState.assessmentSession.questions
    : [];
  return appState.assessmentQuestionIndex + 1 < questions.length;
}

function formatLlmSettingsStatus(settings = {}) {
  if (!settings.provider && !settings.model) {
    return "模型设置已读取";
  }
  const keyStatus = settings.has_api_key ? `Key ${settings.api_key_source || "已配置"}` : "Key 未配置";
  return `${settings.provider || "api"} / ${settings.model || "未填写模型"}；${keyStatus}`;
}

async function loadProjectSpaces() {
  appState.projectsLoading = true;
  appState.projectLoadError = "";
  try {
    await loadProjects();
    appState.selectedProjectId = restoreSelectedProjectId(appState.projects);
    await loadRetrievalSettings();
    await loadRetrievalReviews();
    await loadDocumentCollections();
    await loadLibraryDocuments();
    await loadImportBatches();
    await loadPromptPresets();
    await loadAgentToolRuns();
  } catch (error) {
    appState.projectLoadError = error.message || "项目空间读取失败";
  } finally {
    appState.projectsLoading = false;
  }
}

async function handleSelectProject(projectId) {
  selectProject(projectId);
  clearImportPreview();
  clearCollectionFormStatus();
  clearProjectMutationStatus();
  clearPromptPresetState();
  clearAnswerFeedbackState();
  clearSearchDebugState();
  clearRetrievalSettingsState();
  clearRetrievalReviewState();
  clearAgentToolState();
  resetAssessmentState();
  appState.selectedDocumentCollectionId = "";
  clearCollectionItemStatus();
  clearDocumentDeleteStatus();
  projectFormStatus.value = projectId ? "已切换项目空间" : "未选择项目空间";
  await loadDocumentCollections();
  await loadRetrievalSettings();
  await loadRetrievalReviews();
  await loadLibraryDocuments();
  await loadImportBatches();
  await loadPromptPresets();
  await loadAgentToolRuns();
}

async function handleCreateProject(payload) {
  appState.projectFormSubmitting = true;
  appState.projectFormError = "";
  projectFormStatus.value = "";
  try {
    const project = await createProject(payload);
    projectFormStatus.value = `已创建项目空间：${project.name}`;
    clearCollectionFormStatus();
    clearProjectMutationStatus();
    clearCollectionItemStatus();
    clearDocumentDeleteStatus();
    clearPromptPresetState();
    clearAnswerFeedbackState();
    clearSearchDebugState();
    clearRetrievalSettingsState();
    clearRetrievalReviewState();
    clearAgentToolState();
    resetAssessmentState();
    appState.selectedDocumentCollectionId = "";
    await loadDocumentCollections();
    await loadRetrievalSettings();
    await loadRetrievalReviews();
    await loadLibraryDocuments();
    await loadImportBatches();
    await loadPromptPresets();
    await loadAgentToolRuns();
  } catch (error) {
    appState.projectFormError = error.message || "项目空间创建失败";
  } finally {
    appState.projectFormSubmitting = false;
  }
}

async function handleRenameProject(name) {
  appState.projectRenameSubmitting = true;
  appState.projectMutationError = "";
  appState.projectMutationStatus = "";
  try {
    const project = await renameProject({
      projectId: appState.selectedProjectId,
      name,
    });
    selectProject(project.id);
    await loadProjectSpaces();
    appState.projectMutationStatus = "项目空间已重命名";
  } catch (error) {
    appState.projectMutationError = error.message || "项目空间重命名失败";
  } finally {
    appState.projectRenameSubmitting = false;
  }
}

async function handleDeleteProject() {
  if (!window.confirm("确认删除这个项目空间？项目内文档记录也会被删除。")) {
    return;
  }
  appState.projectDeleteSubmitting = true;
  appState.projectMutationError = "";
  appState.projectMutationStatus = "";
  try {
    await deleteProject(appState.selectedProjectId);
    selectProject("");
    resetLibraryStateAfterProjectDelete();
    await loadProjectSpaces();
    selectProject("");
    resetLibraryStateAfterProjectDelete();
    appState.projectMutationStatus = "项目空间已删除";
  } catch (error) {
    appState.projectMutationError = error.message || "项目空间删除失败";
  } finally {
    appState.projectDeleteSubmitting = false;
  }
}

function resetLibraryStateAfterProjectDelete() {
  appState.documents = [];
  appState.documentsLoadError = "";
  appState.selectedDocumentId = "";
  appState.selectedDocument = null;
  appState.documentPreviewError = "";
  appState.documentCollections = [];
  appState.documentCollectionsLoadError = "";
  appState.selectedDocumentCollectionId = "";
  appState.importBatches = [];
  appState.importBatchesLoadError = "";
  appState.selectedImportBatch = null;
  appState.selectedImportBatchItems = [];
  appState.importBatchDetailError = "";
  clearPromptPresetState();
  clearAnswerFeedbackState();
  clearSearchDebugState();
  clearRetrievalSettingsState();
  clearRetrievalReviewState();
  clearAgentToolState();
  resetAssessmentState();
  clearImportPreview();
  clearCollectionFormStatus();
  clearCollectionRenameStatus();
  clearCollectionItemStatus();
  clearDocumentDeleteStatus();
}

async function handleImportNote(payload) {
  await submitLibraryImport("文本笔记已导入", () => importPlainTextNote({
    projectId: appState.selectedProjectId,
    title: payload.title,
    content: payload.content,
  }));
}

async function handleImportUrl(payload) {
  await submitLibraryImport("URL 摘录已导入", () => importUrlExcerpt({
    projectId: appState.selectedProjectId,
    url: payload.url,
    title: payload.title,
    content: payload.content,
  }));
}

async function handleImportFiles(files) {
  appState.importSubmitting = true;
  appState.importError = "";
  appState.importStatus = "";
  clearImportPreview();
  try {
    const data = await importBrowserFiles({
      projectId: appState.selectedProjectId,
      files,
    });
    if (data.project?.id) {
      selectProject(data.project.id);
    }
    appState.documents = data.documents || [];
    appState.importStatus = formatImportResult("文件上传导入完成", data.result);
    await loadProjectSpaces();
    await loadImportBatches();
  } catch (error) {
    appState.importError = error.message || "文件上传导入失败";
  } finally {
    appState.importSubmitting = false;
  }
}

async function handleImportFolder(files) {
  appState.importSubmitting = true;
  appState.importError = "";
  appState.importStatus = "";
  clearImportPreview();
  try {
    const data = await importBrowserFolder({ files });
    if (data.project?.id) {
      selectProject(data.project.id);
    }
    appState.documents = data.documents || [];
    appState.importStatus = formatImportResult("浏览器文件夹导入完成", data.result);
    await loadProjectSpaces();
    await loadImportBatches();
  } catch (error) {
    appState.importError = error.message || "浏览器文件夹导入失败";
  } finally {
    appState.importSubmitting = false;
  }
}

async function handleSyncDirectory() {
  appState.importSubmitting = true;
  appState.importError = "";
  appState.importStatus = "";
  clearImportPreview();
  try {
    const data = await syncProjectDirectory({
      projectId: appState.selectedProjectId,
    });
    appState.documents = data.documents || [];
    appState.importStatus = formatImportResult("同步当前项目目录完成", data.result);
    await loadLibraryDocuments();
    await loadImportBatches();
  } catch (error) {
    appState.importError = error.message || "同步当前项目目录失败";
  } finally {
    appState.importSubmitting = false;
  }
}

async function handlePreviewImport() {
  appState.importPreviewLoading = true;
  appState.importPreviewError = "";
  appState.importError = "";
  appState.importStatus = "";
  try {
    const preview = await previewProjectImport({
      projectId: appState.selectedProjectId,
    });
    appState.importPreview = preview;
    appState.importStatus = formatImportPreview(preview);
  } catch (error) {
    appState.importPreviewError = error.message || "导入预检失败";
  } finally {
    appState.importPreviewLoading = false;
  }
}

async function submitLibraryImport(successMessage, action) {
  appState.importSubmitting = true;
  appState.importError = "";
  appState.importStatus = "";
  clearImportPreview();
  try {
    await action();
    appState.importStatus = successMessage;
    await loadLibraryDocuments();
    await loadImportBatches();
  } catch (error) {
    appState.importError = error.message || "资料导入失败";
  } finally {
    appState.importSubmitting = false;
  }
}

function formatImportResult(label, result = {}) {
  return `${label}：新增 ${result.created ?? 0}，更新 ${result.updated ?? 0}，未变更 ${result.unchanged ?? 0}，删除 ${result.deleted ?? 0}，跳过 ${result.skipped ?? 0}`;
}

function formatImportPreview(preview = {}) {
  return `导入预检完成：可导入 ${preview?.importable ?? 0}，跳过 ${preview?.skipped ?? 0}`;
}

function clearImportPreview() {
  appState.importPreview = null;
  appState.importPreviewError = "";
}

function clearAnswerFeedbackState() {
  appState.lastAnswerMessageId = "";
  appState.answerFeedbackSubmitting = false;
  appState.answerFeedbackError = "";
  appState.answerFeedbackStatus = "";
}

function clearSearchDebugState() {
  appState.searchDebugResult = null;
  appState.searchDebugLoading = false;
  appState.searchDebugError = "";
  appState.searchDebugStatus = "";
}

function clearRetrievalSettingsState() {
  appState.retrievalSettings = null;
  appState.retrievalSettingsLoading = false;
  appState.retrievalSettingsSaving = false;
  appState.retrievalSettingsError = "";
  appState.retrievalSettingsStatus = "";
}

function clearRetrievalReviewState() {
  appState.retrievalReviews = [];
  appState.retrievalReviewsLoading = false;
  appState.retrievalReviewsError = "";
  appState.retrievalReviewSaving = false;
  appState.retrievalReviewError = "";
  appState.retrievalReviewStatus = "";
  appState.selectedRetrievalReview = null;
  appState.retrievalReviewDetailLoading = false;
  appState.retrievalReviewDetailError = "";
  appState.deletingRetrievalReviewId = "";
}

function clearAgentToolState() {
  appState.agentToolRuns = [];
  appState.agentToolRunsError = "";
  appState.selectedAgentToolRun = null;
  appState.agentToolSubmittingName = "";
  appState.agentToolResult = null;
  appState.agentToolStatus = "";
  appState.agentToolError = "";
  appState.agentToolDetailLoading = false;
  appState.agentToolDetailError = "";
  clearToolSuggestionState();
  clearToolContextState();
  appState.lastUsableToolRun = null;
}

function clearToolSuggestionState() {
  appState.currentToolSuggestion = null;
}

function clearToolContextState() {
  appState.currentToolContextRunId = "";
}

function consumeToolContext() {
  appState.currentToolContextRunId = "";
}

function setLastUsableToolRun(data) {
  if (data.run?.tool_name === "search_sources" && data.run.status === "success") {
    appState.lastUsableToolRun = data.run;
    return;
  }
  appState.lastUsableToolRun = null;
}

async function loadAgentTools() {
  appState.agentToolsLoading = true;
  appState.agentToolsError = "";
  try {
    const tools = await listAgentTools();
    appState.agentTools = tools;
  } catch (error) {
    appState.agentTools = [];
    appState.agentToolsError = error.message || "Agent 工具读取失败";
  } finally {
    appState.agentToolsLoading = false;
  }
}

async function loadAgentToolRuns() {
  appState.agentToolRuns = [];
  appState.agentToolRunsError = "";
  appState.selectedAgentToolRun = null;
  if (!appState.selectedProjectId) {
    return;
  }

  appState.agentToolRunsLoading = true;
  try {
    const runs = await listAgentToolRuns(appState.selectedProjectId);
    appState.agentToolRuns = runs;
  } catch (error) {
    appState.agentToolRunsError = error.message || "工具运行历史读取失败";
  } finally {
    appState.agentToolRunsLoading = false;
  }
}

async function handleRunAgentTool(payload) {
  appState.agentToolSubmittingName = payload.toolName;
  appState.agentToolError = "";
  appState.agentToolStatus = "正在运行只读工具...";
  appState.selectedAgentToolRun = null;
  try {
    const data = await runAgentTool({
      projectId: appState.selectedProjectId,
      toolName: payload.toolName,
      argumentsPayload: payload.argumentsPayload || {},
    });
    appState.agentToolResult = data;
    setLastUsableToolRun(data);
    appState.agentToolStatus = "工具运行完成";
    await loadAgentToolRuns();
  } catch (error) {
    appState.agentToolError = error.message || "工具运行失败";
    appState.agentToolStatus = "工具运行失败";
  } finally {
    appState.agentToolSubmittingName = "";
  }
}

async function handleRunToolSuggestion(suggestion) {
  const toolName = suggestion?.tool || "search_sources";
  if (toolName !== "search_sources") {
    appState.agentToolError = "当前只支持运行 search_sources 建议工具";
    return;
  }
  await handleRunAgentTool({
    toolName: "search_sources",
    argumentsPayload: suggestion?.arguments || {},
  });
  clearToolSuggestionState();
}

function handleUseToolResultContext(runId) {
  if (!runId) {
    appState.answerStatus = "暂无可引用的工具结果";
    return;
  }
  appState.currentToolContextRunId = runId;
  appState.answerStatus = `下一问将引用工具运行 ID：${runId}`;
}

async function handleSelectAgentToolRun(runId) {
  appState.agentToolDetailLoading = true;
  appState.agentToolDetailError = "";
  try {
    const run = await getAgentToolRunDetail(runId);
    appState.selectedAgentToolRun = run;
  } catch (error) {
    appState.agentToolDetailError = error.message || "工具运行详情读取失败";
  } finally {
    appState.agentToolDetailLoading = false;
  }
}

async function handleRunSearchDebug(payload) {
  appState.searchDebugLoading = true;
  appState.searchDebugError = "";
  appState.searchDebugStatus = "正在生成检索诊断...";
  try {
    const data = await runSearchDebug({
      projectId: appState.selectedProjectId,
      ...payload,
    });
    appState.searchDebugResult = data;
    appState.searchDebugStatus = `检索诊断完成：${data.hits?.length || 0} 条来源。`;
  } catch (error) {
    appState.searchDebugError = error.message || "检索诊断失败";
    appState.searchDebugStatus = "检索诊断失败";
  } finally {
    appState.searchDebugLoading = false;
  }
}

async function loadRetrievalSettings() {
  clearRetrievalSettingsState();
  if (!appState.selectedProjectId) {
    appState.retrievalSettingsStatus = "请选择项目空间后读取检索默认值";
    return;
  }

  appState.retrievalSettingsLoading = true;
  try {
    const settings = await getRetrievalSettings(appState.selectedProjectId);
    appState.retrievalSettings = settings;
    appState.retrievalSettingsStatus = settings ? "已加载当前项目默认值" : "未保存项目默认值";
  } catch (error) {
    appState.retrievalSettingsError = error.message || "检索默认值读取失败";
    appState.retrievalSettingsStatus = "检索默认值读取失败";
  } finally {
    appState.retrievalSettingsLoading = false;
  }
}

async function handleSaveRetrievalSettings(payload) {
  appState.retrievalSettingsSaving = true;
  appState.retrievalSettingsError = "";
  appState.retrievalSettingsStatus = "正在保存检索默认值...";
  try {
    const settings = await saveRetrievalSettings({
      projectId: appState.selectedProjectId,
      ...payload,
    });
    appState.retrievalSettings = settings;
    appState.retrievalSettingsStatus = "检索默认值已保存";
  } catch (error) {
    appState.retrievalSettingsError = error.message || "检索默认值保存失败";
    appState.retrievalSettingsStatus = "检索默认值保存失败";
  } finally {
    appState.retrievalSettingsSaving = false;
  }
}

async function loadRetrievalReviews() {
  appState.retrievalReviews = [];
  appState.retrievalReviewsError = "";
  appState.selectedRetrievalReview = null;
  appState.retrievalReviewDetailError = "";
  if (!appState.selectedProjectId) {
    appState.retrievalReviewStatus = "请选择项目空间后查看检索复盘";
    return;
  }

  appState.retrievalReviewsLoading = true;
  try {
    const reviews = await listRetrievalReviews(appState.selectedProjectId);
    appState.retrievalReviews = reviews;
    if (!appState.retrievalReviewStatus) {
      appState.retrievalReviewStatus = "已加载检索复盘";
    }
  } catch (error) {
    appState.retrievalReviewsError = error.message || "检索复盘读取失败";
    appState.retrievalReviewStatus = "检索复盘读取失败";
  } finally {
    appState.retrievalReviewsLoading = false;
  }
}

async function handleSaveRetrievalReview(payload) {
  appState.retrievalReviewSaving = true;
  appState.retrievalReviewError = "";
  appState.retrievalReviewStatus = "正在保存检索复盘...";
  try {
    const review = await saveRetrievalReview({
      projectId: appState.selectedProjectId,
      ...payload,
    });
    await loadRetrievalReviews();
    appState.selectedRetrievalReview = review;
    appState.retrievalReviewStatus = "检索复盘已保存";
  } catch (error) {
    appState.retrievalReviewError = error.message || "检索复盘保存失败";
    appState.retrievalReviewStatus = "检索复盘保存失败";
  } finally {
    appState.retrievalReviewSaving = false;
  }
}

async function handleSelectRetrievalReview(reviewId) {
  appState.retrievalReviewDetailLoading = true;
  appState.retrievalReviewDetailError = "";
  try {
    const review = await getRetrievalReviewDetail(reviewId);
    appState.selectedRetrievalReview = review;
  } catch (error) {
    appState.retrievalReviewDetailError = error.message || "检索复盘详情读取失败";
  } finally {
    appState.retrievalReviewDetailLoading = false;
  }
}

async function handleDeleteRetrievalReview(reviewId) {
  if (!confirm("确认删除这条检索复盘吗？")) {
    return;
  }

  appState.deletingRetrievalReviewId = reviewId;
  appState.retrievalReviewError = "";
  appState.retrievalReviewStatus = "正在删除检索复盘...";
  try {
    const reviews = await deleteRetrievalReview(reviewId);
    appState.retrievalReviews = reviews;
    if (appState.selectedRetrievalReview?.id === reviewId) {
      appState.selectedRetrievalReview = null;
    }
    appState.retrievalReviewStatus = "检索复盘已删除";
  } catch (error) {
    appState.retrievalReviewError = error.message || "检索复盘删除失败";
    appState.retrievalReviewStatus = "检索复盘删除失败";
  } finally {
    appState.deletingRetrievalReviewId = "";
  }
}

async function handleSubmitQuestion(question) {
  appState.currentQuestion = question;
  appState.answerLoading = true;
  appState.answerError = "";
  appState.answerStatus = "正在生成回答...";
  clearAnswerFeedbackState();
  try {
    const data = await askQuestion({
      projectId: appState.selectedProjectId,
      question,
      toolRunId: appState.currentToolContextRunId,
    });
    appState.answerResult = data;
    appState.currentToolSuggestion = data.tool_suggestion || null;
    if (data.tool_context) {
      consumeToolContext();
    }
    appState.lastAnswerMessageId = data.message?.id || "";
    appState.answerStatus = "回答已生成";
  } catch (error) {
    appState.answerError = error.message || "回答生成失败";
    appState.answerStatus = "回答生成失败";
    appState.lastAnswerMessageId = "";
    clearToolSuggestionState();
  } finally {
    appState.answerLoading = false;
  }
}

async function handleSubmitAnswerFeedback(rating) {
  appState.answerFeedbackSubmitting = true;
  appState.answerFeedbackError = "";
  appState.answerFeedbackStatus = "正在保存回答反馈...";
  try {
    const data = await submitAnswerFeedback({
      projectId: appState.selectedProjectId,
      messageId: appState.lastAnswerMessageId,
      rating,
    });
    const label = formatAnswerFeedbackRating(data.feedback?.rating || rating);
    appState.answerFeedbackStatus = "回答反馈已保存";
    if (label) {
      appState.answerFeedbackStatus = `回答反馈已保存：${label}`;
    }
  } catch (error) {
    appState.answerFeedbackError = error.message || "回答反馈保存失败";
    appState.answerFeedbackStatus = "回答反馈保存失败";
  } finally {
    appState.answerFeedbackSubmitting = false;
  }
}

function formatAnswerFeedbackRating(rating) {
  return {
    useful: "有用",
    not_useful: "无用",
    source_wrong: "来源不准",
    need_more_context: "需要更多上下文",
  }[rating] || rating;
}

async function loadLibraryDocuments() {
  appState.documents = [];
  appState.documentsLoadError = "";
  appState.selectedDocumentId = "";
  appState.selectedDocument = null;
  appState.documentPreviewError = "";
  if (!appState.selectedProjectId) {
    return;
  }

  appState.documentsLoading = true;
  try {
    const documents = await listDocuments(appState.selectedProjectId, appState.selectedDocumentCollectionId);
    appState.documents = documents;
  } catch (error) {
    appState.documentsLoadError = error.message || "文档列表读取失败";
  } finally {
    appState.documentsLoading = false;
  }
}

async function loadDocumentCollections() {
  appState.documentCollections = [];
  appState.documentCollectionsLoadError = "";
  if (!appState.selectedProjectId) {
    appState.selectedDocumentCollectionId = "";
    return;
  }

  appState.documentCollectionsLoading = true;
  try {
    const collections = await listDocumentCollections(appState.selectedProjectId);
    appState.documentCollections = collections;
    if (
      appState.selectedDocumentCollectionId
      && appState.selectedDocumentCollectionId !== "unassigned"
      && !collections.some((collection) => collection.id === appState.selectedDocumentCollectionId)
    ) {
      appState.selectedDocumentCollectionId = "";
    }
  } catch (error) {
    appState.documentCollectionsLoadError = error.message || "文档集合读取失败";
  } finally {
    appState.documentCollectionsLoading = false;
  }
}

async function handleSelectDocumentCollection(collectionId) {
  appState.selectedDocumentCollectionId = collectionId;
  clearCollectionItemStatus();
  clearDocumentDeleteStatus();
  await loadLibraryDocuments();
}

async function handleCreateDocumentCollection(name) {
  appState.collectionFormSubmitting = true;
  appState.collectionFormError = "";
  appState.collectionFormStatus = "";
  clearCollectionRenameStatus();
  clearCollectionItemStatus();
  try {
    await createDocumentCollection({
      projectId: appState.selectedProjectId,
      name,
    });
    appState.collectionFormStatus = "文档集合已创建";
    await loadDocumentCollections();
  } catch (error) {
    appState.collectionFormError = error.message || "文档集合创建失败";
  } finally {
    appState.collectionFormSubmitting = false;
  }
}

async function handleUpdateDocumentCollection(payload) {
  appState.collectionRenameSubmitting = true;
  appState.collectionRenameError = "";
  appState.collectionRenameStatus = "";
  clearCollectionFormStatus();
  clearCollectionItemStatus();
  try {
    await updateDocumentCollection({
      collectionId: payload.collectionId,
      name: payload.name,
    });
    appState.collectionRenameStatus = "文档集合已重命名";
    await loadDocumentCollections();
  } catch (error) {
    appState.collectionRenameError = error.message || "文档集合重命名失败";
  } finally {
    appState.collectionRenameSubmitting = false;
  }
}

async function handleDeleteDocumentCollection(collectionId) {
  if (!window.confirm("确认删除这个文档集合？集合内文档不会被删除。")) {
    return;
  }
  appState.collectionFormError = "";
  appState.collectionFormStatus = "";
  clearCollectionRenameStatus();
  clearCollectionItemStatus();
  clearDocumentDeleteStatus();
  appState.deletingCollectionId = collectionId;
  try {
    await deleteDocumentCollection(collectionId);
    if (appState.selectedDocumentCollectionId === collectionId) {
      appState.selectedDocumentCollectionId = "";
    }
    appState.collectionFormStatus = "文档集合已删除，集合内文档不会被删除";
    await loadDocumentCollections();
    await loadLibraryDocuments();
  } catch (error) {
    appState.collectionFormError = error.message || "文档集合删除失败";
  } finally {
    appState.deletingCollectionId = "";
  }
}

async function handleAddDocumentToCollection(payload) {
  appState.collectionItemSubmittingId = payload.documentId;
  appState.collectionItemError = "";
  appState.collectionItemStatus = "";
  clearCollectionFormStatus();
  clearCollectionRenameStatus();
  clearDocumentDeleteStatus();
  try {
    await addDocumentToCollection({
      collectionId: payload.collectionId,
      documentId: payload.documentId,
    });
    appState.collectionItemStatus = "文档已加入集合";
    await loadDocumentCollections();
    await loadLibraryDocuments();
  } catch (error) {
    appState.collectionItemError = error.message || "文档加入集合失败";
  } finally {
    appState.collectionItemSubmittingId = "";
  }
}

async function handleRemoveDocumentFromCollection(payload) {
  appState.collectionItemSubmittingId = payload.documentId;
  appState.collectionItemError = "";
  appState.collectionItemStatus = "";
  clearCollectionFormStatus();
  clearCollectionRenameStatus();
  clearDocumentDeleteStatus();
  try {
    await removeDocumentFromCollection({
      collectionId: payload.collectionId,
      documentId: payload.documentId,
    });
    appState.collectionItemStatus = "文档已从集合移出";
    await loadDocumentCollections();
    await loadLibraryDocuments();
  } catch (error) {
    appState.collectionItemError = error.message || "文档移出集合失败";
  } finally {
    appState.collectionItemSubmittingId = "";
  }
}

async function handleDeleteDocument(documentId) {
  if (!window.confirm("确认从当前项目空间移除这个文档记录？源文件不会被删除。")) {
    return;
  }
  appState.deletingDocumentId = documentId;
  appState.documentDeleteError = "";
  appState.documentDeleteStatus = "";
  clearCollectionFormStatus();
  clearCollectionRenameStatus();
  clearCollectionItemStatus();
  try {
    await deleteDocument(documentId);
    if (appState.selectedDocumentId === documentId) {
      appState.selectedDocumentId = "";
      appState.selectedDocument = null;
      appState.documentPreviewError = "";
    }
    appState.documentDeleteStatus = "文档已删除";
    await loadDocumentCollections();
    await loadLibraryDocuments();
  } catch (error) {
    appState.documentDeleteError = error.message || "文档删除失败";
  } finally {
    appState.deletingDocumentId = "";
  }
}

function clearCollectionFormStatus() {
  appState.collectionFormError = "";
  appState.collectionFormStatus = "";
}

function clearProjectMutationStatus() {
  appState.projectMutationError = "";
  appState.projectMutationStatus = "";
}

function clearPromptPresetState() {
  appState.promptPresets = [];
  appState.promptPresetTemplates = [];
  appState.selectedPromptPresetId = "";
  appState.editingPromptPresetId = "";
  appState.promptPresetLoadError = "";
  appState.promptPresetMutationError = "";
  appState.promptPresetStatus = "";
}

function resetAssessmentState() {
  appState.assessmentSession = null;
  appState.assessmentQuestion = null;
  appState.assessmentQuestionIndex = 0;
  appState.assessmentResults = [];
  appState.assessmentMissedQuestions = [];
  appState.assessmentAnsweredCurrent = false;
  appState.assessmentError = "";
  appState.assessmentStatus = "等待评估";
}

function clearCollectionRenameStatus() {
  appState.collectionRenameError = "";
  appState.collectionRenameStatus = "";
}

function clearCollectionItemStatus() {
  appState.collectionItemError = "";
  appState.collectionItemStatus = "";
}

function clearDocumentDeleteStatus() {
  appState.documentDeleteError = "";
  appState.documentDeleteStatus = "";
}

async function loadImportBatches() {
  appState.importBatches = [];
  appState.importBatchesLoadError = "";
  appState.selectedImportBatch = null;
  appState.selectedImportBatchItems = [];
  appState.importBatchDetailError = "";
  if (!appState.selectedProjectId) {
    return;
  }

  appState.importBatchesLoading = true;
  try {
    const batches = await listImportBatches(appState.selectedProjectId);
    appState.importBatches = batches;
  } catch (error) {
    appState.importBatchesLoadError = error.message || "导入批次历史读取失败";
  } finally {
    appState.importBatchesLoading = false;
  }
}

async function handleSelectImportBatch(batchId) {
  appState.selectedImportBatch = null;
  appState.selectedImportBatchItems = [];
  appState.importBatchDetailError = "";
  if (!batchId) {
    return;
  }

  appState.importBatchDetailLoading = true;
  try {
    const data = await getImportBatchDetail(batchId);
    appState.selectedImportBatch = data.batch;
    appState.selectedImportBatchItems = data.items || [];
  } catch (error) {
    appState.importBatchDetailError = error.message || "导入批次详情读取失败";
  } finally {
    appState.importBatchDetailLoading = false;
  }
}

async function handleSelectDocument(documentId) {
  appState.selectedDocumentId = documentId;
  appState.selectedDocument = null;
  appState.documentPreviewError = "";
  if (!documentId) {
    return;
  }

  appState.documentPreviewLoading = true;
  try {
    const document = await getDocument(documentId);
    appState.selectedDocument = document;
  } catch (error) {
    appState.documentPreviewError = error.message || "文档预览读取失败";
  } finally {
    appState.documentPreviewLoading = false;
  }
}
</script>

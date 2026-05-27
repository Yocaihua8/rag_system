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
      :project-status-message="projectStatusMessage"
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
      :documents="appState.documents"
      :documents-loading="appState.documentsLoading"
      :documents-load-error="appState.documentsLoadError"
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
      @check-health="checkHealth"
      @refresh-projects="loadProjectSpaces"
      @select-project="handleSelectProject"
      @create-project="handleCreateProject"
      @submit-question="handleSubmitQuestion"
      @refresh-documents="loadLibraryDocuments"
      @select-document="handleSelectDocument"
      @import-note="handleImportNote"
      @import-url="handleImportUrl"
      @import-files="handleImportFiles"
      @import-folder="handleImportFolder"
      @sync-directory="handleSyncDirectory"
      @preview-import="handlePreviewImport"
      @refresh-batches="loadImportBatches"
      @select-batch="handleSelectImportBatch"
    />
  </AppShell>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";

import { askQuestion } from "./api/answer.js";
import { apiGet } from "./api/client.js";
import { getDocument, listDocuments } from "./api/documents.js";
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
  loadProjects,
  restoreSelectedProjectId,
  selectProject,
} from "./api/projects.js";
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

onMounted(() => {
  loadProjectSpaces();
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

async function loadProjectSpaces() {
  appState.projectsLoading = true;
  appState.projectLoadError = "";
  try {
    await loadProjects();
    appState.selectedProjectId = restoreSelectedProjectId(appState.projects);
    await loadLibraryDocuments();
    await loadImportBatches();
  } catch (error) {
    appState.projectLoadError = error.message || "项目空间读取失败";
  } finally {
    appState.projectsLoading = false;
  }
}

async function handleSelectProject(projectId) {
  selectProject(projectId);
  clearImportPreview();
  projectFormStatus.value = projectId ? "已切换项目空间" : "未选择项目空间";
  await loadLibraryDocuments();
  await loadImportBatches();
}

async function handleCreateProject(payload) {
  appState.projectFormSubmitting = true;
  appState.projectFormError = "";
  projectFormStatus.value = "";
  try {
    const project = await createProject(payload);
    projectFormStatus.value = `已创建项目空间：${project.name}`;
    await loadLibraryDocuments();
    await loadImportBatches();
  } catch (error) {
    appState.projectFormError = error.message || "项目空间创建失败";
  } finally {
    appState.projectFormSubmitting = false;
  }
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

async function handleSubmitQuestion(question) {
  appState.currentQuestion = question;
  appState.answerLoading = true;
  appState.answerError = "";
  appState.answerStatus = "正在生成回答...";
  try {
    const data = await askQuestion({
      projectId: appState.selectedProjectId,
      question,
    });
    appState.answerResult = data;
    appState.answerStatus = "回答已生成";
  } catch (error) {
    appState.answerError = error.message || "回答生成失败";
    appState.answerStatus = "回答生成失败";
  } finally {
    appState.answerLoading = false;
  }
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

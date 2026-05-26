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
      @check-health="checkHealth"
      @refresh-projects="loadProjectSpaces"
      @select-project="handleSelectProject"
      @create-project="handleCreateProject"
      @submit-question="handleSubmitQuestion"
      @refresh-documents="loadLibraryDocuments"
      @select-document="handleSelectDocument"
    />
  </AppShell>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";

import { askQuestion } from "./api/answer.js";
import { apiGet } from "./api/client.js";
import { getDocument, listDocuments } from "./api/documents.js";
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
  } catch (error) {
    appState.projectLoadError = error.message || "项目空间读取失败";
  } finally {
    appState.projectsLoading = false;
  }
}

async function handleSelectProject(projectId) {
  selectProject(projectId);
  projectFormStatus.value = projectId ? "已切换项目空间" : "未选择项目空间";
  await loadLibraryDocuments();
}

async function handleCreateProject(payload) {
  appState.projectFormSubmitting = true;
  appState.projectFormError = "";
  projectFormStatus.value = "";
  try {
    const project = await createProject(payload);
    projectFormStatus.value = `已创建项目空间：${project.name}`;
    await loadLibraryDocuments();
  } catch (error) {
    appState.projectFormError = error.message || "项目空间创建失败";
  } finally {
    appState.projectFormSubmitting = false;
  }
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

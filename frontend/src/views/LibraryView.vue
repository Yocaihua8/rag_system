<template>
  <section class="view-panel">
    <header class="topbar">
      <div>
        <p class="section-kicker">资料库</p>
        <h2>资料库</h2>
        <p>B-141C 已迁移项目空间基础，B-141E 已迁移文档列表与单文档预览；文件导入、文档集合和批次历史后续迁移。</p>
      </div>
    </header>

    <div class="library-grid">
      <ProjectSpacePanel
        :projects="projects"
        :selected-project-id="selectedProjectId"
        :loading="projectsLoading"
        :load-error="projectLoadError"
        :form-submitting="projectFormSubmitting"
        :form-error="projectFormError"
        :form-status="projectFormStatus"
        :status-message="projectStatusMessage"
        @refresh-projects="$emit('refresh-projects')"
        @select-project="(projectId) => $emit('select-project', projectId)"
        @create-project="(payload) => $emit('create-project', payload)"
      />
      <DocumentListPanel
        :documents="documents"
        :selected-project-id="selectedProjectId"
        :selected-document-id="selectedDocumentId"
        :loading="documentsLoading"
        :load-error="documentsLoadError"
        @refresh-documents="$emit('refresh-documents')"
        @select-document="(documentId) => $emit('select-document', documentId)"
      />
      <DocumentPreviewPanel
        :selected-document="selectedDocument"
        :selected-document-id="selectedDocumentId"
        :loading="documentPreviewLoading"
        :error="documentPreviewError"
      />
    </div>
  </section>
</template>

<script setup>
import DocumentListPanel from "../components/DocumentListPanel.vue";
import DocumentPreviewPanel from "../components/DocumentPreviewPanel.vue";
import ProjectSpacePanel from "../components/ProjectSpacePanel.vue";

defineProps({
  projects: {
    type: Array,
    required: true,
  },
  selectedProjectId: {
    type: String,
    required: true,
  },
  projectsLoading: {
    type: Boolean,
    default: false,
  },
  projectLoadError: {
    type: String,
    default: "",
  },
  projectFormSubmitting: {
    type: Boolean,
    default: false,
  },
  projectFormError: {
    type: String,
    default: "",
  },
  projectFormStatus: {
    type: String,
    default: "",
  },
  projectStatusMessage: {
    type: String,
    default: "",
  },
  documents: {
    type: Array,
    default: () => [],
  },
  documentsLoading: {
    type: Boolean,
    default: false,
  },
  documentsLoadError: {
    type: String,
    default: "",
  },
  selectedDocumentId: {
    type: String,
    default: "",
  },
  selectedDocument: {
    type: Object,
    default: null,
  },
  documentPreviewLoading: {
    type: Boolean,
    default: false,
  },
  documentPreviewError: {
    type: String,
    default: "",
  },
});

defineEmits(["refresh-projects", "select-project", "create-project", "refresh-documents", "select-document"]);
</script>

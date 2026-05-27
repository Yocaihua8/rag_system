<template>
  <section class="view-panel">
    <header class="topbar">
      <div>
        <p class="section-kicker">资料库</p>
        <h2>资料库</h2>
        <p>B-141C 至 B-141M 已迁移项目空间、文档浏览、导入入口、导入批次历史、目录同步、导入预检和文档集合筛选/新建/删除；集合重命名、加入/移出文档等能力继续分片迁移。</p>
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
      <DocumentImportPanel
        :selected-project-id="selectedProjectId"
        :import-submitting="importSubmitting"
        :import-error="importError"
        :import-status="importStatus"
        :import-preview="importPreview"
        :import-preview-loading="importPreviewLoading"
        :import-preview-error="importPreviewError"
        @import-note="(payload) => $emit('import-note', payload)"
        @import-url="(payload) => $emit('import-url', payload)"
        @import-files="(files) => $emit('import-files', files)"
        @import-folder="(files) => $emit('import-folder', files)"
        @sync-directory="$emit('sync-directory')"
        @preview-import="$emit('preview-import')"
      />
      <DocumentCollectionPanel
        :document-collections="documentCollections"
        :selected-project-id="selectedProjectId"
        :selected-document-collection-id="selectedDocumentCollectionId"
        :document-collections-loading="documentCollectionsLoading"
        :document-collections-load-error="documentCollectionsLoadError"
        :collection-form-submitting="collectionFormSubmitting"
        :collection-form-error="collectionFormError"
        :collection-form-status="collectionFormStatus"
        :collection-rename-submitting="collectionRenameSubmitting"
        :collection-rename-error="collectionRenameError"
        :collection-rename-status="collectionRenameStatus"
        :deleting-collection-id="deletingCollectionId"
        @refresh-collections="$emit('refresh-collections')"
        @select-collection="(collectionId) => $emit('select-collection', collectionId)"
        @create-collection="(name) => $emit('create-collection', name)"
        @delete-collection="(collectionId) => $emit('delete-collection', collectionId)"
        @update-collection="(payload) => $emit('update-collection', payload)"
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
      <ImportBatchHistoryPanel
        :selected-project-id="selectedProjectId"
        :import-batches="importBatches"
        :selected-import-batch="selectedImportBatch"
        :selected-import-batch-items="selectedImportBatchItems"
        :loading="importBatchesLoading"
        :load-error="importBatchesLoadError"
        :detail-loading="importBatchDetailLoading"
        :detail-error="importBatchDetailError"
        @refresh-batches="$emit('refresh-batches')"
        @select-batch="(batchId) => $emit('select-batch', batchId)"
      />
    </div>
  </section>
</template>

<script setup>
import DocumentCollectionPanel from "../components/DocumentCollectionPanel.vue";
import DocumentImportPanel from "../components/DocumentImportPanel.vue";
import DocumentListPanel from "../components/DocumentListPanel.vue";
import DocumentPreviewPanel from "../components/DocumentPreviewPanel.vue";
import ImportBatchHistoryPanel from "../components/ImportBatchHistoryPanel.vue";
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
  importSubmitting: {
    type: Boolean,
    default: false,
  },
  importError: {
    type: String,
    default: "",
  },
  importStatus: {
    type: String,
    default: "",
  },
  importPreview: {
    type: Object,
    default: null,
  },
  importPreviewLoading: {
    type: Boolean,
    default: false,
  },
  importPreviewError: {
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
  documentCollections: {
    type: Array,
    default: () => [],
  },
  selectedDocumentCollectionId: {
    type: String,
    default: "",
  },
  documentCollectionsLoading: {
    type: Boolean,
    default: false,
  },
  documentCollectionsLoadError: {
    type: String,
    default: "",
  },
  collectionFormSubmitting: {
    type: Boolean,
    default: false,
  },
  collectionFormError: {
    type: String,
    default: "",
  },
  collectionFormStatus: {
    type: String,
    default: "",
  },
  collectionRenameSubmitting: {
    type: Boolean,
    default: false,
  },
  collectionRenameError: {
    type: String,
    default: "",
  },
  collectionRenameStatus: {
    type: String,
    default: "",
  },
  deletingCollectionId: {
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
  importBatches: {
    type: Array,
    default: () => [],
  },
  importBatchesLoading: {
    type: Boolean,
    default: false,
  },
  importBatchesLoadError: {
    type: String,
    default: "",
  },
  selectedImportBatch: {
    type: Object,
    default: null,
  },
  selectedImportBatchItems: {
    type: Array,
    default: () => [],
  },
  importBatchDetailLoading: {
    type: Boolean,
    default: false,
  },
  importBatchDetailError: {
    type: String,
    default: "",
  },
});

defineEmits([
  "refresh-projects",
  "select-project",
  "create-project",
  "refresh-documents",
  "select-document",
  "refresh-collections",
  "select-collection",
  "create-collection",
  "delete-collection",
  "update-collection",
  "import-note",
  "import-url",
  "import-files",
  "import-folder",
  "sync-directory",
  "preview-import",
  "refresh-batches",
  "select-batch",
]);
</script>

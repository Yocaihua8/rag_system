<template>
  <section class="view-panel">
    <header class="topbar">
      <div>
        <p class="section-kicker">资料库</p>
        <h2>资料库</h2>
        <p>B-141C 至 B-141Q 已迁移项目空间选择/创建/改名/删除、文档浏览、导入入口、导入批次历史、目录同步、导入预检、文档集合筛选/新建/删除/重命名/加入/移出和删除文档；其余能力继续分片迁移。</p>
      </div>
    </header>

    <KnowledgeBaseManagementPanel
      :selected-project-id="selectedProjectId"
      :project-summary="projectSummary"
      :project-summary-loading="projectSummaryLoading"
      :project-summary-error="projectSummaryError"
      :assessment-library="assessmentLibrary"
      :assessment-library-loading="assessmentLibraryLoading"
      :assessment-library-error="assessmentLibraryError"
      :import-batches="importBatches"
      :documents="documents"
    />

    <div class="library-grid">
      <ProjectSpacePanel
        :projects="projects"
        :selected-project-id="selectedProjectId"
        :loading="projectsLoading"
        :load-error="projectLoadError"
        :form-submitting="projectFormSubmitting"
        :form-error="projectFormError"
        :form-status="projectFormStatus"
        :project-rename-submitting="projectRenameSubmitting"
        :project-delete-submitting="projectDeleteSubmitting"
        :project-mutation-error="projectMutationError"
        :project-mutation-status="projectMutationStatus"
        :status-message="projectStatusMessage"
        @refresh-projects="$emit('refresh-projects')"
        @select-project="(projectId) => $emit('select-project', projectId)"
        @create-project="(payload) => $emit('create-project', payload)"
        @rename-project="(name) => $emit('rename-project', name)"
        @delete-project="$emit('delete-project')"
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
        @import-notion-zip="(file) => $emit('import-notion-zip', file)"
        @import-obsidian-vault="(payload) => $emit('import-obsidian-vault', payload)"
        @import-github-repo="(payload) => $emit('import-github-repo', payload)"
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
        :document-collections="documentCollections"
        :selected-document-collection-id="selectedDocumentCollectionId"
        :collection-item-submitting-id="collectionItemSubmittingId"
        :collection-item-error="collectionItemError"
        :collection-item-status="collectionItemStatus"
        :deleting-document-id="deletingDocumentId"
        :document-delete-error="documentDeleteError"
        :document-delete-status="documentDeleteStatus"
        @refresh-documents="$emit('refresh-documents')"
        @select-document="(documentId) => $emit('select-document', documentId)"
        @add-document-to-collection="(payload) => $emit('add-document-to-collection', payload)"
        @remove-document-from-collection="(payload) => $emit('remove-document-from-collection', payload)"
        @delete-document="(documentId) => $emit('delete-document', documentId)"
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
import KnowledgeBaseManagementPanel from "../components/KnowledgeBaseManagementPanel.vue";
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
  projectRenameSubmitting: {
    type: Boolean,
    default: false,
  },
  projectDeleteSubmitting: {
    type: Boolean,
    default: false,
  },
  projectMutationError: {
    type: String,
    default: "",
  },
  projectMutationStatus: {
    type: String,
    default: "",
  },
  projectStatusMessage: {
    type: String,
    default: "",
  },
  projectSummary: {
    type: Object,
    default: null,
  },
  projectSummaryLoading: {
    type: Boolean,
    default: false,
  },
  projectSummaryError: {
    type: String,
    default: "",
  },
  assessmentLibrary: {
    type: Object,
    default: null,
  },
  assessmentLibraryLoading: {
    type: Boolean,
    default: false,
  },
  assessmentLibraryError: {
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
  collectionItemSubmittingId: {
    type: String,
    default: "",
  },
  collectionItemError: {
    type: String,
    default: "",
  },
  collectionItemStatus: {
    type: String,
    default: "",
  },
  deletingDocumentId: {
    type: String,
    default: "",
  },
  documentDeleteError: {
    type: String,
    default: "",
  },
  documentDeleteStatus: {
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
  "rename-project",
  "delete-project",
  "refresh-documents",
  "select-document",
  "refresh-collections",
  "select-collection",
  "create-collection",
  "delete-collection",
  "update-collection",
  "add-document-to-collection",
  "remove-document-from-collection",
  "delete-document",
  "import-note",
  "import-url",
  "import-files",
  "import-folder",
  "import-notion-zip",
  "import-obsidian-vault",
  "import-github-repo",
  "sync-directory",
  "preview-import",
  "refresh-batches",
  "select-batch",
]);
</script>

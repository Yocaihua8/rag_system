<template>
  <div class="page full" aria-label="资料库：创建项目空间、导入本地资料、管理文档集合并查看导入历史。">
    <div>
      <div class="dashboard">
        <div v-for="[label, value] in summaryMetrics" :key="label" class="metric">
          <div class="v">{{ value }}</div>
          <div class="k">{{ label }}</div>
        </div>
        <div class="health-stamp" :class="healthStamp.className">
          {{ healthStamp.label }}
          <small>{{ healthStamp.detail }}</small>
        </div>
      </div>
      <p class="dashboard-note">最近活动：{{ summaryLastActivity }}</p>

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

      <div class="import-row">
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

      <div class="coll-tabs" aria-label="文档集合筛选">
        <button type="button" :class="{ active: selectedDocumentCollectionId === '' }" @click="$emit('select-collection', '')">
          全部 ({{ documents.length }})
        </button>
        <button type="button" :class="{ active: selectedDocumentCollectionId === 'unassigned' }" @click="$emit('select-collection', 'unassigned')">
          未分组
        </button>
        <button
          v-for="collection in documentCollections"
          :key="collection.id"
          type="button"
          :class="{ active: selectedDocumentCollectionId === collection.id }"
          @click="$emit('select-collection', collection.id)"
        >
          {{ collection.name }} ({{ collection.document_count ?? collection.count ?? 0 }})
        </button>
        <button type="button" class="add" @click="focusCollectionManagement">+ 新建集合</button>
      </div>

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

      <div ref="collectionManagement">
        <DocumentCollectionPanel
          :document-collections="documentCollections"
          :selected-project-id="selectedProjectId"
          :selected-document-collection-id="selectedDocumentCollectionId"
          :loading="documentCollectionsLoading"
          :load-error="documentCollectionsLoadError"
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
      </div>
      <DocumentPreviewPanel
        :selected-document="selectedDocument"
        :selected-document-id="selectedDocumentId"
        :loading="documentPreviewLoading"
        :error="documentPreviewError"
      />
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from "vue";

import DocumentCollectionPanel from "../components/DocumentCollectionPanel.vue";
import DocumentImportPanel from "../components/DocumentImportPanel.vue";
import DocumentListPanel from "../components/DocumentListPanel.vue";
import DocumentPreviewPanel from "../components/DocumentPreviewPanel.vue";
import ImportBatchHistoryPanel from "../components/ImportBatchHistoryPanel.vue";
import ProjectSpacePanel from "../components/ProjectSpacePanel.vue";

const props = defineProps({
  projects: {
    type: Array,
    required: true,
  },
  selectedProjectId: {
    type: String,
    required: true,
  },
  projectSummary: {
    type: Object,
    default: null,
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

const collectionManagement = ref(null);
const qualitySummary = ref(null);
const qualitySummaryRequestId = ref(0);

const summaryMetrics = computed(() => [
  ["文档", summaryValue("document_count", props.documents.length)],
  ["Chunk", summaryValue("chunk_count", 0)],
  ["向量", summaryValue("vector_count", 0)],
  ["回答有来源率", qualitySourceRate.value],
  ["聊天", summaryValue("chat_message_count", 0)],
  ["工具", summaryValue("agent_tool_run_count", 0)],
  ["复盘", summaryValue("retrieval_review_count", 0)],
]);

const qualitySourceRate = computed(() => {
  const rate = Number(qualitySummary.value?.has_sources_rate ?? 0);
  return `${Math.round(rate * 100)}%`;
});

const healthStamp = computed(() => {
  if (!props.selectedProjectId) {
    return { label: "未选择项目", detail: "PROJECT REQUIRED", className: "empty" };
  }
  const chunkCount = Number(summaryValue("chunk_count", 0));
  const vectorCount = Number(summaryValue("vector_count", 0));
  if (chunkCount <= 0) {
    return { label: "暂无 Chunk", detail: "EMPTY INDEX", className: "empty" };
  }
  if (vectorCount > 0) {
    return { label: "✓ 向量已生成", detail: "HYBRID READY", className: "ready" };
  }
  return { label: "仅关键词", detail: "KEYWORD ONLY", className: "warning" };
});

const summaryLastActivity = computed(() => {
  return props.projectSummary?.last_activity_at || "暂无记录";
});

function summaryValue(fieldName, fallbackValue) {
  return props.projectSummary?.[fieldName] ?? fallbackValue;
}

function focusCollectionManagement() {
  collectionManagement.value?.scrollIntoView({ behavior: "smooth", block: "start" });
}

async function loadQualitySummary(projectId) {
  const requestId = qualitySummaryRequestId.value + 1;
  qualitySummaryRequestId.value = requestId;
  qualitySummary.value = null;
  if (!projectId) {
    return;
  }
  try {
    const response = await fetch(`/api/projects/quality-summary?project_id=${encodeURIComponent(projectId)}`);
    if (!response.ok) {
      return;
    }
    const data = await response.json();
    if (qualitySummaryRequestId.value === requestId) {
      qualitySummary.value = data;
    }
  } catch {
    if (qualitySummaryRequestId.value === requestId) {
      qualitySummary.value = null;
    }
  }
}

watch(
  () => props.selectedProjectId,
  (projectId) => {
    loadQualitySummary(projectId);
  },
  { immediate: true },
);

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
  "sync-directory",
  "preview-import",
  "refresh-batches",
  "select-batch",
]);
</script>

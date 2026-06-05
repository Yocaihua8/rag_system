<template>
  <section class="document-list-panel" aria-labelledby="document-list-title">
    <div class="section-title-row">
      <div>
        <p class="section-kicker">文档列表</p>
        <h2 id="document-list-title">文档列表</h2>
      </div>
      <button type="button" :disabled="loading || !selectedProjectId" @click="$emit('refresh-documents')">
        {{ loading ? "刷新中..." : "刷新文档" }}
      </button>
    </div>

    <p v-if="!selectedProjectId" class="status-line">未选择项目空间</p>
    <p v-else-if="loading" class="status-line">正在读取文档...</p>
    <p v-else-if="loadError" class="status-line error">{{ loadError }}</p>
    <p v-else-if="documents.length === 0" class="status-line">暂无文档</p>

    <table v-else class="doc-table">
      <thead>
        <tr>
          <th></th>
          <th>文档</th>
          <th>来源</th>
          <th>修改</th>
          <th>集合</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="document in documents" :key="document.id" :class="{ active: document.id === selectedDocumentId }">
          <td>📄</td>
          <td class="name">
            <button type="button" class="table-link" @click="$emit('select-document', document.id)">
              {{ document.relative_path || document.title || "未命名文档" }}
            </button>
          </td>
          <td class="src">{{ document.source_path || document.relative_path || "未知来源" }}</td>
          <td class="date">{{ document.updated_at || "未记录" }}</td>
          <td class="size">
            <div v-if="documentCollections.length > 0" class="table-actions">
              <select
                v-model="collectionSelections[document.id]"
                :disabled="isSubmitting(document) || availableCollectionsForDocument(document).length === 0"
              >
                <option value="">选择集合</option>
                <option v-for="collection in availableCollectionsForDocument(document)" :key="collection.id" :value="collection.id">
                  {{ collection.name }}
                </option>
              </select>
              <button type="button" :disabled="isSubmitting(document) || !collectionSelections[document.id]" @click="submitAdd(document)">
                {{ isSubmitting(document) ? "处理中..." : "加入集合" }}
              </button>
              <button
                v-if='selectedDocumentCollectionId && selectedDocumentCollectionId !== "unassigned"'
                type="button"
                class="delete"
                :disabled="isSubmitting(document)"
                @click="submitRemove(document)"
              >
                移出集合
              </button>
            </div>
          </td>
          <td>
            <button type="button" class="delete" :disabled="deletingDocumentId !== ''" @click="$emit('delete-document', document.id)">
              {{ deletingDocumentId === document.id ? "删除中..." : "删除文档" }}
            </button>
          </td>
        </tr>
      </tbody>
    </table>
    <p v-if="collectionItemError" class="status-line error">{{ collectionItemError }}</p>
    <p v-else-if="collectionItemStatus" class="status-line">{{ collectionItemStatus }}</p>
    <p v-if="documentDeleteError" class="status-line error">{{ documentDeleteError }}</p>
    <p v-else-if="documentDeleteStatus" class="status-line">{{ documentDeleteStatus }}</p>
  </section>
</template>

<script setup>
import { reactive } from "vue";

const props = defineProps({
  documents: {
    type: Array,
    required: true,
  },
  selectedProjectId: {
    type: String,
    required: true,
  },
  selectedDocumentId: {
    type: String,
    default: "",
  },
  loading: {
    type: Boolean,
    default: false,
  },
  loadError: {
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
});

const emit = defineEmits(["refresh-documents", "select-document", "add-document-to-collection", "remove-document-from-collection", "delete-document"]);

const collectionSelections = reactive({});

function availableCollectionsForDocument() {
  return props.documentCollections.filter((collection) => collection.id !== props.selectedDocumentCollectionId);
}

function isSubmitting(document) {
  return props.collectionItemSubmittingId === document.id;
}

function submitAdd(document) {
  emit("add-document-to-collection", {
    collectionId: collectionSelections[document.id],
    documentId: document.id,
  });
}

function submitRemove(document) {
  emit("remove-document-from-collection", {
    collectionId: props.selectedDocumentCollectionId,
    documentId: document.id,
  });
}
</script>

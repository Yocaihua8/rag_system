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

    <ul v-else class="document-list">
      <li v-for="document in documents" :key="document.id">
        <button
          type="button"
          class="document-list-item"
          :class="{ active: document.id === selectedDocumentId }"
          @click="$emit('select-document', document.id)"
        >
          <span>{{ document.relative_path || document.source_path || "未命名文档" }}</span>
          <small>{{ document.updated_at || "未记录更新时间" }}</small>
        </button>
      </li>
    </ul>
  </section>
</template>

<script setup>
defineProps({
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
});

defineEmits(["refresh-documents", "select-document"]);
</script>

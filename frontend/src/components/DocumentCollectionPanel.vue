<template>
  <section class="document-collection-panel" aria-labelledby="document-collection-title">
    <div class="section-title-row">
      <div>
        <p class="section-kicker">文档集合</p>
        <h2 id="document-collection-title">文档集合</h2>
      </div>
      <button type="button" :disabled="loading || !selectedProjectId" @click="$emit('refresh-collections')">
        {{ loading ? "刷新中..." : "刷新集合" }}
      </button>
    </div>

    <p v-if="!selectedProjectId" class="status-line">未选择项目空间</p>
    <p v-else-if="loading" class="status-line">正在读取文档集合...</p>
    <p v-else-if="loadError" class="status-line error">{{ loadError }}</p>

    <label class="field-block">
      集合筛选
      <select
        :value="selectedDocumentCollectionId"
        :disabled="loading || !selectedProjectId"
        @change="$emit('select-collection', $event.target.value)"
      >
        <option value="">全部文档</option>
        <option value="unassigned">未分组</option>
        <option
          v-for="collection in documentCollections"
          :key="collection.id"
          :value="collection.id"
        >
          {{ collection.name }}（{{ collection.document_count ?? 0 }}）
        </option>
      </select>
    </label>

    <p v-if="selectedProjectId && !loading && documentCollections.length === 0" class="status-line">
      暂无文档集合
    </p>

    <ul v-else class="document-collection-list">
      <li v-for="collection in documentCollections" :key="collection.id">
        <button
          type="button"
          class="document-collection-item"
          :class="{ active: collection.id === selectedDocumentCollectionId }"
          @click="$emit('select-collection', collection.id)"
        >
          <span>{{ collection.name }}</span>
          <small>{{ collection.document_count ?? 0 }} 个文档</small>
        </button>
      </li>
    </ul>
  </section>
</template>

<script setup>
defineProps({
  documentCollections: {
    type: Array,
    default: () => [],
  },
  selectedProjectId: {
    type: String,
    required: true,
  },
  selectedDocumentCollectionId: {
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

defineEmits(["refresh-collections", "select-collection"]);
</script>

<template>
  <section class="import-batch-panel" aria-labelledby="import-batch-title">
    <div class="section-title-row">
      <div>
        <p class="section-kicker">导入批次历史</p>
        <h2 id="import-batch-title">导入批次历史</h2>
      </div>
      <button type="button" :disabled="loading || !selectedProjectId" @click="$emit('refresh-batches')">
        {{ loading ? "刷新中..." : "刷新批次" }}
      </button>
    </div>

    <p v-if="!selectedProjectId" class="status-line">未选择项目空间</p>
    <p v-else-if="loading" class="status-line">正在读取导入批次...</p>
    <p v-else-if="loadError" class="status-line error">{{ loadError }}</p>
    <p v-else-if="importBatches.length === 0" class="status-line">暂无导入批次历史</p>

    <ul v-else class="import-batch-list">
      <li v-for="batch in importBatches" :key="batch.id">
        <button
          type="button"
          class="import-batch-item"
          :class="{ active: selectedImportBatch && batch.id === selectedImportBatch.id }"
          @click="$emit('select-batch', batch.id)"
        >
          <span>{{ formatImportSourceType(batch.source_type) }} / {{ formatImportBatchStatus(batch.status) }}</span>
          <small>{{ formatBatchSummary(batch) }}</small>
          <small>{{ batch.finished_at || batch.created_at || "未记录时间" }}</small>
          <strong>查看详情</strong>
        </button>
      </li>
    </ul>

    <article class="import-batch-detail" aria-labelledby="import-batch-detail-title">
      <p class="section-kicker">批次详情</p>
      <h3 id="import-batch-detail-title">批次详情</h3>

      <p v-if="detailLoading" class="status-line">正在读取导入批次详情...</p>
      <p v-else-if="detailError" class="status-line error">{{ detailError }}</p>
      <p v-else-if="!selectedImportBatch" class="muted-line">请选择一条导入批次查看详情</p>

      <div v-else class="batch-detail-body">
        <p>来源：{{ formatImportSourceType(selectedImportBatch.source_type) }}</p>
        <p>状态：{{ formatImportBatchStatus(selectedImportBatch.status) }}</p>
        <p>时间：{{ selectedImportBatch.finished_at || selectedImportBatch.created_at || "未记录时间" }}</p>
        <p>汇总：{{ formatBatchSummary(selectedImportBatch) }}</p>

        <p class="section-kicker">跳过 / 错误明细</p>
        <p v-if="visibleItems.length === 0" class="muted-line">本批次没有跳过或错误明细</p>
        <ol v-else>
          <li v-for="item in visibleItems" :key="item.id || `${item.kind}:${item.relative_path}`">
            {{ formatImportBatchItemKind(item.kind) }}：{{ item.relative_path || "未记录路径" }}：{{ item.reason || "无原因" }}
          </li>
        </ol>
      </div>
    </article>
  </section>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  selectedProjectId: {
    type: String,
    required: true,
  },
  importBatches: {
    type: Array,
    default: () => [],
  },
  selectedImportBatch: {
    type: Object,
    default: null,
  },
  selectedImportBatchItems: {
    type: Array,
    default: () => [],
  },
  loading: {
    type: Boolean,
    default: false,
  },
  loadError: {
    type: String,
    default: "",
  },
  detailLoading: {
    type: Boolean,
    default: false,
  },
  detailError: {
    type: String,
    default: "",
  },
});

defineEmits(["refresh-batches", "select-batch"]);

const visibleItems = computed(() => {
  return props.selectedImportBatchItems.filter((item) => ["skipped", "error"].includes(item.kind));
});

function formatBatchSummary(batch) {
  const summary = batch.summary || {};
  return [
    `新增 ${summary.created ?? 0}`,
    `更新 ${summary.updated ?? 0}`,
    `未变更 ${summary.unchanged ?? 0}`,
    `删除 ${summary.deleted ?? 0}`,
    `跳过 ${summary.skipped ?? 0}`,
    `错误 ${summary.errors ?? 0}`,
  ].join("，");
}

function formatImportSourceType(sourceType) {
  const labels = {
    directory_sync: "同步当前项目目录",
    browser_folder_upload: "浏览器文件夹导入",
    file_upload: "文件上传导入",
    text_note: "文本笔记导入",
    url_excerpt: "URL 摘录导入",
  };
  return labels[sourceType] || sourceType || "未知来源";
}

function formatImportBatchStatus(status) {
  const labels = {
    success: "成功",
    partial: "部分完成",
    failed: "失败",
  };
  return labels[status] || status || "未知";
}

function formatImportBatchItemKind(kind) {
  const labels = {
    skipped: "未导入",
    error: "读取失败",
  };
  return labels[kind] || kind || "明细";
}
</script>

<template>
  <section class="document-preview-panel" aria-labelledby="document-preview-title">
    <div class="section-title-row">
      <div>
        <p class="section-kicker">文档预览</p>
        <h2 id="document-preview-title">文档预览</h2>
      </div>
    </div>

    <p v-if="!selectedDocumentId" class="muted-line">请选择文档查看正文</p>
    <p v-else-if="loading" class="status-line">正在读取正文...</p>
    <p v-else-if="error" class="status-line error">{{ error }}</p>
    <p v-else-if="!selectedDocument" class="muted-line">正文预览暂不可用</p>

    <article v-else class="document-preview">
      <header>
        <p class="section-kicker">正文预览</p>
        <h3>{{ selectedDocument.relative_path || selectedDocument.source_path || "未命名文档" }}</h3>
        <p>{{ selectedDocument.updated_at || "未记录更新时间" }}</p>
      </header>
      <pre>{{ selectedDocument.content || "暂无正文内容" }}</pre>
    </article>
  </section>
</template>

<script setup>
defineProps({
  selectedDocument: {
    type: Object,
    default: null,
  },
  selectedDocumentId: {
    type: String,
    default: "",
  },
  loading: {
    type: Boolean,
    default: false,
  },
  error: {
    type: String,
    default: "",
  },
});
</script>

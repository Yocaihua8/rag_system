<template>
  <section class="knowledge-management-panel" aria-labelledby="knowledge-management-title">
    <div class="section-title-row">
      <div>
        <p class="section-kicker">知识库辅助管理</p>
        <h2 id="knowledge-management-title">知识库辅助管理</h2>
      </div>
      <span class="status">{{ overviewStatus }}</span>
    </div>

    <p v-if="!selectedProjectId" class="status-line">请选择项目空间后查看知识库管理概览</p>
    <template v-else>
      <p v-if="projectSummaryError" class="status-line error">{{ projectSummaryError }}</p>
      <p v-if="assessmentLibraryError" class="status-line error">{{ assessmentLibraryError }}</p>

      <div class="knowledge-management-grid">
        <div class="management-block management-block-wide">
          <div class="management-block-header">
            <h3>项目状态</h3>
            <strong>{{ projectStatusLabel }}</strong>
          </div>
          <dl class="management-metrics">
            <div>
              <dt>文件列表</dt>
              <dd>{{ projectSummary?.document_count ?? documents.length }}</dd>
            </div>
            <div>
              <dt>分块</dt>
              <dd>{{ projectSummary?.chunk_count ?? 0 }}</dd>
            </div>
            <div>
              <dt>向量</dt>
              <dd>{{ projectSummary?.vector_count ?? 0 }}</dd>
            </div>
            <div>
              <dt>评估题库</dt>
              <dd>{{ assessmentLibrary?.question_count ?? projectSummary?.assessment_question_count ?? 0 }}</dd>
            </div>
          </dl>
          <p class="muted-line">
            最近活动：{{ formatDate(projectSummary?.last_activity_at) }}
          </p>
        </div>

        <div class="management-block">
          <div class="management-block-header">
            <h3>检索健康</h3>
            <strong>{{ retrievalHealthLabel }}</strong>
          </div>
          <p class="muted-line">
            复盘 {{ projectSummary?.retrieval_review_count ?? 0 }} 条，回答 {{ projectSummary?.chat_message_count ?? 0 }} 条。
          </p>
        </div>

        <div class="management-block">
          <div class="management-block-header">
            <h3>摄入进度</h3>
            <strong>{{ latestImportBatch ? latestImportBatch.status || "已记录" : "暂无导入批次历史" }}</strong>
          </div>
          <p class="muted-line">
            {{ latestImportBatch ? formatImportBatch(latestImportBatch) : "暂无导入批次历史" }}
          </p>
        </div>

        <div class="management-block management-block-wide">
          <div class="management-block-header">
            <h3>文件列表</h3>
            <strong>{{ documents.length ? `${documents.length} 个文件` : "知识库为空" }}</strong>
          </div>
          <ul v-if="documents.length" class="management-list">
            <li v-for="document in latestDocuments" :key="document.id">
              <span>{{ document.title || document.path || document.id }}</span>
              <small>{{ document.source_type || "document" }} · {{ formatDate(document.updated_at || document.created_at) }}</small>
            </li>
          </ul>
          <p v-else class="muted-line">知识库为空</p>
        </div>

        <div class="management-block">
          <div class="management-block-header">
            <h3>评估题库</h3>
            <strong>{{ assessmentLibrary?.question_count ?? 0 }} 题</strong>
          </div>
          <p v-if="questionTypeRows.length === 0" class="muted-line">暂无评估题目</p>
          <dl v-else class="management-pairs">
            <div v-for="row in questionTypeRows" :key="row.label">
              <dt>{{ row.label }}</dt>
              <dd>{{ row.count }}</dd>
            </div>
          </dl>
        </div>

        <div class="management-block">
          <div class="management-block-header">
            <h3>最近结果</h3>
            <strong>{{ assessmentLibrary?.result_count ?? projectSummary?.assessment_result_count ?? 0 }} 条</strong>
          </div>
          <dl v-if="statusCountRows.length" class="management-pairs">
            <div v-for="row in statusCountRows" :key="row.label">
              <dt>{{ row.label }}</dt>
              <dd>{{ row.count }}</dd>
            </div>
          </dl>
          <p v-else class="muted-line">暂无最近结果</p>
        </div>
      </div>
    </template>
  </section>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  selectedProjectId: {
    type: String,
    required: true,
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
  importBatches: {
    type: Array,
    default: () => [],
  },
  documents: {
    type: Array,
    default: () => [],
  },
});

const latestImportBatch = computed(() => props.importBatches[0] || null);

const latestDocuments = computed(() => {
  return props.documents.slice(0, 5);
});

const projectStatusLabel = computed(() => {
  if (props.projectSummaryLoading) {
    return "读取中";
  }
  if (!props.projectSummary && props.documents.length === 0) {
    return "知识库为空";
  }
  return "可管理";
});

const retrievalHealthLabel = computed(() => {
  if (props.projectSummaryLoading) {
    return "检查中";
  }
  const chunkCount = Number(props.projectSummary?.chunk_count || 0);
  const vectorCount = Number(props.projectSummary?.vector_count || 0);
  if (chunkCount === 0) {
    return "知识库为空";
  }
  if (vectorCount < chunkCount) {
    return "待补齐向量";
  }
  return "可检索";
});

const overviewStatus = computed(() => {
  if (props.projectSummaryLoading || props.assessmentLibraryLoading) {
    return "刷新中...";
  }
  if (!props.selectedProjectId) {
    return "未选择项目";
  }
  return "已同步";
});

const questionTypeRows = computed(() => {
  return toCountRows(props.assessmentLibrary?.question_type_counts);
});

const statusCountRows = computed(() => {
  return toCountRows(props.assessmentLibrary?.status_counts);
});

function toCountRows(counts = {}) {
  return Object.entries(counts || {}).map(([label, count]) => ({
    label,
    count,
  }));
}

function formatDate(value) {
  if (!value) {
    return "N/A";
  }
  return String(value).replace("T", " ").slice(0, 16);
}

function formatImportBatch(batch) {
  const created = batch.created_count ?? batch.created ?? 0;
  const updated = batch.updated_count ?? batch.updated ?? 0;
  const skipped = batch.skipped_count ?? batch.skipped ?? 0;
  const deleted = batch.deleted_count ?? batch.deleted ?? 0;
  return `${formatDate(batch.created_at)} · 新增 ${created}，更新 ${updated}，删除 ${deleted}，跳过 ${skipped}`;
}
</script>

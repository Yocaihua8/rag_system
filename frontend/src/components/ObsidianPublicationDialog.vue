<template>
  <div
    v-if="open"
    class="publication-backdrop"
    data-publication-action="backdrop"
    @click.self="emit('close')"
  >
    <section
      class="publication-dialog"
      role="dialog"
      aria-modal="true"
      aria-labelledby="publication-dialog-title"
    >
      <header class="publication-header">
        <div>
          <p class="section-kicker">Obsidian 发布预览</p>
          <h2 id="publication-dialog-title">确认受控写回内容</h2>
          <p>{{ previewData.scope_notice || "以下内容只会写入当前项目已配对的 Obsidian 输出目录。" }}</p>
        </div>
        <button type="button" data-publication-action="close" @click="emit('close')">关闭</button>
      </header>

      <p v-if="loading" class="status-line">正在生成内容与路径预览...</p>
      <p v-if="error" class="status-line error">{{ error }}</p>
      <p v-if="status" class="status-line">{{ status }}</p>

      <div v-if="publication.id" class="publication-meta">
        <span>发布修订 {{ publication.revision }}</span>
        <strong :data-publication-status="publication.status">
          {{ publicationStatusLabel(publication.status) }}
        </strong>
      </div>

      <div
        v-if="publication.status === 'queued'"
        class="publication-notice"
        data-publication-notice="queued"
      >
        已进入插件执行队列，等待 Obsidian 桌面插件回报结果；这不代表文件已经写入。
      </div>
      <div
        v-else-if="publication.status === 'conflict'"
        class="publication-notice publication-notice-error"
        data-publication-notice="conflict"
      >
        插件检测到路径、系统标记或文件哈希冲突，未覆盖 Vault 中的文件。
      </div>
      <div
        v-else-if="publication.status === 'failed'"
        class="publication-notice publication-notice-error"
        data-publication-notice="failed"
      >
        插件执行失败，当前修订没有被标记为已应用。
      </div>
      <div
        v-else-if="publication.status === 'applied'"
        class="publication-notice publication-notice-success"
        data-publication-notice="applied"
      >
        插件已回报该发布修订应用成功。
      </div>

      <p v-if="!loading && !publication.id && !error" class="status-line">
        暂无发布预览。
      </p>

      <ol v-if="artifacts.length" class="publication-artifacts">
        <li v-for="artifact in artifacts" :key="artifact.revision_id || artifact.stable_id">
          <header>
            <div>
              <span>{{ artifactTypeLabel(artifact.artifact_type) }}</span>
              <h3>{{ artifact.target_path }}</h3>
            </div>
            <span :data-artifact-status="artifact.status">{{ artifactStatusLabel(artifact.status) }}</span>
          </header>
          <dl>
            <div>
              <dt>内容哈希</dt>
              <dd><code>{{ artifact.content_hash }}</code></dd>
            </div>
            <div>
              <dt>预期 Vault 哈希</dt>
              <dd>
                <code v-if="artifact.expected_vault_hash">{{ artifact.expected_vault_hash }}</code>
                <span v-else>无（按新文件处理）</span>
              </dd>
            </div>
          </dl>
          <details open>
            <summary>完整 Markdown 内容</summary>
            <pre>{{ artifact.content }}</pre>
          </details>
        </li>
      </ol>

      <footer class="publication-footer">
        <p>确认后仅进入插件队列；最终状态以插件执行结果为准。</p>
        <div>
          <button type="button" data-publication-action="cancel" @click="emit('close')">
            取消
          </button>
          <button
            v-if="publication.status === 'draft'"
            type="button"
            :disabled="loading"
            data-publication-action="confirm"
            @click="confirmPublication"
          >
            {{ loading ? "提交中..." : "确认并交给插件执行" }}
          </button>
        </div>
      </footer>
    </section>
  </div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  open: {
    type: Boolean,
    default: false,
  },
  preview: {
    type: Object,
    default: () => ({}),
  },
  loading: {
    type: Boolean,
    default: false,
  },
  error: {
    type: String,
    default: "",
  },
  status: {
    type: String,
    default: "",
  },
});

const emit = defineEmits(["close", "confirm"]);

const previewData = computed(() => props.preview || {});
const publication = computed(() => previewData.value.publication || {});
const artifacts = computed(() => (
  Array.isArray(publication.value.artifacts) ? publication.value.artifacts : []
));

function confirmPublication() {
  if (publication.value.status !== "draft" || !publication.value.id || props.loading) return;
  emit("confirm", { publicationId: publication.value.id });
}

function publicationStatusLabel(value) {
  const labels = {
    draft: "待确认",
    confirmed: "已确认",
    queued: "等待插件执行",
    applied: "已应用",
    conflict: "冲突，未覆盖",
    failed: "执行失败",
  };
  return labels[value] || value || "未知状态";
}

function artifactStatusLabel(value) {
  const labels = {
    draft: "待确认",
    queued: "等待执行",
    applied: "已应用",
    conflict: "冲突",
    failed: "失败",
  };
  return labels[value] || value || "未知状态";
}

function artifactTypeLabel(value) {
  const labels = {
    project_understanding: "项目理解",
    knowledge_coverage: "知识覆盖与技能差距",
    learning_plan: "学习计划",
    assessment_record: "评估记录",
  };
  return labels[value] || value || "受管产物";
}
</script>

<style scoped>
.publication-backdrop {
  position: fixed;
  inset: 0;
  z-index: 50;
  display: grid;
  place-items: center;
  padding: var(--space-4);
  background: rgb(17 17 17 / 32%);
}

.publication-dialog {
  width: min(940px, 96vw);
  max-height: 92vh;
  overflow-y: auto;
  padding: var(--space-5);
  color: var(--text-primary);
  background: var(--surface-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
}

.publication-header,
.publication-meta,
.publication-artifacts header,
.publication-footer,
.publication-footer > div {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-3);
}

.publication-header h2,
.publication-artifacts h3 {
  margin: var(--space-1) 0;
}

.publication-meta,
.publication-notice {
  margin-top: var(--space-4);
  padding: var(--space-3);
  background: var(--surface-sunken);
  border-radius: var(--radius);
}

.publication-notice {
  color: var(--warning);
  background: var(--warning-soft);
}

.publication-notice-error {
  color: var(--danger);
  background: var(--danger-soft);
}

.publication-notice-success {
  color: var(--success);
  background: var(--success-soft);
}

.publication-artifacts {
  display: grid;
  gap: var(--space-4);
  padding: 0;
  list-style: none;
}

.publication-artifacts > li {
  padding: var(--space-4);
  background: var(--surface-sunken);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
}

.publication-artifacts dl {
  display: grid;
  gap: var(--space-2);
  margin: var(--space-3) 0;
}

.publication-artifacts dl div {
  display: grid;
  grid-template-columns: minmax(130px, auto) minmax(0, 1fr);
  gap: var(--space-3);
}

.publication-artifacts dd {
  min-width: 0;
  margin: 0;
  overflow-wrap: anywhere;
}

.publication-artifacts pre {
  max-height: none;
  overflow-x: auto;
  padding: var(--space-4);
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  background: var(--surface-card);
  border-radius: var(--radius);
}

.publication-footer {
  align-items: center;
  margin-top: var(--space-5);
  padding-top: var(--space-4);
  border-top: 1px solid var(--border);
}

.publication-footer > div {
  align-items: center;
}

@media (max-width: 700px) {
  .publication-header,
  .publication-footer,
  .publication-artifacts header {
    flex-direction: column;
  }
}
</style>

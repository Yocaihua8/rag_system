<template>
  <section class="view-panel learning-plan-view">
    <header class="topbar learning-plan-topbar">
      <div>
        <p class="section-kicker">学习计划</p>
        <h2>当前项目学习计划</h2>
        <p>{{ currentData.scope_notice || "学习计划仅针对当前项目和当前来源版本，不代表整体职业能力。" }}</p>
      </div>
      <div class="learning-plan-actions">
        <button
          type="button"
          :disabled="busy || !activeProjectId"
          data-learning-plan-action="refresh"
          @click="emit('refresh')"
        >
          刷新
        </button>
        <button
          type="button"
          :disabled="busy || !activeProjectId || stale"
          data-learning-plan-action="generate"
          @click="emit('generate')"
        >
          {{ generating ? "生成中..." : currentData.draft ? "生成新草稿" : "生成草稿" }}
        </button>
      </div>
    </header>

    <p v-if="error" class="status-line error">{{ error }}</p>
    <p v-if="status" class="status-line">{{ status }}</p>
    <p v-if="loading" class="status-line">正在读取当前项目学习计划...</p>
    <p v-else-if="!activeProjectId" class="status-line">请先选择项目。</p>

    <div v-if="stale" class="learning-plan-warning" role="alert">
      <strong>当前分析已过期。</strong>
      <p>请重新分析项目后再生成、编辑、确认或发布计划。已确认计划仍只按服务端权限记录任务进度。</p>
    </div>

    <nav
      v-if="currentData.draft && currentData.confirmed"
      class="learning-plan-tabs"
      aria-label="学习计划版本"
    >
      <button
        type="button"
        :class="{ active: selectedPlanKind === 'draft' }"
        data-learning-plan-tab="draft"
        @click="selectedPlanKind = 'draft'"
      >
        当前草稿
      </button>
      <button
        type="button"
        :class="{ active: selectedPlanKind === 'confirmed' }"
        data-learning-plan-tab="confirmed"
        @click="selectedPlanKind = 'confirmed'"
      >
        已确认计划
      </button>
    </nav>

    <section v-if="!loading && activeProjectId && !activePlan" class="learning-plan-empty">
      <p class="section-kicker">尚无计划</p>
      <h3>从当前项目知识差距生成学习任务</h3>
      <p>系统会保留已确认计划；再次生成只会创建新的可编辑草稿。</p>
      <button
        type="button"
        :disabled="generating || stale"
        data-learning-plan-action="generate-empty"
        @click="emit('generate')"
      >
        {{ generating ? "生成中..." : "生成学习计划草稿" }}
      </button>
    </section>

    <template v-else-if="activePlan">
      <section class="learning-plan-summary">
        <div>
          <p class="section-kicker">{{ activePlan.status === "draft" ? "可编辑草稿" : "执行中的计划" }}</p>
          <h3>修订 {{ activePlan.revision }} · {{ planStatusLabel(activePlan.status) }}</h3>
          <p>共 {{ activePlan.items?.length || 0 }} 项，预计 {{ totalMinutes }} 分钟。</p>
        </div>
        <div class="learning-plan-summary-actions">
          <button
            v-if="activePlan.status === 'draft'"
            type="button"
            :disabled="!canConfirm"
            data-learning-plan-action="confirm"
            @click="confirmDraft"
          >
            {{ confirming ? "确认中..." : "确认此计划" }}
          </button>
          <button
            v-if="currentData.confirmed"
            type="button"
            :disabled="publicationLoading || stale || !obsidianConnection"
            data-learning-plan-action="preview-publication"
            @click="emit('preview-publication')"
          >
            {{ publicationLoading ? "生成预览中..." : "预览发布到 Obsidian" }}
          </button>
          <button
            v-if="!obsidianConnection"
            type="button"
            data-learning-plan-action="open-obsidian-settings"
            @click="emit('open-obsidian-settings')"
          >
            连接 Obsidian
          </button>
        </div>
      </section>

      <p v-if="publicationError" class="status-line error">{{ publicationError }}</p>
      <p v-if="publicationStatus" class="status-line">{{ publicationStatus }}</p>
      <p v-if="currentData.confirmed && !obsidianConnection" class="muted-line">
        发布前需要先在设置中完成当前项目的 Obsidian 配对。
      </p>

      <form
        v-if="activePlan.status === 'draft'"
        class="learning-plan-editor"
        @submit.prevent="saveStructure"
      >
        <ol class="learning-plan-list">
          <li v-for="(item, index) in editableItems" :key="item.id || item.stable_key">
            <div class="learning-plan-item-heading">
              <div>
                <span class="learning-plan-index">任务 {{ index + 1 }}</span>
                <span>{{ item.item_type === "source_gap" ? "补充来源" : "项目学习" }}</span>
              </div>
              <div class="learning-plan-order-actions">
                <button
                  type="button"
                  :disabled="!canEditStructure || index === 0"
                  :aria-label="`上移任务 ${index + 1}`"
                  data-learning-plan-action="move-up"
                  @click="moveItem(index, -1)"
                >
                  上移
                </button>
                <button
                  type="button"
                  :disabled="!canEditStructure || index === editableItems.length - 1"
                  :aria-label="`下移任务 ${index + 1}`"
                  data-learning-plan-action="move-down"
                  @click="moveItem(index, 1)"
                >
                  下移
                </button>
              </div>
            </div>

            <label>
              学习目标
              <input
                v-model.trim="item.objective"
                :disabled="!canEditStructure"
                data-learning-plan-field="objective"
              />
            </label>
            <label>
              练习问题
              <textarea
                v-model.trim="item.practice_question"
                :disabled="!canEditStructure"
                data-learning-plan-field="practice-question"
              ></textarea>
            </label>
            <label>
              完成标准
              <textarea
                v-model.trim="item.completion_criteria"
                :disabled="!canEditStructure"
                data-learning-plan-field="completion-criteria"
              ></textarea>
            </label>
            <label class="learning-plan-minutes">
              预计时长（分钟）
              <input
                v-model.number="item.estimated_minutes"
                type="number"
                min="1"
                step="1"
                :disabled="!canEditStructure"
                data-learning-plan-field="estimated-minutes"
              />
            </label>

            <div class="learning-plan-source-row">
              <span>
                知识点 {{ item.knowledge_point_id || "未关联" }} ·
                技能 {{ item.skill_node_id || "未关联" }}
              </span>
              <button
                type="button"
                :disabled="!(item.source_ids || []).length"
                data-learning-plan-action="open-sources"
                @click="openSources(item)"
              >
                查看阅读来源（{{ item.source_ids?.length || 0 }}）
              </button>
            </div>
          </li>
        </ol>
        <div class="learning-plan-footer-actions">
          <button
            type="submit"
            :disabled="!canSaveStructure"
            data-learning-plan-action="save"
          >
            {{ saving ? "保存中..." : "保存草稿" }}
          </button>
        </div>
      </form>

      <section v-else class="learning-plan-progress">
        <ol class="learning-plan-list">
          <li v-for="(item, index) in activePlan.items || []" :key="item.id || item.stable_key">
            <div class="learning-plan-item-heading">
              <div>
                <span class="learning-plan-index">任务 {{ index + 1 }}</span>
                <h4>{{ item.objective }}</h4>
              </div>
              <label class="learning-plan-status-field">
                任务状态
                <select
                  v-model="progressStatuses[item.id || item.stable_key]"
                  :disabled="!activePlan.can_update_progress || saving"
                  data-learning-plan-field="status"
                >
                  <option value="todo">待开始</option>
                  <option value="in_progress">进行中</option>
                  <option value="done">已完成</option>
                  <option value="skipped">已跳过</option>
                </select>
              </label>
            </div>
            <dl class="learning-plan-readonly-details">
              <div>
                <dt>练习问题</dt>
                <dd>{{ item.practice_question }}</dd>
              </div>
              <div>
                <dt>完成标准</dt>
                <dd>{{ item.completion_criteria }}</dd>
              </div>
              <div>
                <dt>预计时长</dt>
                <dd>{{ item.estimated_minutes }} 分钟</dd>
              </div>
            </dl>
            <button
              type="button"
              :disabled="!(item.source_ids || []).length"
              data-learning-plan-action="open-sources"
              @click="openSources(item)"
            >
              查看阅读来源（{{ item.source_ids?.length || 0 }}）
            </button>
          </li>
        </ol>
        <div class="learning-plan-footer-actions">
          <button
            type="button"
            :disabled="saving || !activePlan.can_update_progress"
            data-learning-plan-action="save-progress"
            @click="saveProgress"
          >
            {{ saving ? "保存中..." : "保存任务进度" }}
          </button>
        </div>
      </section>
    </template>
  </section>
</template>

<script setup>
import { computed, ref, watch } from "vue";

const props = defineProps({
  projectId: {
    type: String,
    default: "",
  },
  selectedProjectId: {
    type: String,
    default: "",
  },
  currentPlan: {
    type: Object,
    default: () => ({}),
  },
  loading: {
    type: Boolean,
    default: false,
  },
  generating: {
    type: Boolean,
    default: false,
  },
  saving: {
    type: Boolean,
    default: false,
  },
  confirming: {
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
  obsidianConnection: {
    type: Object,
    default: null,
  },
  publicationLoading: {
    type: Boolean,
    default: false,
  },
  publicationError: {
    type: String,
    default: "",
  },
  publicationStatus: {
    type: String,
    default: "",
  },
});

const emit = defineEmits([
  "generate",
  "refresh",
  "update-plan",
  "confirm",
  "preview-publication",
  "open-sources",
  "open-obsidian-settings",
]);

const selectedPlanKind = ref("draft");
const editableItems = ref([]);
const progressStatuses = ref({});

const activeProjectId = computed(() => props.projectId || props.selectedProjectId);
const currentData = computed(() => props.currentPlan?.current || props.currentPlan || {});
const stale = computed(() => Boolean(currentData.value.stale));
const busy = computed(() => props.loading || props.generating);
const activePlan = computed(() => {
  if (selectedPlanKind.value === "confirmed") {
    return currentData.value.confirmed || currentData.value.draft || null;
  }
  return currentData.value.draft || currentData.value.confirmed || null;
});
const totalMinutes = computed(() => (
  activePlan.value?.items || []
).reduce((total, item) => total + (Number(item.estimated_minutes) || 0), 0));
const canEditStructure = computed(() => Boolean(
  activePlan.value?.status === "draft"
  && activePlan.value?.can_edit_structure
  && !stale.value
  && !props.saving,
));
const canSaveStructure = computed(() => (
  canEditStructure.value
  && editableItems.value.length > 0
  && editableItems.value.every(validEditableItem)
));
const canConfirm = computed(() => Boolean(
  activePlan.value?.status === "draft"
  && activePlan.value?.can_confirm
  && !stale.value
  && !props.confirming
  && !props.saving,
));

watch(
  () => [currentData.value.draft?.id, currentData.value.confirmed?.id],
  ([draftId, confirmedId]) => {
    if (selectedPlanKind.value === "draft" && !draftId && confirmedId) {
      selectedPlanKind.value = "confirmed";
    } else if (selectedPlanKind.value === "confirmed" && !confirmedId && draftId) {
      selectedPlanKind.value = "draft";
    }
  },
  { immediate: true },
);

watch(
  activePlan,
  (plan) => {
    editableItems.value = (plan?.items || []).map((item) => ({
      ...item,
      source_ids: [...(item.source_ids || [])],
      reading_sources: (item.reading_sources || []).map((source) => ({ ...source })),
    }));
    progressStatuses.value = Object.fromEntries(
      (plan?.items || []).map((item) => [
        item.id || item.stable_key,
        item.status || "todo",
      ]),
    );
  },
  { immediate: true },
);

function validEditableItem(item) {
  return Boolean(
    String(item.stable_key || "").trim()
    && String(item.item_type || "").trim()
    && String(item.objective || "").trim()
    && String(item.practice_question || "").trim()
    && String(item.completion_criteria || "").trim()
    && Number.isInteger(Number(item.estimated_minutes))
    && Number(item.estimated_minutes) > 0,
  );
}

function moveItem(index, offset) {
  if (!canEditStructure.value) return;
  const target = index + offset;
  if (target < 0 || target >= editableItems.value.length) return;
  const items = [...editableItems.value];
  [items[index], items[target]] = [items[target], items[index]];
  editableItems.value = items;
}

function serializeItem(item, sortOrder) {
  return {
    stable_key: String(item.stable_key || "").trim(),
    item_type: String(item.item_type || "learning").trim(),
    objective: String(item.objective || "").trim(),
    knowledge_point_id: String(item.knowledge_point_id || "").trim(),
    skill_node_id: String(item.skill_node_id || "").trim(),
    source_ids: [...(item.source_ids || [])],
    practice_question: String(item.practice_question || "").trim(),
    completion_criteria: String(item.completion_criteria || "").trim(),
    estimated_minutes: Number(item.estimated_minutes),
    status: String(item.status || "todo").trim() || "todo",
    sort_order: sortOrder,
  };
}

function saveStructure() {
  if (!canSaveStructure.value || !activePlan.value) return;
  emit("update-plan", {
    planId: activePlan.value.id,
    items: editableItems.value.map(serializeItem),
    expectedRevision: activePlan.value.revision,
    expectedItemsHash: activePlan.value.items_hash,
  });
}

function confirmDraft() {
  if (!canConfirm.value || !activePlan.value) return;
  emit("confirm", {
    planId: activePlan.value.id,
    expectedRevision: activePlan.value.revision,
    expectedItemsHash: activePlan.value.items_hash,
  });
}

function saveProgress() {
  if (!activePlan.value?.can_update_progress || props.saving) return;
  emit("update-plan", {
    planId: activePlan.value.id,
    itemStatuses: { ...progressStatuses.value },
    expectedProgressHash: activePlan.value.progress_hash,
  });
}

function openSources(item) {
  const sources = { ...(currentData.value.sources || {}) };
  for (const source of item.reading_sources || []) {
    if (source?.id) {
      sources[source.id] = source;
    }
  }
  emit("open-sources", {
    title: item.objective || "学习任务来源",
    source_ids: [...(item.source_ids || [])],
    sources,
  });
}

function planStatusLabel(statusValue) {
  const labels = {
    draft: "草稿",
    confirmed: "已确认",
    archived: "历史版本",
  };
  return labels[statusValue] || statusValue;
}
</script>

<style scoped>
.learning-plan-view {
  overflow-y: auto;
}

.learning-plan-topbar,
.learning-plan-actions,
.learning-plan-summary,
.learning-plan-summary-actions,
.learning-plan-item-heading,
.learning-plan-order-actions,
.learning-plan-source-row,
.learning-plan-footer-actions {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-3);
}

.learning-plan-actions,
.learning-plan-summary-actions,
.learning-plan-order-actions,
.learning-plan-footer-actions {
  align-items: center;
  justify-content: flex-start;
  flex-wrap: wrap;
}

.learning-plan-warning,
.learning-plan-empty,
.learning-plan-summary {
  margin-top: var(--space-4);
  padding: var(--space-4);
  background: var(--surface-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
}

.learning-plan-warning {
  color: var(--warning);
  background: var(--warning-soft);
}

.learning-plan-warning p {
  margin-bottom: 0;
}

.learning-plan-tabs {
  display: flex;
  gap: var(--space-2);
  margin-top: var(--space-4);
}

.learning-plan-tabs button.active {
  color: var(--accent);
  border-color: var(--accent);
}

.learning-plan-summary h3,
.learning-plan-item-heading h4 {
  margin: var(--space-1) 0;
}

.learning-plan-editor,
.learning-plan-progress {
  margin-top: var(--space-4);
}

.learning-plan-list {
  display: grid;
  gap: var(--space-4);
  padding: 0;
  list-style: none;
}

.learning-plan-list > li {
  display: grid;
  gap: var(--space-4);
  padding: var(--space-5);
  background: var(--surface-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
}

.learning-plan-list label {
  display: grid;
  gap: var(--space-2);
}

.learning-plan-list input,
.learning-plan-list textarea,
.learning-plan-list select {
  width: 100%;
}

.learning-plan-list textarea {
  min-height: 88px;
  resize: vertical;
}

.learning-plan-minutes,
.learning-plan-status-field {
  width: min(220px, 100%);
}

.learning-plan-index {
  margin-right: var(--space-2);
  color: var(--text-secondary);
  font-size: var(--text-sm);
}

.learning-plan-source-row {
  align-items: center;
  color: var(--text-secondary);
  font-size: var(--text-sm);
}

.learning-plan-readonly-details {
  display: grid;
  gap: var(--space-3);
  margin: 0;
}

.learning-plan-readonly-details div {
  display: grid;
  gap: var(--space-1);
}

.learning-plan-readonly-details dt {
  color: var(--text-secondary);
  font-size: var(--text-sm);
}

.learning-plan-readonly-details dd {
  margin: 0;
}

@media (max-width: 760px) {
  .learning-plan-topbar,
  .learning-plan-summary,
  .learning-plan-item-heading,
  .learning-plan-source-row {
    flex-direction: column;
  }
}
</style>

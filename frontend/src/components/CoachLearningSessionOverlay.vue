<template>
  <div
    v-if="open"
    class="coach-learning-backdrop"
    data-coach-learning-backdrop
    @click.self="emit('close')"
  >
    <section
      class="coach-learning-overlay"
      role="dialog"
      aria-modal="true"
      aria-labelledby="coach-learning-title"
    >
      <header class="coach-learning-header">
        <div>
          <p class="section-kicker">逐点学习</p>
          <h2 id="coach-learning-title">当前项目知识学习</h2>
          <p>讲解、练习和结果只对应当前项目及当前来源版本。</p>
        </div>
        <button
          type="button"
          data-coach-learning-action="close"
          @click="emit('close')"
        >
          关闭
        </button>
      </header>

      <p v-if="error" class="status-line error" role="alert">{{ error }}</p>
      <p v-if="loading && !hasSession" class="coach-learning-loading" aria-live="polite">
        正在恢复学习会话...
      </p>
      <form
        v-else-if="!hasSession"
        class="coach-learning-target"
        data-coach-learning-action="start"
        @submit.prevent="startSession"
      >
        <p>选择当前项目中的一个知识点或技能节点，学习会话每次只展示一个知识点。</p>
        <label>
          学习目标类型
          <select v-model="targetType" data-coach-learning-field="target-type">
            <option value="knowledge_point">项目知识点</option>
            <option value="skill">技能节点（当前项目）</option>
          </select>
        </label>
        <label>
          学习目标
          <select v-model="targetId" data-coach-learning-field="target-id">
            <option value="">请选择</option>
            <option v-for="target in availableTargets" :key="target.id" :value="target.id">
              {{ target.title || target.name || target.stable_key }}
            </option>
          </select>
        </label>
        <p v-if="availableTargets.length === 0" class="muted-line">
          暂无可学习目标，请先在学习地图完成当前项目分析。
        </p>
        <button type="submit" :disabled="loading || !targetId">开始逐点学习</button>
      </form>

      <template v-else>
        <div class="coach-learning-progress" aria-label="学习进度">
          <div>
            <span>{{ progressLabel }}</span>
            <strong>{{ progressPercent }}%</strong>
          </div>
          <progress :value="progressCompleted" :max="progressTotal"></progress>
        </div>

        <p v-if="isStale" class="coach-learning-warning" role="status">
          当前来源版本已变化，本次会话只能查看。请重新分析项目后开始新的学习会话。
        </p>
        <p v-else-if="loading" class="coach-learning-loading" aria-live="polite">
          正在更新学习状态...
        </p>

        <section v-if="sessionData.status === 'completed'" class="coach-learning-complete">
          <p class="section-kicker">完成</p>
          <h3>本次逐点学习已完成</h3>
          <p>学习结果已按当前项目和来源版本记录，可返回学习地图查看掌握状态。</p>
        </section>

        <section v-else-if="sessionData.status === 'abandoned'" class="coach-learning-complete">
          <p class="section-kicker">已结束</p>
          <h3>本次学习会话已放弃</h3>
          <p>历史作答仍会保留，但不会把打开或放弃会话当作计划完成证据。</p>
        </section>

        <section v-else-if="currentStep" class="coach-learning-step">
          <div class="coach-learning-step-heading">
            <div>
              <p class="section-kicker">{{ progressLabel }}</p>
              <h3>{{ currentStep.title || "当前知识点" }}</h3>
            </div>
            <span v-if="sessionData.status" class="coach-learning-status">
              {{ statusLabel(sessionData.status) }}
            </span>
          </div>

          <p
            v-if="currentStep.explanation"
            class="coach-learning-explanation"
          >
            {{ currentStep.explanation }}
          </p>

          <section v-if="contextContent" class="coach-learning-context">
            <p class="section-kicker">{{ contextTitle }}</p>
            <pre>{{ contextContent }}</pre>
          </section>

          <section class="coach-learning-sources">
            <div class="coach-learning-section-heading">
              <p class="section-kicker">当前项目真实来源</p>
              <button
                v-if="visibleSources.length"
                type="button"
                data-coach-learning-source-action="open"
                @click="openSources"
              >
                查看完整来源
              </button>
            </div>
            <p v-if="visibleSources.length === 0" class="muted-line">暂无可展示来源。</p>
            <ol v-else>
              <li v-for="source in visibleSources" :key="source.id || source.path || source.source_path">
                <strong>{{ source.path || source.source_path || "未知路径" }}</strong>
                <p v-if="source.excerpt">{{ source.excerpt }}</p>
                <p v-else class="muted-line">无片段预览。</p>
              </li>
            </ol>
          </section>

          <section v-if="currentExercise" class="coach-learning-exercise">
            <p class="section-kicker">{{ exerciseTypeLabel(currentExercise.question_type) }}</p>
            <h4>{{ currentExercise.prompt || "完成当前练习" }}</h4>

            <section v-if="fixtureTables.length" class="coach-learning-fixture">
              <p v-if="fixtureNotice" class="coach-learning-fixture-notice">
                {{ fixtureNotice }}
              </p>
              <article
                v-for="table in fixtureTables"
                :key="table.name"
                class="coach-learning-table-card"
              >
                <div class="coach-learning-table-heading">
                  <span>样例表</span>
                  <strong>{{ table.name }}</strong>
                </div>
                <div class="coach-learning-table-scroll">
                  <table>
                    <thead>
                      <tr>
                        <th v-for="column in tableColumns(table)" :key="column.name">
                          <span>{{ column.name }}</span>
                          <small>{{ column.type || "TEXT" }}{{ column.nullable === false ? " · NOT NULL" : "" }}</small>
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="(row, rowIndex) in tableRows(table)" :key="rowIndex">
                        <td
                          v-for="(column, columnIndex) in tableColumns(table)"
                          :key="column.name"
                        >
                          {{ formatCell(rowCell(row, column, columnIndex)) }}
                        </td>
                      </tr>
                      <tr v-if="tableRows(table).length === 0">
                        <td :colspan="Math.max(tableColumns(table).length, 1)">空结果样例</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </article>
            </section>

            <form
              v-if="showsAnswerForm"
              class="coach-learning-answer"
              data-coach-learning-action="submit"
              @submit.prevent="submitAttempt"
            >
              <label :for="answerFieldId">
                {{ currentExercise.question_type === "sql_query" ? "你的 SQL" : "你的回答" }}
              </label>
              <textarea
                :id="answerFieldId"
                v-model="answer"
                data-coach-learning-field="answer"
                :disabled="interactionBlocked"
                :placeholder="answerPlaceholder"
                spellcheck="false"
              ></textarea>
              <p v-if="currentExercise.question_type === 'sql_query'" class="muted-line">
                仅执行当前固定练习数据上的单条只读查询，不连接项目正式数据库。
              </p>
              <button
                type="submit"
                :disabled="interactionBlocked || !answer.trim()"
              >
                {{ submitting ? "正在批改..." : "提交本题" }}
              </button>
            </form>

            <section v-if="latestAttempt" class="coach-learning-feedback" aria-live="polite">
              <div class="coach-learning-feedback-heading">
                <div>
                  <p class="section-kicker">第 {{ latestAttempt.attempt_no || attempts.length }} 次作答</p>
                  <h4>{{ attemptResultLabel(latestAttempt) }}</h4>
                </div>
                <strong>得分 {{ scorePercent(latestAttempt.score) }}%</strong>
              </div>
              <p v-if="latestAttempt.feedback">{{ latestAttempt.feedback }}</p>
              <p v-if="attemptError" class="status-line error">{{ attemptError }}</p>
              <p v-if="latestAttempt.counts_for_mastery === false" class="coach-learning-warning">
                本次作答仅用于练习，不计入独立掌握证据。
              </p>

              <div v-if="previewColumns.length" class="coach-learning-preview">
                <p class="section-kicker">本次结果预览</p>
                <div class="coach-learning-table-scroll">
                  <table>
                    <thead>
                      <tr>
                        <th v-for="column in previewColumns" :key="column">{{ column }}</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="(row, rowIndex) in previewRows" :key="rowIndex">
                        <td v-for="(column, columnIndex) in previewColumns" :key="column">
                          {{ formatCell(rowCell(row, { name: column }, columnIndex)) }}
                        </td>
                      </tr>
                      <tr v-if="previewRows.length === 0">
                        <td :colspan="previewColumns.length">查询返回空结果。</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </section>

            <section
              v-if="answerIsRevealed && revealedAnswer"
              class="coach-learning-revealed-answer"
            >
              <p class="section-kicker">参考答案</p>
              <pre>{{ revealedAnswer }}</pre>
              <p>继续作答可用于练习，但已查看本题答案后的 attempt 不计入独立掌握证据。</p>
            </section>
          </section>

          <div v-if="!isReadOnly" class="coach-learning-actions">
            <button
              v-if="allows('begin_learning')"
              type="button"
              data-coach-learning-action="begin-learning"
              :disabled="interactionBlocked"
              @click="transition('begin_learning')"
            >
              开始学习
            </button>
            <button
              v-if="allows('begin_question')"
              type="button"
              data-coach-learning-action="begin-question"
              :disabled="interactionBlocked"
              @click="transition('begin_question')"
            >
              开始本题
            </button>
            <button
              v-if="allows('retry')"
              type="button"
              data-coach-learning-action="retry"
              :disabled="interactionBlocked"
              @click="transition('retry')"
            >
              重新作答
            </button>
            <button
              v-if="allows('reveal')"
              type="button"
              data-coach-learning-action="reveal"
              :disabled="interactionBlocked"
              @click="transition('reveal')"
            >
              查看答案
            </button>
            <button
              v-if="allows('next')"
              type="button"
              data-coach-learning-action="next"
              :disabled="interactionBlocked"
              @click="transition('next')"
            >
              {{ isLastStep ? "完成学习" : "下一知识点" }}
            </button>
            <button
              v-if="allows('abandon')"
              type="button"
              class="coach-learning-secondary"
              data-coach-learning-action="abandon"
              :disabled="interactionBlocked"
              @click="transition('abandon')"
            >
              放弃本次会话
            </button>
          </div>
        </section>

      </template>
    </section>
  </div>
</template>

<script setup>
import { computed, ref, watch } from "vue";

const props = defineProps({
  open: {
    type: Boolean,
    default: false,
  },
  session: {
    type: Object,
    default: null,
  },
  loading: {
    type: Boolean,
    default: false,
  },
  submitting: {
    type: Boolean,
    default: false,
  },
  error: {
    type: String,
    default: "",
  },
  knowledgePoints: {
    type: [Array, Object],
    default: () => [],
  },
  skills: {
    type: [Array, Object],
    default: () => [],
  },
  initialTarget: {
    type: Object,
    default: null,
  },
});

const emit = defineEmits(["close", "open-sources", "start", "transition", "submit-attempt"]);
const answer = ref("");
const idempotencyKey = ref(createIdempotencyKey());
const targetType = ref(props.initialTarget?.target_type || "knowledge_point");
const targetId = ref(props.initialTarget?.target_id || "");

const sessionData = computed(() => props.session?.session || props.session || {});
const hasSession = computed(() => Boolean(sessionData.value.id));
const currentStep = computed(() => sessionData.value.current_step || null);
const currentExercise = computed(
  () => sessionData.value.current_exercise || currentStep.value?.current_exercise || null,
);
const attempts = computed(() => {
  const value = sessionData.value.attempts || currentStep.value?.attempts;
  return Array.isArray(value) ? value : [];
});
const latestAttempt = computed(() => attempts.value.reduce((latest, attempt) => {
  if (!latest) return attempt;
  return Number(attempt.attempt_no || 0) >= Number(latest.attempt_no || 0) ? attempt : latest;
}, null));
const allowedActions = computed(() => new Set(
  Array.isArray(sessionData.value.allowed_actions) ? sessionData.value.allowed_actions : [],
));
const isReadOnly = computed(() => Boolean(sessionData.value.read_only));
const isStale = computed(
  () => isReadOnly.value
    && !["completed", "abandoned"].includes(sessionData.value.status),
);
const interactionBlocked = computed(
  () => props.loading || props.submitting || isReadOnly.value,
);
const showsAnswerForm = computed(
  () => Boolean(currentExercise.value)
    && ["awaiting_answer", "retrying"].includes(sessionData.value.status)
    && allows("submit"),
);
const progressTotal = computed(() => Math.max(
  Number(sessionData.value.progress?.total || sessionData.value.step_count || 1),
  1,
));
const progressCurrent = computed(() => Math.min(
  Math.max(Number(sessionData.value.progress?.current || 1), 1),
  progressTotal.value,
));
const progressCompleted = computed(() => Math.min(
  Math.max(Number(
    sessionData.value.progress?.completed
      ?? (sessionData.value.status === "completed"
        ? progressTotal.value
        : Math.max(progressCurrent.value - 1, 0)),
  ), 0),
  progressTotal.value,
));
const progressLabel = computed(() => `知识点 ${progressCurrent.value} / ${progressTotal.value}`);
const progressPercent = computed(() => Math.round(
  (progressCompleted.value / progressTotal.value) * 100,
));
const isLastStep = computed(() => progressCurrent.value >= progressTotal.value);
const contextTitle = computed(() => {
  const context = currentStep.value?.context;
  return typeof context === "object" && context ? context.title || "项目上下文" : "项目上下文";
});
const contextContent = computed(() => {
  const context = currentStep.value?.context;
  if (typeof context === "string") return context;
  if (!context || typeof context !== "object") return "";
  return context.content || context.code || context.example || "";
});
const sourceIndex = computed(() => {
  const value = sessionData.value.sources || {};
  if (Array.isArray(value)) {
    return Object.fromEntries(
      value
        .filter((source) => source && typeof source === "object")
        .map((source) => [source.id || source.path || source.source_path, source]),
    );
  }
  return value;
});
const currentSourceIds = computed(() => {
  const value = currentStep.value?.source_ids || [];
  return Array.isArray(value) ? value : [];
});
const visibleSources = computed(() => currentSourceIds.value
  .map((sourceId) => sourceIndex.value[sourceId])
  .filter(Boolean));
const fixture = computed(
  () => currentExercise.value?.fixture || currentExercise.value?.sql_fixture || {},
);
const fixtureTables = computed(() => {
  if (Array.isArray(fixture.value.tables)) return fixture.value.tables;
  if (!Array.isArray(fixture.value.schema)) return [];
  const seedRows = fixture.value.seed_rows || {};
  return fixture.value.schema.map((table) => ({
    ...table,
    sample_rows: Array.isArray(seedRows[table.name]) ? seedRows[table.name] : [],
  }));
});
const fixtureNotice = computed(() => fixture.value.notice
  || (fixtureTables.value.length
    ? "以下是固定练习数据，不是项目正式数据库内容。"
    : ""));
const preview = computed(() => latestAttempt.value?.result_preview || {});
const previewColumns = computed(() => {
  const columns = preview.value.columns;
  return Array.isArray(columns)
    ? columns.map((column) => typeof column === "object" ? column.name : column).filter(Boolean)
    : [];
});
const previewRows = computed(() => Array.isArray(preview.value.rows) ? preview.value.rows : []);
const attemptError = computed(() => {
  const value = latestAttempt.value?.error || latestAttempt.value?.error_message;
  if (!value) return "";
  if (typeof value === "string") return value;
  return value.message || value.detail || value.code || "本次执行失败，请根据反馈调整答案。";
});
const answerIsRevealed = computed(
  () => Boolean(
    currentExercise.value?.answer_revealed
      || currentExercise.value?.revealed
      || currentExercise.value?.revealed_at,
  ),
);
const revealedAnswer = computed(
  () => currentExercise.value?.revealed_answer || currentExercise.value?.reference_answer || "",
);
const answerFieldId = computed(
  () => `coach-learning-answer-${currentExercise.value?.id || "current"}`,
);
const answerPlaceholder = computed(() => currentExercise.value?.question_type === "sql_query"
  ? "SELECT ...\nFROM ..."
  : "结合当前项目来源说明你的理解");
const knowledgePointItems = computed(
  () => normalizeItems(props.knowledgePoints, "knowledge_points"),
);
const skillItems = computed(
  () => normalizeItems(props.skills, "skills"),
);
const availableTargets = computed(() => targetType.value === "skill"
  ? skillItems.value.filter((skill) => (
    skill.project_evidence !== "no_project_evidence"
    && skill.assessment_state !== "no_project_evidence"
  ))
  : knowledgePointItems.value);

watch(
  () => [
    currentExercise.value?.id || "",
    attempts.value.length,
    sessionData.value.status,
  ],
  (current, previous) => {
    const exerciseChanged = current[0] !== previous?.[0];
    const attemptRecorded = current[1] !== previous?.[1];
    const enteredRetry = current[2] === "retrying" && previous?.[2] !== "retrying";
    if (exerciseChanged || attemptRecorded || enteredRetry) {
      answer.value = "";
      idempotencyKey.value = createIdempotencyKey();
    }
  },
);

watch(
  () => props.initialTarget,
  (target) => {
    if (!target) {
      targetType.value = "knowledge_point";
      targetId.value = "";
      return;
    }
    targetType.value = target.target_type || "knowledge_point";
    targetId.value = target.target_id || "";
  },
  { deep: true },
);

watch(targetType, () => {
  if (!availableTargets.value.some((target) => target.id === targetId.value)) {
    targetId.value = "";
  }
});

function createIdempotencyKey() {
  if (typeof globalThis.crypto?.randomUUID === "function") {
    return globalThis.crypto.randomUUID();
  }
  return `coach-learning-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function allows(action) {
  return allowedActions.value.has(action);
}

function normalizeItems(value, responseKey) {
  if (Array.isArray(value)) return value;
  const unwrapped = value?.[responseKey] || value || {};
  return Array.isArray(unwrapped.items) ? unwrapped.items : [];
}

function startSession() {
  if (props.loading || !targetId.value) return;
  emit("start", {
    target_type: targetType.value,
    target_id: targetId.value,
    origin_type: "coach",
  });
}

function transition(action) {
  if (interactionBlocked.value || !allows(action)) return;
  emit("transition", {
    session_id: sessionData.value.id,
    expected_version: sessionData.value.version,
    action,
  });
}

function submitAttempt() {
  if (
    interactionBlocked.value
    || !currentExercise.value
    || !answer.value.trim()
    || !allows("submit")
  ) {
    return;
  }
  emit("submit-attempt", {
    session_id: sessionData.value.id,
    exercise_id: currentExercise.value.id,
    answer: answer.value,
    expected_version: sessionData.value.version,
    idempotency_key: idempotencyKey.value,
  });
}

function openSources() {
  emit("open-sources", {
    title: currentStep.value?.title || "当前知识点来源",
    source_ids: currentSourceIds.value,
    sources: sourceIndex.value,
  });
}

function tableColumns(table) {
  return Array.isArray(table?.columns)
    ? table.columns.map((column) => typeof column === "string" ? { name: column } : column)
    : [];
}

function tableRows(table) {
  const rows = table?.sample_rows || table?.rows;
  return Array.isArray(rows) ? rows : [];
}

function rowCell(row, column, columnIndex) {
  if (Array.isArray(row)) return row[columnIndex];
  if (row && typeof row === "object") return row[column.name];
  return undefined;
}

function formatCell(value) {
  if (value === null) return "NULL";
  if (value === undefined) return "—";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

function scorePercent(value) {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? Math.round(numeric * 100) : 0;
}

function attemptResultLabel(attempt) {
  if (attempt.status === "grading") return "正在批改";
  if (Number(attempt.score) >= 0.75) return "本题已达标";
  if (attempt.error) return "执行未完成";
  return "本题需要巩固";
}

function exerciseTypeLabel(value) {
  const labels = {
    concept: "概念理解",
    flow: "流程说明",
    code_location: "代码定位",
    sql_query: "SQL 查询练习",
  };
  return labels[value] || "项目练习";
}

function statusLabel(value) {
  const labels = {
    ready: "准备开始",
    learning: "正在学习",
    awaiting_answer: "等待作答",
    evaluated: "已批改",
    retrying: "巩固作答",
    completed: "已完成",
    abandoned: "已放弃",
  };
  return labels[value] || value;
}
</script>

<style scoped>
.coach-learning-backdrop {
  position: fixed;
  inset: 0;
  z-index: 45;
  display: grid;
  place-items: center;
  padding: var(--space-4);
  background: rgb(17 17 17 / 32%);
}

.coach-learning-overlay {
  width: min(880px, 96vw);
  max-height: 92vh;
  overflow-y: auto;
  padding: var(--space-5);
  color: var(--text-primary);
  background: var(--surface-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
}

.coach-learning-header,
.coach-learning-step-heading,
.coach-learning-section-heading,
.coach-learning-feedback-heading,
.coach-learning-table-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-4);
}

.coach-learning-header h2,
.coach-learning-step-heading h3,
.coach-learning-exercise h4 {
  margin: var(--space-1) 0;
}

.coach-learning-progress {
  display: grid;
  gap: var(--space-2);
  margin-top: var(--space-5);
}

.coach-learning-target {
  display: grid;
  gap: var(--space-3);
  margin-top: var(--space-5);
}

.coach-learning-target label {
  display: grid;
  gap: var(--space-2);
}

.coach-learning-target select {
  width: 100%;
}

.coach-learning-progress div {
  display: flex;
  justify-content: space-between;
  gap: var(--space-3);
}

.coach-learning-progress progress {
  width: 100%;
  accent-color: var(--accent);
}

.coach-learning-loading,
.coach-learning-warning {
  padding: var(--space-3);
  border-radius: var(--radius);
}

.coach-learning-loading {
  color: var(--text-secondary);
  background: var(--surface-sunken);
}

.coach-learning-warning {
  color: var(--warning);
  background: var(--warning-soft);
}

.coach-learning-step,
.coach-learning-complete {
  margin-top: var(--space-5);
  padding: var(--space-4);
  background: var(--surface-sunken);
  border-radius: var(--radius-lg);
}

.coach-learning-status {
  flex: 0 0 auto;
  padding: var(--space-1) var(--space-3);
  color: var(--text-secondary);
  background: var(--surface-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-pill);
  font-size: var(--text-sm);
}

.coach-learning-explanation {
  font-size: var(--text-md);
  line-height: 1.7;
}

.coach-learning-context,
.coach-learning-sources,
.coach-learning-exercise,
.coach-learning-feedback,
.coach-learning-revealed-answer {
  margin-top: var(--space-4);
  padding-top: var(--space-4);
  border-top: 1px solid var(--border);
}

.coach-learning-context pre,
.coach-learning-revealed-answer pre {
  overflow-x: auto;
  padding: var(--space-3);
  white-space: pre-wrap;
  color: var(--text-primary);
  background: var(--surface-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  font-family: var(--font-mono);
}

.coach-learning-sources ol {
  display: grid;
  gap: var(--space-3);
  padding: 0;
  list-style: none;
}

.coach-learning-sources li {
  padding: var(--space-3);
  background: var(--surface-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
}

.coach-learning-sources li p {
  margin: var(--space-2) 0 0;
  white-space: pre-wrap;
}

.coach-learning-fixture {
  display: grid;
  gap: var(--space-3);
  margin-top: var(--space-4);
}

.coach-learning-fixture-notice {
  margin: 0;
  color: var(--text-secondary);
}

.coach-learning-table-card {
  padding: var(--space-3);
  background: var(--surface-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
}

.coach-learning-table-heading {
  justify-content: flex-start;
  margin-bottom: var(--space-2);
}

.coach-learning-table-heading span {
  color: var(--text-secondary);
}

.coach-learning-table-scroll {
  overflow-x: auto;
}

.coach-learning-table-scroll table {
  width: 100%;
  border-collapse: collapse;
  font-family: var(--font-mono);
  font-size: var(--text-sm);
}

.coach-learning-table-scroll th,
.coach-learning-table-scroll td {
  padding: var(--space-2);
  text-align: left;
  border: 1px solid var(--border);
}

.coach-learning-table-scroll th small {
  display: block;
  margin-top: var(--space-1);
  color: var(--text-muted);
  font-weight: var(--weight-regular);
}

.coach-learning-answer {
  display: grid;
  gap: var(--space-3);
  margin-top: var(--space-4);
}

.coach-learning-answer textarea {
  min-height: 180px;
  resize: vertical;
  font-family: var(--font-mono);
  line-height: 1.6;
  white-space: pre;
  tab-size: 2;
}

.coach-learning-answer button {
  justify-self: start;
}

.coach-learning-feedback {
  padding: var(--space-4);
  background: var(--surface-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
}

.coach-learning-preview {
  margin-top: var(--space-3);
}

.coach-learning-actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  margin-top: var(--space-5);
}

.coach-learning-secondary {
  color: var(--text-secondary);
  background: transparent;
  border-color: var(--border-strong);
}

@media (max-width: 640px) {
  .coach-learning-backdrop {
    align-items: end;
    padding: 0;
  }

  .coach-learning-overlay {
    width: 100%;
    max-height: 96vh;
    border-radius: var(--radius-lg) var(--radius-lg) 0 0;
  }

  .coach-learning-header,
  .coach-learning-step-heading,
  .coach-learning-feedback-heading {
    gap: var(--space-2);
  }
}
</style>

<template>
  <div v-if="open" class="coach-assessment-backdrop" data-coach-assessment-action="backdrop" @click.self="emit('close')">
    <section class="coach-assessment-overlay" role="dialog" aria-modal="true" aria-labelledby="coach-assessment-title">
      <header class="coach-assessment-header">
        <div>
          <p class="section-kicker">定向评估</p>
          <h2 id="coach-assessment-title">当前项目知识评估</h2>
          <p>{{ sessionData.scope_notice || "这是当前项目中的评估结果，不代表整体职业能力。" }}</p>
        </div>
        <button type="button" data-coach-assessment-action="close" @click="emit('close')">关闭</button>
      </header>

      <p v-if="error" class="status-line error">{{ error }}</p>
      <p v-if="sessionData.read_only" class="coach-assessment-warning">
        当前来源版本已变化，本次评估只能查看。请返回学习地图重新分析。
      </p>

      <form v-if="!hasSession" class="coach-assessment-target" @submit.prevent="start(false)">
        <label>
          评估目标类型
          <select v-model="targetType" data-coach-assessment-field="target-type">
            <option value="knowledge_point">项目知识点</option>
            <option value="skill">技能节点（当前项目）</option>
          </select>
        </label>
        <label>
          评估目标
          <select v-model="targetId" data-coach-assessment-field="target-id">
            <option value="">请选择</option>
            <option v-for="target in availableTargets" :key="target.id" :value="target.id">
              {{ target.title || target.name || target.stable_key }}
            </option>
          </select>
        </label>
        <button type="submit" :disabled="loading || !targetId" data-coach-assessment-action="start">
          {{ loading ? "正在生成..." : "开始评估" }}
        </button>
      </form>

      <template v-else>
        <div class="coach-assessment-session-bar">
          <div>
            <span class="learning-map-category">{{ targetTypeLabel(sessionData.target_type) }}</span>
            <strong>{{ sessionData.target?.label || selectedTargetLabel }}</strong>
          </div>
          <button
            type="button"
            :disabled="loading"
            data-coach-assessment-action="restart"
            @click="start(true)"
          >
            重新开始
          </button>
        </div>

        <section
          v-if="visibleResult && (!currentQuestion?.result || visibleResult.id !== currentQuestion.result.id)"
          class="coach-assessment-result coach-assessment-latest-result"
        >
          <p class="section-kicker">刚刚提交的当前项目评估</p>
          <ResultDetails :result="visibleResult" @open-sources="openResultSources" />
        </section>

        <section v-if="currentQuestion" class="coach-assessment-question">
          <p class="section-kicker">第 {{ currentQuestionNumber }} / {{ sessionData.question_count || questions.length }} 题</p>
          <h3>{{ questionTypeLabel(currentQuestion.question_type) }}</h3>
          <p class="coach-assessment-prompt">{{ currentQuestion.prompt }}</p>

          <div v-if="currentQuestion.answered && currentQuestion.result" class="coach-assessment-result">
            <ResultDetails :result="currentQuestion.result" @open-sources="openResultSources" />
          </div>

          <form v-else class="coach-assessment-answer" @submit.prevent="submitAnswer">
            <label>
              你的回答
              <textarea
                v-model.trim="answer"
                data-coach-assessment-field="answer"
                :disabled="submitting || sessionData.read_only"
                placeholder="结合当前项目和来源说明你的理解"
              ></textarea>
            </label>
            <button
              type="submit"
              :disabled="submitting || sessionData.read_only || !answer"
              data-coach-assessment-action="submit"
            >
              {{ submitting ? "评估中..." : "提交回答" }}
            </button>
          </form>

        </section>

        <section v-else class="coach-assessment-complete">
          <p class="section-kicker">完成</p>
          <h3>本次评估已完成</h3>
          <p>结果已计入当前项目知识覆盖，可返回学习地图查看。</p>
        </section>
      </template>
    </section>
  </div>
</template>

<script setup>
import { computed, defineComponent, h, ref, watch } from "vue";

const props = defineProps({
  open: {
    type: Boolean,
    default: false,
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
  session: {
    type: Object,
    default: null,
  },
  assessmentResult: {
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
});

const emit = defineEmits(["close", "open-sources", "start", "restart", "submit-answer"]);
const targetType = ref(props.initialTarget?.target_type || "knowledge_point");
const targetId = ref(props.initialTarget?.target_id || "");
const answer = ref("");

const ResultDetails = defineComponent({
  name: "CoachAssessmentResultDetails",
  props: {
    result: {
      type: Object,
      required: true,
    },
  },
  emits: ["open-sources"],
  setup(resultProps, { emit: resultEmit }) {
    const statusLabels = {
      unassessed: "未验证",
      needs_work: "需补强",
      developing: "发展中",
      mastered: "已掌握",
    };
    const percentage = (value) => {
      const numeric = Number(value);
      return Number.isFinite(numeric) ? `${Math.round(numeric * 100)}%` : "未提供";
    };
    return () => h("div", { class: "coach-result-details" }, [
      h("h3", statusLabels[resultProps.result.status] || "当前项目评估结果"),
      h("p", `置信度：${percentage(resultProps.result.confidence)}${resultProps.result.low_confidence ? "（低置信度）" : ""}`),
      h("p", `评估方式：${resultProps.result.evaluator || "未提供"}`),
      h("div", [
        h("p", { class: "section-kicker" }, "命中证据"),
        h("ul", (resultProps.result.matched_evidence || []).length
          ? resultProps.result.matched_evidence.map((item) => h("li", { key: `${item.point}:${item.evidence}` }, `${item.point}：${item.evidence}`))
          : [h("li", "暂无命中证据")]),
      ]),
      h("div", [
        h("p", { class: "section-kicker" }, "缺失点"),
        h("ul", (resultProps.result.missing_points || []).length
          ? resultProps.result.missing_points.map((item) => h("li", { key: item }, item))
          : [h("li", "暂无缺失点")]),
      ]),
      h("div", [
        h("p", { class: "section-kicker" }, "来源 ID"),
        h("ul", (resultProps.result.source_ids || []).length
          ? resultProps.result.source_ids.map((item) => h("li", { key: item }, item))
          : [h("li", "暂无来源 ID")]),
        (resultProps.result.source_ids || []).length
          ? h("button", {
            type: "button",
            "data-coach-assessment-action": "open-result-sources",
            onClick: () => resultEmit("open-sources", resultProps.result),
          }, "查看来源")
          : null,
      ]),
    ]);
  },
});

const sessionData = computed(() => props.session?.session || props.session || {});
const hasSession = computed(() => Boolean(sessionData.value.id));
const questions = computed(() => Array.isArray(sessionData.value.questions) ? sessionData.value.questions : []);
const currentQuestion = computed(() => {
  const currentId = sessionData.value.current_question_id;
  if (currentId) {
    return questions.value.find((question) => question.id === currentId) || null;
  }
  return questions.value.find((question) => !question.answered) || null;
});
const currentQuestionNumber = computed(() => {
  const index = questions.value.findIndex((question) => question.id === currentQuestion.value?.id);
  return index >= 0 ? index + 1 : 0;
});
const visibleResult = computed(() => props.assessmentResult?.result || props.assessmentResult || null);
const knowledgePointItems = computed(() => normalizeItems(props.knowledgePoints, "knowledge_points"));
const skillItems = computed(() => normalizeItems(props.skills, "skills"));
const availableTargets = computed(() => targetType.value === "skill"
  ? skillItems.value.filter((skill) => skill.project_evidence !== "no_project_evidence" && skill.assessment_state !== "no_project_evidence")
  : knowledgePointItems.value);
const selectedTargetLabel = computed(() => {
  const selected = availableTargets.value.find((target) => target.id === targetId.value);
  return selected?.title || selected?.name || selected?.stable_key || "未命名目标";
});

watch(
  () => props.initialTarget,
  (target) => {
    if (!target) return;
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

watch(
  () => currentQuestion.value?.id,
  () => {
    answer.value = "";
  },
);

function normalizeItems(value, responseKey) {
  if (Array.isArray(value)) return value;
  const unwrapped = value?.[responseKey] || value || {};
  return Array.isArray(unwrapped.items) ? unwrapped.items : [];
}

function start(restart) {
  const payload = {
    target_type: sessionData.value.target_type || targetType.value,
    target_id: sessionData.value.target_id || targetId.value,
    restart,
  };
  emit(restart ? "restart" : "start", payload);
}

function submitAnswer() {
  if (!currentQuestion.value || !answer.value) return;
  emit("submit-answer", {
    session_id: sessionData.value.id,
    question_id: currentQuestion.value.id,
    answer: answer.value,
  });
}

function openResultSources(result) {
  emit("open-sources", {
    title: "评估结果来源",
    source_ids: result?.source_ids || [],
    sources: sessionData.value.sources || {},
  });
}

function targetTypeLabel(value) {
  return value === "skill" ? "当前项目技能节点" : "项目知识点";
}

function questionTypeLabel(value) {
  const labels = {
    concept: "概念理解",
    flow: "流程说明",
    code_location: "代码定位",
  };
  return labels[value] || "项目理解";
}
</script>

<style scoped>
.coach-assessment-backdrop {
  position: fixed;
  inset: 0;
  z-index: 45;
  display: grid;
  place-items: center;
  padding: var(--space-4);
  background: rgb(17 17 17 / 32%);
}

.coach-assessment-overlay {
  width: min(760px, 96vw);
  max-height: 92vh;
  overflow-y: auto;
  padding: var(--space-5);
  color: var(--text-primary);
  background: var(--surface-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
}

.coach-assessment-header,
.coach-assessment-session-bar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-4);
}

.coach-assessment-header h2 {
  margin: var(--space-1) 0;
}

.coach-assessment-target,
.coach-assessment-answer {
  display: grid;
  gap: var(--space-4);
  margin-top: var(--space-5);
}

.coach-assessment-target label,
.coach-assessment-answer label {
  display: grid;
  gap: var(--space-2);
}

.coach-assessment-target select,
.coach-assessment-answer textarea {
  width: 100%;
}

.coach-assessment-answer textarea {
  min-height: 160px;
  resize: vertical;
}

.coach-assessment-warning {
  padding: var(--space-3);
  color: var(--warning);
  background: var(--warning-soft);
  border-radius: var(--radius);
}

.coach-assessment-session-bar,
.coach-assessment-question,
.coach-assessment-complete {
  margin-top: var(--space-5);
  padding: var(--space-4);
  background: var(--surface-sunken);
  border-radius: var(--radius-lg);
}

.coach-assessment-session-bar div {
  display: grid;
  gap: var(--space-1);
}

.coach-assessment-prompt {
  font-size: var(--text-md);
  line-height: 1.7;
}

.coach-assessment-result {
  margin-top: var(--space-4);
  padding-top: var(--space-4);
  border-top: 1px solid var(--border);
}

.coach-assessment-latest-result {
  padding: var(--space-4);
  background: var(--surface-sunken);
  border: 0;
  border-radius: var(--radius-lg);
}
</style>

<template>
  <div class="page full">
    <div class="eval-frame">
      <div class="eval-head">
        <h2>项目掌握评估 · {{ selectedProjectId || "未选择项目" }}</h2>
        <span class="progress">— 第 {{ currentQuestionNumber }} 题 / 共 {{ totalQuestions || 0 }} 题 —</span>
      </div>

      <div class="eval-summary">
        <span>从已导入资料生成题目</span>
        <span class="pill m">已掌握 {{ masteredCount }}</span>
        <span class="pill b">基本理解 {{ partialCount }}</span>
        <span class="pill g">需补充 {{ gapCount }}</span>
        <button type="button" class="btn-ghost" :disabled="assessmentLoading || !selectedProjectId" @click="$emit('start-assessment')">
          {{ assessmentSession ? "重新开始" : "开始评估" }}
        </button>
      </div>

      <p v-if="assessmentError" class="status-line error">{{ assessmentError }}</p>
      <p class="status-line">{{ assessmentStatus || emptyStateText }}</p>

      <div v-if="assessmentQuestion" class="question">
        <span class="q-num">{{ romanNumerals[assessmentQuestionIndex] || currentQuestionNumber }}.</span>
        {{ assessmentQuestion.prompt }}
      </div>
      <div v-if="assessmentQuestion" class="eval-meta">
        <span>题型：{{ formatQuestionType(assessmentQuestion.question_type) }}</span>
        <span>知识点：{{ assessmentQuestion.knowledge_point || "未命名知识点" }}</span>
        <span>来源：{{ assessmentQuestion.source_path || "未知来源" }}</span>
      </div>
      <p v-else class="muted-line">请先选择项目空间并点击“开始评估”。</p>

      <form @submit.prevent="submitAnswer">
        <textarea
          v-model.trim="assessmentAnswer"
          class="answer-box"
          name="assessment_answer"
          placeholder="输入你对当前题目的回答"
          :disabled="!assessmentQuestion || assessmentSubmitting || assessmentAnsweredCurrent"
        ></textarea>
        <div class="eval-actions">
          <button type="button" class="btn-ghost" :disabled="!assessmentSession" @click="$emit('reset-assessment')">重置评估</button>
          <div>
            <button type="submit" class="btn-ink" :disabled="!assessmentQuestion || assessmentSubmitting || assessmentAnsweredCurrent">
              {{ assessmentSubmitting ? "评估中..." : "提交回答 ▶" }}
            </button>
            <button type="button" class="btn-ghost" :disabled="!assessmentAnsweredCurrent" @click="goNext">
              {{ hasNextQuestion ? "下一题" : "完成评估" }}
            </button>
          </div>
        </div>
      </form>

      <div v-if="latestResult" :class="['verdict', verdictClass]">
        <div class="level">{{ statusLabel(latestResult.status) }}</div>
        <h3>结果概览 · {{ scorePercent }}</h3>
        <div v-if="latestResult.source_path" class="ref">参考：{{ latestResult.source_path }}</div>
        <p>匹配要点：{{ (latestResult.matched_points || []).join("；") || "暂无匹配要点" }}</p>
        <p>缺失要点：{{ (latestResult.missing_points || []).join("；") || "暂无缺失要点" }}</p>
      </div>

      <div class="assessment-ledger">
        <div>
          <div class="col-head"><span>答题记录</span><span class="num">{{ assessmentResults.length }}</span></div>
          <ol class="assessment-history">
            <li v-for="entry in assessmentResults" :key="entry.result?.result_id || entry.question?.id">
              <strong>{{ entry.result?.status || "未评估" }}｜{{ formatScore(entry.result?.score) }}</strong>
              <p>{{ entry.question?.prompt || "未知题目" }}</p>
            </li>
            <li v-if="assessmentResults.length === 0">暂无答题记录</li>
          </ol>
        </div>
        <div>
          <div class="col-head"><span>待复测列表</span><span class="num">{{ assessmentMissedQuestions.length }}</span></div>
          <ol class="assessment-history">
            <li v-for="entry in assessmentMissedQuestions" :key="entry.result?.result_id || entry.question?.id">
              <strong>{{ entry.result?.status || "需要复测" }}</strong>
              <p>{{ entry.question?.knowledge_point || entry.question?.source_path || "未命名题目" }}</p>
            </li>
            <li v-if="assessmentMissedQuestions.length === 0">暂无待复测题目</li>
          </ol>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from "vue";

const props = defineProps({
  selectedProjectId: {
    type: String,
    default: "",
  },
  assessmentSession: {
    type: Object,
    default: null,
  },
  assessmentQuestion: {
    type: Object,
    default: null,
  },
  assessmentQuestionIndex: {
    type: Number,
    default: 0,
  },
  assessmentResults: {
    type: Array,
    default: () => [],
  },
  assessmentMissedQuestions: {
    type: Array,
    default: () => [],
  },
  assessmentAnsweredCurrent: {
    type: Boolean,
    default: false,
  },
  assessmentLoading: {
    type: Boolean,
    default: false,
  },
  assessmentSubmitting: {
    type: Boolean,
    default: false,
  },
  assessmentError: {
    type: String,
    default: "",
  },
  assessmentStatus: {
    type: String,
    default: "",
  },
});

const emit = defineEmits(["start-assessment", "submit-assessment-answer", "next-assessment-question", "reset-assessment"]);

const assessmentAnswer = ref("");

watch(
  () => props.assessmentQuestion?.id,
  () => {
    assessmentAnswer.value = "";
  },
);

const totalQuestions = computed(() => {
  return Array.isArray(props.assessmentSession?.questions) ? props.assessmentSession.questions.length : 0;
});

const currentQuestionNumber = computed(() => {
  if (!props.assessmentQuestion) {
    return 0;
  }
  return props.assessmentQuestionIndex + 1;
});

const hasNextQuestion = computed(() => {
  return props.assessmentQuestionIndex + 1 < totalQuestions.value;
});

const latestResult = computed(() => {
  return props.assessmentResults.at(-1)?.result || null;
});

const scorePercent = computed(() => {
  return formatScore(latestResult.value?.score);
});

const statusClass = computed(() => {
  const status = latestResult.value?.status || "";
  return {
    "status-line": true,
    "assessment-status-good": status === "已掌握" || status === "基本理解",
    "assessment-status-warning": status === "需要补充" || status === "暂未掌握",
  };
});

const masteredCount = computed(() => props.assessmentResults.filter((entry) => entry.result?.status === "已掌握").length);
const partialCount = computed(() => props.assessmentResults.filter((entry) => entry.result?.status === "基本理解").length);
const gapCount = computed(() => props.assessmentResults.filter((entry) => ["需要补充", "暂未掌握"].includes(entry.result?.status)).length);
const verdictClass = computed(() => {
  const status = latestResult.value?.status || "";
  if (status === "已掌握") {
    return "mastered";
  }
  if (status === "需要补充" || status === "暂未掌握") {
    return "gap";
  }
  return "partial";
});
const romanNumerals = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII"];

const emptyStateText = computed(() => {
  if (!props.selectedProjectId) {
    return "未选择项目空间";
  }
  if (!props.assessmentSession) {
    return "点击“开始评估”生成题目。";
  }
  return "等待提交当前题回答。";
});

function submitAnswer() {
  emit("submit-assessment-answer", assessmentAnswer.value);
}

function goNext() {
  emit("next-assessment-question");
}

function formatQuestionType(questionType) {
  const labels = {
    concept: "概念理解",
    flow: "流程说明",
    code_location: "代码定位",
  };
  return labels[questionType] || questionType || "未知题型";
}

function formatScore(score) {
  const value = Number(score ?? 0);
  return `${Math.round(value * 100)}%`;
}

function statusLabel(status) {
  return {
    已掌握: "○ 已掌握",
    基本理解: "○ 基本理解",
    需要补充: "○ 需要补充",
    暂未掌握: "○ 暂未掌握",
  }[status] || "○ 等待评估";
}
</script>

<template>
  <section class="view-panel assessment-view">
    <header class="topbar">
      <div>
        <p class="section-kicker">评估</p>
        <h2>掌握评估</h2>
        <p>B-141T 已迁移评估最小闭环；回答反馈和题库管理后续迁移。</p>
      </div>
      <button type="button" :disabled="assessmentLoading || !selectedProjectId" @click="$emit('start-assessment')">
        {{ assessmentSession ? "重新开始" : "开始评估" }}
      </button>
    </header>

    <p v-if="assessmentError" class="status-line error">{{ assessmentError }}</p>
    <p class="status-line">{{ assessmentStatus || emptyStateText }}</p>

    <div class="assessment-grid">
      <section class="assessment-panel">
        <div class="section-title-row">
          <div>
            <p class="section-kicker">当前题目</p>
            <h3>第 {{ currentQuestionNumber }} / {{ totalQuestions || 0 }} 题</h3>
          </div>
          <button type="button" :disabled="!assessmentSession" @click="$emit('reset-assessment')">重置评估</button>
        </div>

        <div v-if="assessmentQuestion" class="assessment-question">
          <p><strong>题型：</strong>{{ formatQuestionType(assessmentQuestion.question_type) }}</p>
          <p><strong>知识点：</strong>{{ assessmentQuestion.knowledge_point || "未命名知识点" }}</p>
          <p><strong>来源：</strong>{{ assessmentQuestion.source_path || "未知来源" }}</p>
          <p class="question-prompt">{{ assessmentQuestion.prompt }}</p>
        </div>
        <p v-else class="muted-line">请先选择项目空间并点击“开始评估”。</p>

        <form class="question-form" @submit.prevent="submitAnswer">
          <label>
            评估回答
            <textarea
              v-model.trim="assessmentAnswer"
              name="assessment_answer"
              placeholder="输入你对当前题目的回答"
              :disabled="!assessmentQuestion || assessmentSubmitting || assessmentAnsweredCurrent"
            ></textarea>
          </label>
          <div class="actions">
            <button type="submit" :disabled="!assessmentQuestion || assessmentSubmitting || assessmentAnsweredCurrent">
              {{ assessmentSubmitting ? "评估中..." : "提交回答" }}
            </button>
            <button type="button" :disabled="!assessmentAnsweredCurrent" @click="goNext">
              {{ hasNextQuestion ? "下一题" : "完成评估" }}
            </button>
          </div>
        </form>
      </section>

      <section class="assessment-panel">
        <p class="section-kicker">结果概览</p>
        <h3 :class="statusClass">{{ latestResult?.status || "等待评估" }}</h3>
        <p>得分：{{ scorePercent }}</p>
        <p v-if="latestResult?.source_path">来源：{{ latestResult.source_path }}</p>

        <div class="assessment-result-list">
          <p class="section-kicker">匹配要点</p>
          <ul>
            <li v-for="point in latestResult?.matched_points || []" :key="point">{{ point }}</li>
            <li v-if="(latestResult?.matched_points || []).length === 0">暂无匹配要点</li>
          </ul>
        </div>

        <div class="assessment-result-list">
          <p class="section-kicker">缺失要点</p>
          <ul>
            <li v-for="point in latestResult?.missing_points || []" :key="point">{{ point }}</li>
            <li v-if="(latestResult?.missing_points || []).length === 0">暂无缺失要点</li>
          </ul>
        </div>
      </section>

      <section class="assessment-panel">
        <p class="section-kicker">答题记录</p>
        <ol class="assessment-history">
          <li v-for="entry in assessmentResults" :key="entry.result?.result_id || entry.question?.id">
            <strong>{{ entry.result?.status || "未评估" }}｜{{ formatScore(entry.result?.score) }}</strong>
            <p>{{ entry.question?.prompt || "未知题目" }}</p>
          </li>
          <li v-if="assessmentResults.length === 0">暂无答题记录</li>
        </ol>
      </section>

      <section class="assessment-panel">
        <p class="section-kicker">待复测列表</p>
        <ol class="assessment-history">
          <li v-for="entry in assessmentMissedQuestions" :key="entry.result?.result_id || entry.question?.id">
            <strong>{{ entry.result?.status || "需要复测" }}</strong>
            <p>{{ entry.question?.knowledge_point || entry.question?.source_path || "未命名题目" }}</p>
          </li>
          <li v-if="assessmentMissedQuestions.length === 0">暂无待复测题目</li>
        </ol>
      </section>
    </div>
  </section>
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
</script>

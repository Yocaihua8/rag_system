<template>
  <section class="view-panel">
    <header class="topbar">
      <div>
        <p class="section-kicker">工作台</p>
        <h2>项目问答</h2>
        <p>B-141D 已迁移非流式问答入口；SSE、Agent 工具和检索调试后续迁移。</p>
      </div>
    </header>

    <div class="workbench-grid">
      <QuestionPanel
        :selected-project-id="selectedProjectId"
        :loading="answerLoading"
        :error="answerError"
        :status-message="answerStatus || statusMessage"
        @submit-question="(question) => $emit('submit-question', question)"
        @check-health="$emit('check-health')"
      />
      <AnswerPanel
        :answer-result="answerResult"
        :loading="answerLoading"
        :error="answerError"
      />
    </div>
  </section>
</template>

<script setup>
import AnswerPanel from "../components/AnswerPanel.vue";
import QuestionPanel from "../components/QuestionPanel.vue";

defineProps({
  statusMessage: {
    type: String,
    required: true,
  },
  selectedProjectId: {
    type: String,
    required: true,
  },
  answerResult: {
    type: Object,
    default: null,
  },
  answerLoading: {
    type: Boolean,
    default: false,
  },
  answerError: {
    type: String,
    default: "",
  },
  answerStatus: {
    type: String,
    default: "",
  },
});

defineEmits(["check-health", "submit-question"]);
</script>

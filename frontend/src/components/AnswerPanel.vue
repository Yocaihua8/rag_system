<template>
  <section class="answer-panel" aria-labelledby="answer-panel-title">
    <div class="section-title-row">
      <div>
        <p class="section-kicker">回答</p>
        <h2 id="answer-panel-title">回答</h2>
      </div>
      <div v-if="answerResult" class="answer-meta">
        <span>mode: {{ answerResult.mode || "local" }}</span>
        <span>provider: {{ answerResult.provider || "local" }}</span>
      </div>
    </div>

    <p v-if="loading" class="status-line">正在生成回答...</p>
    <p v-else-if="error" class="status-line error">{{ error }}</p>
    <p v-else-if="!answerResult" class="muted-line">提交问题后会在这里显示回答。</p>

    <div v-if="answerResult" class="answer-body">
      <p>{{ answerResult.answer || answerResult.message || "暂无回答" }}</p>
    </div>

    <div v-if="answerResult" class="source-quality">
      <p class="section-kicker">来源质量</p>
      <p>{{ sourceQualityText }}</p>
    </div>

    <div v-if="answerResult" class="source-list">
      <p class="section-kicker">来源</p>
      <p v-if="sources.length === 0" class="muted-line">暂无来源</p>
      <ol v-else>
        <li v-for="source in sources" :key="source.chunk_id || source.document_id || source.path">
          <strong>{{ source.path || "未知来源" }}</strong>
          <p>{{ source.snippet || source.preview || "无片段预览" }}</p>
        </li>
      </ol>
    </div>

    <div v-if="answerResult" class="answer-feedback">
      <p class="section-kicker">回答反馈</p>
      <p v-if="!lastAnswerMessageId" class="muted-line">当前回答暂不可反馈。</p>
      <div v-else class="feedback-actions">
        <button
          type="button"
          data-feedback-rating="useful"
          :disabled="answerFeedbackSubmitting"
          @click="submitAnswerFeedback('useful')"
        >
          有用
        </button>
        <button
          type="button"
          data-feedback-rating="not_useful"
          :disabled="answerFeedbackSubmitting"
          @click="submitAnswerFeedback('not_useful')"
        >
          无用
        </button>
        <button
          type="button"
          data-feedback-rating="source_wrong"
          :disabled="answerFeedbackSubmitting"
          @click="submitAnswerFeedback('source_wrong')"
        >
          来源不准
        </button>
        <button
          type="button"
          data-feedback-rating="need_more_context"
          :disabled="answerFeedbackSubmitting"
          @click="submitAnswerFeedback('need_more_context')"
        >
          需要更多上下文
        </button>
      </div>
      <p v-if="answerFeedbackStatus" class="status-line">{{ answerFeedbackStatus }}</p>
      <p v-if="answerFeedbackError" class="status-line error">{{ answerFeedbackError }}</p>
    </div>
  </section>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  answerResult: {
    type: Object,
    default: null,
  },
  lastAnswerMessageId: {
    type: String,
    default: "",
  },
  answerFeedbackSubmitting: {
    type: Boolean,
    default: false,
  },
  answerFeedbackStatus: {
    type: String,
    default: "",
  },
  answerFeedbackError: {
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

const emit = defineEmits(["submit-answer-feedback"]);

const sources = computed(() => {
  return props.answerResult?.sources || [];
});

const sourceQualityText = computed(() => {
  const sourceQuality = props.answerResult?.source_quality;
  if (!sourceQuality) {
    return "来源质量：暂无来源质量摘要";
  }
  return sourceQuality.label || sourceQuality.reason || `来源质量：${sourceQuality.level || "unknown"}`;
});

function submitAnswerFeedback(rating) {
  emit("submit-answer-feedback", rating);
}
</script>

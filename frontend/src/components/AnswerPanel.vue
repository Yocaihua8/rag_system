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

    <div v-if="toolSuggestion" class="tool-suggestion">
      <p class="section-kicker">建议工具</p>
      <p>{{ formatToolSuggestion(toolSuggestion) }}</p>
      <button
        type="button"
        :disabled="agentToolSubmittingName === suggestionToolName"
        @click="runToolSuggestion"
      >
        {{ agentToolSubmittingName === suggestionToolName ? "运行中..." : "运行建议工具" }}
      </button>
    </div>

    <div v-if="lastUsableToolRun" class="tool-context-card">
      <p class="section-kicker">可用工具结果</p>
      <p>{{ formatUsableToolRun(lastUsableToolRun) }}</p>
      <button type="button" @click="useToolResultContext">使用工具结果作为下一问上下文</button>
    </div>

    <div v-if="currentToolContextRunId" class="tool-context-notice">
      <p class="section-kicker">下一问上下文</p>
      <p>下一问将带入工具运行：{{ currentToolContextRunId }}</p>
      <button type="button" @click="clearToolContext">清除工具上下文</button>
    </div>

    <div v-if="usedToolContext" class="tool-context-notice">
      <p class="section-kicker">本轮已使用工具来源</p>
      <p>{{ formatUsedToolContext(usedToolContext) }}</p>
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
  toolSuggestion: {
    type: Object,
    default: null,
  },
  lastUsableToolRun: {
    type: Object,
    default: null,
  },
  currentToolContextRunId: {
    type: String,
    default: "",
  },
  agentToolSubmittingName: {
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

const emit = defineEmits(["submit-answer-feedback", "run-tool-suggestion", "use-tool-result-context", "clear-tool-context"]);

const sources = computed(() => {
  return props.answerResult?.sources || [];
});

const toolSuggestion = computed(() => {
  return props.toolSuggestion || props.answerResult?.tool_suggestion || null;
});

const usedToolContext = computed(() => {
  return props.answerResult?.tool_context || null;
});

const suggestionToolName = computed(() => {
  return toolSuggestion.value?.tool || "search_sources";
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

function runToolSuggestion() {
  emit("run-tool-suggestion", toolSuggestion.value);
}

function useToolResultContext() {
  emit("use-tool-result-context", props.lastUsableToolRun?.id || "");
}

function clearToolContext() {
  emit("clear-tool-context");
}

function formatToolSuggestion(suggestion) {
  const toolName = suggestion.tool || "search_sources";
  const query = suggestion.arguments?.query || "";
  const reason = suggestion.reason || "当前来源不足，可先扩大来源检索。";
  return `${reason} 工具：${toolName}${query ? `；查询：${query}` : ""}`;
}

function formatUsableToolRun(run) {
  const query = run.result?.query || run.arguments?.query || "";
  return `${run.tool_name || "search_sources"} / ${run.status || "success"}${query ? ` / ${query}` : ""}`;
}

function formatUsedToolContext(context) {
  const query = context.query || context.arguments?.query || "";
  const runId = context.tool_run_id || context.run_id || "";
  return `${query ? `查询：${query}` : "已带入工具来源"}${runId ? `；运行 ID：${runId}` : ""}`;
}
</script>

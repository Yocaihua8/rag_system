<template>
  <section class="answer-panel conv" aria-labelledby="answer-panel-title">
    <div class="col-head">
      <span id="answer-panel-title">对话</span>
      <span class="num">Respondeo</span>
    </div>

    <p v-if="loading" class="status-line">正在生成回答...</p>
    <p v-else-if="error" class="status-line error">{{ error }}</p>
    <p v-else-if="!answerResult" class="muted-line">提交问题后会在这里显示回答。</p>

    <article v-if="answerResult" class="turn assistant">
      <div class="speaker">答 · Respondeo</div>
      <div class="body">
        <MarkdownBody :content="answerResult.answer || answerResult.message || '暂无回答'" />
      </div>

      <div class="obs">
        <span>命中 <strong>{{ sources.length }}</strong></span>
        <span>top_k <strong>{{ observability.top_k }}</strong></span>
        <span>模式 <strong>{{ answerResult.mode || "local" }}</strong></span>
        <span>模型 <strong>{{ answerResult.provider || observability.model }}</strong></span>
        <span>耗时 <strong>{{ observability.latency }}</strong></span>
      </div>

      <div class="sources">
        <span class="label">来源</span>
        <span v-if="sources.length === 0" class="src">暂无来源 · {{ sourceQualityText }}</span>
        <template v-else>
          <span v-for="(source, index) in sources" :key="source.chunk_id || source.document_id || source.path" class="src">
            <span class="roman">{{ romanNumerals[index] || index + 1 }}</span>
            <em>{{ source.path || "未知来源" }}</em>
            <span style="color:var(--ink-3)"> · {{ source.snippet || source.preview || "无片段预览" }}</span>
          </span>
        </template>
      </div>

      <div class="feedback" aria-label="回答反馈">
        <button
          type="button"
          data-feedback-rating="useful"
          :disabled="answerFeedbackSubmitting || !lastAnswerMessageId"
          @click="submitAnswerFeedback('useful')"
        >
          有用
        </button>
        <button
          type="button"
          data-feedback-rating="not_useful"
          :disabled="answerFeedbackSubmitting || !lastAnswerMessageId"
          @click="submitAnswerFeedback('not_useful')"
        >
          无用
        </button>
        <button
          type="button"
          data-feedback-rating="source_wrong"
          :disabled="answerFeedbackSubmitting || !lastAnswerMessageId"
          @click="submitAnswerFeedback('source_wrong')"
        >
          来源不准
        </button>
        <button
          type="button"
          data-feedback-rating="need_more_context"
          :disabled="answerFeedbackSubmitting || !lastAnswerMessageId"
          @click="submitAnswerFeedback('need_more_context')"
        >
          需要更多上下文
        </button>
      </div>
      <p v-if="!lastAnswerMessageId" class="muted-line">当前回答暂不可反馈。</p>
      <p v-if="answerFeedbackStatus" class="status-line">{{ answerFeedbackStatus }}</p>
      <p v-if="answerFeedbackError" class="status-line error">{{ answerFeedbackError }}</p>
    </article>

    <div v-if="toolSuggestion" class="tool-suggest">
      <span>建议工具</span>
      <span>来源不足时建议运行</span>
      <span class="pill">{{ suggestionToolName }}</span>
      <span>{{ formatToolSuggestion(toolSuggestion) }}</span>
      <button type="button" :disabled="agentToolSubmittingName === suggestionToolName" @click="runToolSuggestion">
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

  </section>
</template>

<script setup>
import { computed } from "vue";
import MarkdownBody from "./MarkdownBody.vue";

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

const observability = computed(() => {
  const data = props.answerResult?.observability || props.answerResult?.debug || {};
  return {
    top_k: data.top_k ?? props.answerResult?.retrieval?.top_k ?? "-",
    model: data.model || props.answerResult?.model || "local",
    latency: data.latency || data.latency_ms || "-",
  };
});

const toolSuggestion = computed(() => {
  return props.toolSuggestion || null;
});

const usedToolContext = computed(() => {
  return props.answerResult?.tool_context || null;
});

const suggestionToolName = computed(() => {
  return toolSuggestion.value?.tool || "search_sources";
});

const romanNumerals = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII"];

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

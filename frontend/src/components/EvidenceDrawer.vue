<template>
  <aside class="evidence-drawer" :class="{ open: !collapsed }" aria-label="依据">
    <button
      type="button"
      class="evidence-toggle"
      data-evidence-action="toggle"
      :aria-expanded="String(!collapsed)"
      @click="emit('toggle')"
    >
      依据
    </button>

    <div v-if="!collapsed" class="evidence-drawer-body">
      <section class="evidence-section">
        <div class="section-title-row">
          <div>
            <p class="section-kicker">来源</p>
            <h2>回答依据</h2>
          </div>
        </div>
        <p class="status-line">{{ sourceQualityText }}</p>
        <p v-if="sources.length === 0" class="muted-line">暂无来源</p>
        <ol v-else class="evidence-source-list">
          <li v-for="source in sources" :key="source.chunk_id || source.document_id || source.path">
            <strong>{{ source.path || "未知来源" }}</strong>
            <p>{{ source.snippet || source.preview || "无片段预览" }}</p>
          </li>
        </ol>
      </section>

      <section v-if="toolSuggestion" class="evidence-section">
        <p class="section-kicker">建议</p>
        <p>{{ formatToolSuggestion(toolSuggestion) }}</p>
        <button
          type="button"
          data-evidence-action="run-tool"
          :disabled="agentToolSubmittingName === suggestionToolName"
          @click="emit('run-tool-suggestion', toolSuggestion)"
        >
          {{ agentToolSubmittingName === suggestionToolName ? "运行中..." : "查更多来源" }}
        </button>
      </section>

      <section v-if="lastUsableToolRun || currentToolContextRunId || usedToolContext" class="evidence-section">
        <p class="section-kicker">上下文</p>
        <div v-if="lastUsableToolRun" class="tool-context-card">
          <p>{{ formatUsableToolRun(lastUsableToolRun) }}</p>
          <button type="button" data-evidence-action="use-tool-run" @click="useToolResultContext">
            用到下一问
          </button>
        </div>
        <div v-if="currentToolContextRunId" class="tool-context-notice">
          <p>下一问将带入：{{ currentToolContextRunId }}</p>
          <button type="button" data-evidence-action="clear-tool-context" @click="emit('clear-tool-context')">
            清除
          </button>
        </div>
        <p v-if="usedToolContext" class="muted-line">{{ formatUsedToolContext(usedToolContext) }}</p>
      </section>

      <slot name="advanced" />
    </div>
  </aside>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  collapsed: {
    type: Boolean,
    default: true,
  },
  answerResult: {
    type: Object,
    default: null,
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
});

const emit = defineEmits(["toggle", "run-tool-suggestion", "use-tool-result-context", "clear-tool-context"]);

const sources = computed(() => {
  return props.answerResult?.sources || [];
});

const usedToolContext = computed(() => {
  return props.answerResult?.tool_context || null;
});

const suggestionToolName = computed(() => {
  return props.toolSuggestion?.tool || "search_sources";
});

const sourceQualityText = computed(() => {
  const sourceQuality = props.answerResult?.source_quality;
  if (!sourceQuality) {
    return "暂无来源质量摘要";
  }
  return sourceQuality.label || sourceQuality.reason || `来源质量：${sourceQuality.level || "unknown"}`;
});

function useToolResultContext() {
  emit("use-tool-result-context", props.lastUsableToolRun?.id || "");
}

function formatToolSuggestion(suggestion) {
  const query = suggestion.arguments?.query || "";
  const reason = suggestion.reason || "当前来源不足，可先查更多来源。";
  return `${reason}${query ? ` 查询：${query}` : ""}`;
}

function formatUsableToolRun(run) {
  const query = run.result?.query || run.arguments?.query || "";
  return `${run.status || "success"}${query ? ` / ${query}` : ""}`;
}

function formatUsedToolContext(context) {
  const query = context.query || context.arguments?.query || "";
  const runId = context.tool_run_id || context.run_id || "";
  return `${query ? `已使用：${query}` : "已带入工具来源"}${runId ? ` / ${runId}` : ""}`;
}
</script>

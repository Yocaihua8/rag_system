<template>
  <section class="view-panel">
    <header class="topbar">
      <div>
        <p class="section-kicker">工作台</p>
        <h2>项目问答</h2>
        <p>B-141D 已迁移非流式问答入口，B-141U 已迁移回答反馈，B-141V 已迁移检索调试，B-141W 已迁移 Agent 只读工具，B-141X 已迁移工具建议与来源上下文，B-141Y 已迁移项目级检索默认值；SSE 和会话后续迁移。</p>
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
        :last-answer-message-id="lastAnswerMessageId"
        :answer-feedback-submitting="answerFeedbackSubmitting"
        :answer-feedback-status="answerFeedbackStatus"
        :answer-feedback-error="answerFeedbackError"
        :tool-suggestion="currentToolSuggestion"
        :last-usable-tool-run="lastUsableToolRun"
        :current-tool-context-run-id="currentToolContextRunId"
        :agent-tool-submitting-name="agentToolSubmittingName"
        @submit-answer-feedback="(rating) => $emit('submit-answer-feedback', rating)"
        @run-tool-suggestion="(suggestion) => $emit('run-tool-suggestion', suggestion)"
        @use-tool-result-context="(runId) => $emit('use-tool-result-context', runId)"
        @clear-tool-context="$emit('clear-tool-context')"
      />
      <SearchDebugPanel
        :selected-project-id="selectedProjectId"
        :search-debug-result="searchDebugResult"
        :search-debug-loading="searchDebugLoading"
        :search-debug-error="searchDebugError"
        :search-debug-status="searchDebugStatus"
        :retrieval-settings="retrievalSettings"
        :retrieval-settings-loading="retrievalSettingsLoading"
        :retrieval-settings-saving="retrievalSettingsSaving"
        :retrieval-settings-status="retrievalSettingsStatus"
        :retrieval-settings-error="retrievalSettingsError"
        @run-search-debug="(payload) => $emit('run-search-debug', payload)"
        @save-retrieval-settings="(payload) => $emit('save-retrieval-settings', payload)"
      />
      <AgentToolsPanel
        :selected-project-id="selectedProjectId"
        :agent-tools="agentTools"
        :agent-tools-loading="agentToolsLoading"
        :agent-tools-error="agentToolsError"
        :agent-tool-runs="agentToolRuns"
        :agent-tool-runs-loading="agentToolRunsLoading"
        :agent-tool-runs-error="agentToolRunsError"
        :selected-agent-tool-run="selectedAgentToolRun"
        :agent-tool-result="agentToolResult"
        :agent-tool-status="agentToolStatus"
        :agent-tool-error="agentToolError"
        :agent-tool-submitting-name="agentToolSubmittingName"
        :agent-tool-detail-loading="agentToolDetailLoading"
        :agent-tool-detail-error="agentToolDetailError"
        @load-agent-tools="$emit('load-agent-tools')"
        @run-agent-tool="(payload) => $emit('run-agent-tool', payload)"
        @load-agent-tool-runs="$emit('load-agent-tool-runs')"
        @select-agent-tool-run="(runId) => $emit('select-agent-tool-run', runId)"
      />
    </div>
  </section>
</template>

<script setup>
import AnswerPanel from "../components/AnswerPanel.vue";
import AgentToolsPanel from "../components/AgentToolsPanel.vue";
import QuestionPanel from "../components/QuestionPanel.vue";
import SearchDebugPanel from "../components/SearchDebugPanel.vue";

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
  currentToolSuggestion: {
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
  searchDebugResult: {
    type: Object,
    default: null,
  },
  searchDebugLoading: {
    type: Boolean,
    default: false,
  },
  searchDebugError: {
    type: String,
    default: "",
  },
  searchDebugStatus: {
    type: String,
    default: "",
  },
  retrievalSettings: {
    type: Object,
    default: null,
  },
  retrievalSettingsLoading: {
    type: Boolean,
    default: false,
  },
  retrievalSettingsSaving: {
    type: Boolean,
    default: false,
  },
  retrievalSettingsStatus: {
    type: String,
    default: "",
  },
  retrievalSettingsError: {
    type: String,
    default: "",
  },
  agentTools: {
    type: Array,
    default: () => [],
  },
  agentToolsLoading: {
    type: Boolean,
    default: false,
  },
  agentToolsError: {
    type: String,
    default: "",
  },
  agentToolRuns: {
    type: Array,
    default: () => [],
  },
  agentToolRunsLoading: {
    type: Boolean,
    default: false,
  },
  agentToolRunsError: {
    type: String,
    default: "",
  },
  selectedAgentToolRun: {
    type: Object,
    default: null,
  },
  agentToolResult: {
    type: Object,
    default: null,
  },
  agentToolStatus: {
    type: String,
    default: "",
  },
  agentToolError: {
    type: String,
    default: "",
  },
  agentToolSubmittingName: {
    type: String,
    default: "",
  },
  agentToolDetailLoading: {
    type: Boolean,
    default: false,
  },
  agentToolDetailError: {
    type: String,
    default: "",
  },
});

defineEmits(["check-health", "submit-question", "submit-answer-feedback", "run-tool-suggestion", "use-tool-result-context", "clear-tool-context", "run-search-debug", "save-retrieval-settings", "load-agent-tools", "run-agent-tool", "load-agent-tool-runs", "select-agent-tool-run"]);
</script>

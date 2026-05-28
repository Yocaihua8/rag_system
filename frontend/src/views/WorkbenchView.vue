<template>
  <section class="view-panel">
    <header class="topbar">
      <div>
        <p class="section-kicker">工作台</p>
        <h2>项目问答</h2>
        <p>B-142 已迁移 SSE 流式问答、取消当前回答、聊天会话和历史恢复；工作台继续复用既有回答反馈、检索调试、Agent 只读工具、工具来源上下文、项目级检索默认值和检索复盘。</p>
      </div>
    </header>

    <div class="workbench-grid">
      <QuestionPanel
        :selected-project-id="selectedProjectId"
        :loading="answerLoading"
        :error="answerError"
        :status-message="answerStatus || statusMessage"
        @submit-question="(question) => $emit('submit-question', question)"
        @cancel-answer="$emit('cancel-answer')"
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
      <ChatSessionPanel
        :selected-project-id="selectedProjectId"
        :chat-sessions="chatSessions"
        :selected-chat-session-id="selectedChatSessionId"
        :chat-messages="chatMessages"
        :chat-sessions-loading="chatSessionsLoading"
        :chat-sessions-error="chatSessionsError"
        :chat-messages-loading="chatMessagesLoading"
        :chat-messages-error="chatMessagesError"
        :chat-session-mutation-submitting="chatSessionMutationSubmitting"
        :chat-session-mutation-status="chatSessionMutationStatus"
        :chat-session-mutation-error="chatSessionMutationError"
        :deleting-chat-session-id="deletingChatSessionId"
        @refresh-chat-sessions="$emit('refresh-chat-sessions')"
        @select-chat-session="(sessionId) => $emit('select-chat-session', sessionId)"
        @create-chat-session="(title) => $emit('create-chat-session', title)"
        @rename-chat-session="(payload) => $emit('rename-chat-session', payload)"
        @delete-chat-session="(sessionId) => $emit('delete-chat-session', sessionId)"
        @refresh-chat-messages="$emit('refresh-chat-messages')"
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
        :retrieval-reviews="retrievalReviews"
        :retrieval-reviews-loading="retrievalReviewsLoading"
        :retrieval-reviews-error="retrievalReviewsError"
        :retrieval-review-saving="retrievalReviewSaving"
        :retrieval-review-error="retrievalReviewError"
        :retrieval-review-status="retrievalReviewStatus"
        :selected-retrieval-review="selectedRetrievalReview"
        :retrieval-review-detail-loading="retrievalReviewDetailLoading"
        :retrieval-review-detail-error="retrievalReviewDetailError"
        :deleting-retrieval-review-id="deletingRetrievalReviewId"
        @run-search-debug="(payload) => $emit('run-search-debug', payload)"
        @save-retrieval-settings="(payload) => $emit('save-retrieval-settings', payload)"
        @save-retrieval-review="(payload) => $emit('save-retrieval-review', payload)"
        @select-retrieval-review="(reviewId) => $emit('select-retrieval-review', reviewId)"
        @delete-retrieval-review="(reviewId) => $emit('delete-retrieval-review', reviewId)"
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
import ChatSessionPanel from "../components/ChatSessionPanel.vue";
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
  chatSessions: {
    type: Array,
    default: () => [],
  },
  selectedChatSessionId: {
    type: String,
    default: "",
  },
  chatMessages: {
    type: Array,
    default: () => [],
  },
  chatSessionsLoading: {
    type: Boolean,
    default: false,
  },
  chatSessionsError: {
    type: String,
    default: "",
  },
  chatMessagesLoading: {
    type: Boolean,
    default: false,
  },
  chatMessagesError: {
    type: String,
    default: "",
  },
  chatSessionMutationSubmitting: {
    type: Boolean,
    default: false,
  },
  chatSessionMutationStatus: {
    type: String,
    default: "",
  },
  chatSessionMutationError: {
    type: String,
    default: "",
  },
  deletingChatSessionId: {
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
  retrievalReviews: {
    type: Array,
    default: () => [],
  },
  retrievalReviewsLoading: {
    type: Boolean,
    default: false,
  },
  retrievalReviewsError: {
    type: String,
    default: "",
  },
  retrievalReviewSaving: {
    type: Boolean,
    default: false,
  },
  retrievalReviewError: {
    type: String,
    default: "",
  },
  retrievalReviewStatus: {
    type: String,
    default: "",
  },
  selectedRetrievalReview: {
    type: Object,
    default: null,
  },
  retrievalReviewDetailLoading: {
    type: Boolean,
    default: false,
  },
  retrievalReviewDetailError: {
    type: String,
    default: "",
  },
  deletingRetrievalReviewId: {
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

defineEmits(["check-health", "submit-question", "cancel-answer", "submit-answer-feedback", "run-tool-suggestion", "use-tool-result-context", "clear-tool-context", "refresh-chat-sessions", "select-chat-session", "create-chat-session", "rename-chat-session", "delete-chat-session", "refresh-chat-messages", "run-search-debug", "save-retrieval-settings", "save-retrieval-review", "select-retrieval-review", "delete-retrieval-review", "load-agent-tools", "run-agent-tool", "load-agent-tool-runs", "select-agent-tool-run"]);
</script>

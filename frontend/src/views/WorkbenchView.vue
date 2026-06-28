<template>
  <section class="view-panel">
    <header class="topbar">
      <div>
        <p class="section-kicker">工作台</p>
        <h2>项目问答</h2>
        <p>B-142 已接入流式问答、取消、会话历史和消息管理；右侧保留检索调试、检索复盘、Agent 只读工具和工具来源上下文。</p>
      </div>
    </header>

    <FirstRunWizard
      v-if="firstRunVisible"
      :selected-project-id="selectedProjectId"
      :ollama-status="ollamaStatus"
      :ollama-status-loading="ollamaStatusLoading"
      :ollama-status-error="ollamaStatusError"
      :ollama-pulling-model="ollamaPullingModel"
      :ollama-pull-progress="ollamaPullProgress"
      :ollama-pull-status="ollamaPullStatus"
      :ollama-pull-error="ollamaPullError"
      :project-form-submitting="projectFormSubmitting"
      :project-form-error="projectFormError"
      :project-form-status="projectFormStatus"
      @refresh-ollama-status="$emit('refresh-ollama-status')"
      @pull-ollama-model="(model) => $emit('pull-ollama-model', model)"
      @create-project="(payload) => $emit('create-project', payload)"
      @dismiss-first-run="$emit('dismiss-first-run')"
    />

    <div class="workbench-grid">
      <ChatSessionPanel
        :selected-project-id="selectedProjectId"
        :chat-sessions="chatSessions"
        :selected-chat-session-id="selectedChatSessionId"
        :loading="chatSessionsLoading"
        :error="chatSessionsError"
        :mutation-status="chatSessionMutationStatus"
        :mutation-error="chatSessionMutationError"
        @select-chat-session="(sessionId) => $emit('select-chat-session', sessionId)"
        @create-chat-session="(title) => $emit('create-chat-session', title)"
        @rename-chat-session="(payload) => $emit('rename-chat-session', payload)"
        @delete-chat-session="(sessionId) => $emit('delete-chat-session', sessionId)"
      />

      <div class="workbench-main-column">
      <QuestionComposer
        :selected-project-id="selectedProjectId"
        :loading="answerLoading"
        :error="answerError"
        :status-message="answerStatus || statusMessage"
        :answer-cancel-status="answerCancelStatus"
        @submit-question="(question) => $emit('submit-question', question)"
        @cancel-answer="$emit('cancel-answer')"
        @check-health="$emit('check-health')"
      />
      <ChatThread
        :chat-messages="chatMessages"
        :loading="chatMessagesLoading"
        :error="chatMessagesError"
        :answer-streaming-text="answerStreamingText"
        @delete-chat-message="(messageId) => $emit('delete-chat-message', messageId)"
        @clear-chat-messages="$emit('clear-chat-messages')"
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
      </div>

      <div class="workbench-context-rail">
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
    </div>
  </section>
</template>

<script setup>
import AnswerPanel from "../components/AnswerPanel.vue";
import AgentToolsPanel from "../components/AgentToolsPanel.vue";
import ChatSessionPanel from "../components/ChatSessionPanel.vue";
import ChatThread from "../components/ChatThread.vue";
import FirstRunWizard from "../components/FirstRunWizard.vue";
import QuestionComposer from "../components/QuestionComposer.vue";
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
  firstRunVisible: {
    type: Boolean,
    default: false,
  },
  ollamaStatus: {
    type: Object,
    default: null,
  },
  ollamaStatusLoading: {
    type: Boolean,
    default: false,
  },
  ollamaStatusError: {
    type: String,
    default: "",
  },
  ollamaPullingModel: {
    type: String,
    default: "",
  },
  ollamaPullProgress: {
    type: Object,
    default: null,
  },
  ollamaPullStatus: {
    type: String,
    default: "",
  },
  ollamaPullError: {
    type: String,
    default: "",
  },
  answerStreamingText: {
    type: String,
    default: "",
  },
  answerCancelStatus: {
    type: String,
    default: "",
  },
  chatMessages: {
    type: Array,
    default: () => [],
  },
  chatSessions: {
    type: Array,
    default: () => [],
  },
  selectedChatSessionId: {
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
  chatSessionsLoading: {
    type: Boolean,
    default: false,
  },
  chatSessionsError: {
    type: String,
    default: "",
  },
  chatSessionMutationError: {
    type: String,
    default: "",
  },
  chatSessionMutationStatus: {
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

defineEmits(["check-health", "submit-question", "cancel-answer", "refresh-ollama-status", "pull-ollama-model", "dismiss-first-run", "select-chat-session", "create-chat-session", "rename-chat-session", "delete-chat-session", "delete-chat-message", "clear-chat-messages", "submit-answer-feedback", "run-tool-suggestion", "use-tool-result-context", "clear-tool-context", "run-search-debug", "save-retrieval-settings", "save-retrieval-review", "select-retrieval-review", "delete-retrieval-review", "load-agent-tools", "run-agent-tool", "load-agent-tool-runs", "select-agent-tool-run"]);
</script>

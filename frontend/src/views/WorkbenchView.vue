<template>
  <section class="view-panel chat-view">
    <header class="chat-view-header">
      <div>
        <p class="section-kicker">聊</p>
        <h2>问资料</h2>
        <p>选择左侧工作区，直接围绕资料提问；来源、工具和复盘都收在右侧依据里。</p>
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
      @refresh-ollama-status="emit('refresh-ollama-status')"
      @pull-ollama-model="(model) => emit('pull-ollama-model', model)"
      @create-project="(payload) => emit('create-project', payload)"
      @dismiss-first-run="emit('dismiss-first-run')"
    />

    <div class="workbench-grid phase2-workbench-grid">
      <div class="workbench-main-column">
        <QuestionComposer
          :selected-project-id="selectedProjectId"
          :loading="answerLoading"
          :error="answerError"
          :status-message="answerStatus || statusMessage"
          :answer-cancel-status="answerCancelStatus"
          @submit-question="(question) => emit('submit-question', question)"
          @cancel-answer="emit('cancel-answer')"
          @check-health="emit('check-health')"
          @open-library="emit('open-library')"
          @compare-answers="(payload) => emit('compare-answers', payload)"
          @start-assessment-tool="emit('start-assessment-tool')"
        />
        <ChatThread
          :chat-messages="chatMessages"
          :loading="chatMessagesLoading"
          :error="chatMessagesError"
          :answer-streaming-text="answerStreamingText"
          @edit-chat-message="(message) => emit('edit-chat-message', message)"
          @delete-chat-message="(messageId) => emit('delete-chat-message', messageId)"
          @clear-chat-messages="emit('clear-chat-messages')"
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
          @submit-answer-feedback="(rating) => emit('submit-answer-feedback', rating)"
          @run-tool-suggestion="(suggestion) => emit('run-tool-suggestion', suggestion)"
          @use-tool-result-context="(runId) => emit('use-tool-result-context', runId)"
          @clear-tool-context="emit('clear-tool-context')"
        />
      </div>

      <EvidenceDrawer
        :collapsed="evidenceCollapsed"
        :answer-result="answerResult"
        :tool-suggestion="currentToolSuggestion"
        :last-usable-tool-run="lastUsableToolRun"
        :current-tool-context-run-id="currentToolContextRunId"
        :agent-tool-submitting-name="agentToolSubmittingName"
        @toggle="emit('toggle-evidence')"
        @run-tool-suggestion="(suggestion) => emit('run-tool-suggestion', suggestion)"
        @use-tool-result-context="(runId) => emit('use-tool-result-context', runId)"
        @clear-tool-context="emit('clear-tool-context')"
      >
        <template #advanced>
          <section class="evidence-advanced-panel">
            <div class="context-rail-tabs" role="tablist" aria-label="依据工具">
              <button
                type="button"
                role="tab"
                :aria-selected="activeContextTab === 'debug'"
                :class="{ active: activeContextTab === 'debug' }"
                @click="activeContextTab = 'debug'"
              >
                查来源
              </button>
              <button
                type="button"
                role="tab"
                :aria-selected="activeContextTab === 'review'"
                :class="{ active: activeContextTab === 'review' }"
                @click="activeContextTab = 'review'"
              >
                复盘
              </button>
              <button
                type="button"
                role="tab"
                :aria-selected="activeContextTab === 'tools'"
                :class="{ active: activeContextTab === 'tools' }"
                @click="activeContextTab = 'tools'"
              >
                工具
              </button>
              <button
                type="button"
                role="tab"
                :aria-selected="activeContextTab === 'compare'"
                :class="{ active: activeContextTab === 'compare' }"
                @click="activeContextTab = 'compare'"
              >
                对比
              </button>
            </div>

            <SearchDebugPanel
              v-show="activeContextTab === 'debug' || activeContextTab === 'review'"
              :active-section="activeContextTab"
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
              @run-search-debug="(payload) => emit('run-search-debug', payload)"
              @save-retrieval-settings="(payload) => emit('save-retrieval-settings', payload)"
              @save-retrieval-review="(payload) => emit('save-retrieval-review', payload)"
              @select-retrieval-review="(reviewId) => emit('select-retrieval-review', reviewId)"
              @delete-retrieval-review="(reviewId) => emit('delete-retrieval-review', reviewId)"
            />
            <AgentToolsPanel
              v-show="activeContextTab === 'tools'"
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
              @load-agent-tools="emit('load-agent-tools')"
              @run-agent-tool="(payload) => emit('run-agent-tool', payload)"
              @load-agent-tool-runs="emit('load-agent-tool-runs')"
              @select-agent-tool-run="(runId) => emit('select-agent-tool-run', runId)"
            />
            <ModelComparisonPanel
              v-show="activeContextTab === 'compare'"
              :selected-project-id="selectedProjectId"
              :model-profiles="modelProfiles"
              :model-comparison-result="modelComparisonResult"
              :loading="modelComparisonLoading"
              :error="modelComparisonError"
              :status="modelComparisonStatus"
              @compare-answers="(payload) => emit('compare-answers', payload)"
            />
          </section>
        </template>
      </EvidenceDrawer>
    </div>
  </section>
</template>

<script setup>
import { ref } from "vue";
import AnswerPanel from "../components/AnswerPanel.vue";
import AgentToolsPanel from "../components/AgentToolsPanel.vue";
import ChatThread from "../components/ChatThread.vue";
import EvidenceDrawer from "../components/EvidenceDrawer.vue";
import FirstRunWizard from "../components/FirstRunWizard.vue";
import ModelComparisonPanel from "../components/ModelComparisonPanel.vue";
import QuestionComposer from "../components/QuestionComposer.vue";
import SearchDebugPanel from "../components/SearchDebugPanel.vue";

const activeContextTab = ref("debug");

defineProps({
  statusMessage: {
    type: String,
    required: true,
  },
  selectedProjectId: {
    type: String,
    required: true,
  },
  projectFormSubmitting: {
    type: Boolean,
    default: false,
  },
  projectFormError: {
    type: String,
    default: "",
  },
  projectFormStatus: {
    type: String,
    default: "",
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
  evidenceCollapsed: {
    type: Boolean,
    default: true,
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
  modelProfiles: {
    type: Array,
    default: () => [],
  },
  modelComparisonResult: {
    type: Object,
    default: null,
  },
  modelComparisonLoading: {
    type: Boolean,
    default: false,
  },
  modelComparisonError: {
    type: String,
    default: "",
  },
  modelComparisonStatus: {
    type: String,
    default: "",
  },
  chatMessages: {
    type: Array,
    default: () => [],
  },
  chatMessagesLoading: {
    type: Boolean,
    default: false,
  },
  chatMessagesError: {
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

const emit = defineEmits([
  "cancel-answer",
  "check-health",
  "clear-chat-messages",
  "clear-tool-context",
  "compare-answers",
  "create-project",
  "delete-chat-message",
  "delete-retrieval-review",
  "dismiss-first-run",
  "edit-chat-message",
  "load-agent-tool-runs",
  "load-agent-tools",
  "open-library",
  "pull-ollama-model",
  "refresh-ollama-status",
  "run-agent-tool",
  "run-search-debug",
  "run-tool-suggestion",
  "save-retrieval-review",
  "save-retrieval-settings",
  "select-agent-tool-run",
  "select-retrieval-review",
  "submit-answer-feedback",
  "submit-question",
  "start-assessment-tool",
  "toggle-evidence",
  "use-tool-result-context",
]);
</script>

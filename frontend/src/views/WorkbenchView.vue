<template>
  <div class="page workbench-page">
    <aside class="workbench-side workbench-left">
      <div class="workbench-scroll">
        <ChatSessionPanel
          :selected-project-id="selectedProjectId"
          :chat-sessions="chatSessions"
          :selected-chat-session-id="selectedChatSessionId"
          :chat-sessions-loading="chatSessionsLoading"
          :chat-sessions-error="chatSessionsError"
          :chat-session-mutation-submitting="chatSessionMutationSubmitting"
          :chat-session-mutation-status="chatSessionMutationStatus"
          :chat-session-mutation-error="chatSessionMutationError"
          :deleting-chat-session-id="deletingChatSessionId"
          @refresh-chat-sessions="$emit('refresh-chat-sessions')"
          @select-chat-session="(sessionId) => $emit('select-chat-session', sessionId)"
          @create-chat-session="(title) => $emit('create-chat-session', title)"
          @rename-chat-session="(payload) => $emit('rename-chat-session', payload)"
          @delete-chat-session="(sessionId) => $emit('delete-chat-session', sessionId)"
        />
      </div>
    </aside>

    <main class="conv-col workbench-center" aria-label="对话">
      <div ref="convEl" class="workbench-scroll conv">
        <div v-if="!selectedProjectId" class="conv-empty">
          <div class="conv-empty-mark">
            <svg width="48" height="48" viewBox="0 0 40 40" fill="none">
              <rect x="0.5" y="0.5" width="39" height="39" stroke="currentColor" stroke-opacity="0.2" />
              <g stroke="var(--accent)" fill="none" stroke-width="1">
                <path d="M20 9 L29 25 L11 25 Z" fill="var(--accent)" fill-opacity="0.08" />
                <path d="M20 13 L26 24 L14 24 Z" />
                <path d="M20 17 L23 23 L17 23 Z" />
              </g>
            </svg>
          </div>
          <p class="conv-empty-title">前往资料库创建项目</p>
          <p class="conv-empty-sub">导入本地文档后，在这里向你的知识库提问。</p>
          <button class="btn-ink" type="button" @click="$emit('change-view', 'library')">
            前往资料库 →
          </button>
        </div>

        <div v-else-if="chatMessages.length === 0 && !answerResult && !answerLoading" class="conv-empty">
          <p class="conv-empty-title">暂无对话记录</p>
          <p class="conv-empty-sub">在下方提问，围绕已导入的项目资料进行检索问答。</p>
        </div>

        <template v-else>
          <article
            v-for="(msg, i) in chatThread"
            :key="msg._key"
            class="turn"
            :class="msg.role"
          >
            <div class="speaker">
              {{ msg.role === "user" ? "问 · Quaero" : "答 · Respondeo" }}
            </div>
            <div class="body">
              <template v-if="msg.role === 'user'">
                <div v-if="editingMessageId === msg.messageId" class="branch-editor">
                  <textarea v-model="branchDraft" rows="3" />
                  <div class="branch-actions">
                    <button
                      type="button"
                      :disabled="branchSubmitting || !branchDraft.trim()"
                      @click="submitBranchEdit(msg)"
                    >
                      {{ branchSubmitting ? "保存中…" : "保存" }}
                    </button>
                    <button type="button" :disabled="branchSubmitting" @click="cancelBranchEdit">取消</button>
                  </div>
                  <p v-if="branchError" class="status-line error">{{ branchError }}</p>
                </div>
                <template v-else>
                  <p style="margin:0">{{ msg.content }}</p>
                  <button
                    v-if="selectedChatSessionId && msg.messageId"
                    type="button"
                    class="branch-edit"
                    title="编辑"
                    aria-label="编辑"
                    @click="startBranchEdit(msg)"
                  >
                    ✎
                  </button>
                </template>
              </template>
              <MarkdownBody v-else :content="msg.content" />
            </div>
            <template v-if="msg.role === 'assistant' && msg.sources && msg.sources.length">
              <div class="sources">
                <span class="label">来源</span>
                <span v-for="(src, si) in msg.sources" :key="si" class="src">
                  <span class="roman">{{ ROMAN[si] || si + 1 }}</span>
                  <em>{{ src.path || src.document_path || "未知" }}</em>
                  <span style="color:var(--ink-3)"> · {{ src.snippet || "" }}</span>
                </span>
              </div>
            </template>
          </article>
        </template>

        <article v-if="answerLoading" class="turn assistant turn-streaming">
          <div class="speaker">答 · Respondeo</div>
          <div class="body">
            <MarkdownBody :content="liveAnswer" />
            <span class="cursor" />
          </div>
        </article>

        <article v-if="latestAnswer" ref="latestEl" class="turn assistant">
          <div class="speaker">答 · Respondeo</div>
          <div class="body">
            <MarkdownBody :content="latestAnswer.answer || ''" />
          </div>
          <div class="obs">
            <span>命中 <strong>{{ (latestAnswer.sources || []).length }}</strong></span>
            <span>模式 <strong>{{ latestAnswer.mode || "local" }}</strong></span>
            <span>模型 <strong>{{ latestAnswer.provider || "api" }}</strong></span>
          </div>
          <div v-if="(latestAnswer.sources || []).length" class="sources">
            <span class="label">来源</span>
            <span v-for="(src, si) in latestAnswer.sources" :key="si" class="src">
              <span class="roman">{{ ROMAN[si] || si + 1 }}</span>
              <em>{{ src.path || "未知" }}</em>
              <span style="color:var(--ink-3)"> · {{ src.snippet || "" }}</span>
            </span>
          </div>
          <div class="feedback">
            <button
              v-for="[rating, label] in FEEDBACK"
              :key="rating"
              type="button"
              :class="{ on: lastFeedback === rating }"
              :disabled="answerFeedbackSubmitting || !lastAnswerMessageId"
              @click="doFeedback(rating)"
            >
              {{ label }}
            </button>
          </div>
          <p v-if="answerFeedbackStatus" class="status-line">{{ answerFeedbackStatus }}</p>
          <p v-if="answerFeedbackError" class="status-line error">{{ answerFeedbackError }}</p>
        </article>

        <div v-if="currentToolSuggestion && !answerLoading" class="tool-suggest">
          <span>来源不足，建议运行</span>
          <span class="pill">{{ currentToolSuggestion.tool }}</span>
          <button
            type="button"
            :disabled="!!agentToolSubmittingName"
            @click="$emit('run-tool-suggestion', currentToolSuggestion)"
          >
            {{ agentToolSubmittingName ? "运行中…" : "运行" }}
          </button>
        </div>

        <div v-if="currentToolContextRunId" class="tool-context-notice">
          <p class="section-kicker">下一问将引用工具结果</p>
          <p>运行 ID：{{ currentToolContextRunId }}</p>
          <button type="button" @click="$emit('clear-tool-context')">清除</button>
        </div>
      </div>

      <div class="composer conv-composer">
        <div v-if="cloudModelNotice" class="tool-suggest tool-suggest-sm">
          <span>{{ cloudModelNotice }}</span>
          <span class="pill">cloud model</span>
        </div>
        <form class="composer-row" @submit.prevent="send">
          <textarea
            v-model="draft"
            :disabled="answerLoading || !selectedProjectId"
            placeholder="在此输入问题… Cmd+Enter 发送"
            rows="3"
            @keydown.meta.enter.prevent="send"
            @keydown.ctrl.enter.prevent="send"
          />
          <button
            class="send"
            type="submit"
            :disabled="answerLoading || !selectedProjectId || !draft.trim()"
          >
            {{ answerLoading ? "生成中…" : "发送 ▶" }}
          </button>
        </form>
        <div class="composer-actions">
          <button v-if="answerLoading" type="button" class="btn-ghost" @click="$emit('cancel-answer')">取消</button>
          <span class="status">{{ answerStatus || statusMessage || "" }}</span>
          <p v-if="answerError" class="status-line error" style="margin:0">{{ answerError }}</p>
        </div>
      </div>
    </main>

    <aside class="workbench-side workbench-right">
      <div class="workbench-scroll">
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
      </div>
    </aside>
  </div>
</template>

<script setup>
import { computed, nextTick, ref, watch } from "vue";

import AgentToolsPanel from "../components/AgentToolsPanel.vue";
import ChatSessionPanel from "../components/ChatSessionPanel.vue";
import MarkdownBody from "../components/MarkdownBody.vue";
import SearchDebugPanel from "../components/SearchDebugPanel.vue";

const props = defineProps({
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
  cloudModelNotice: {
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

const emit = defineEmits(["check-health", "submit-question", "cancel-answer", "submit-answer-feedback", "run-tool-suggestion", "use-tool-result-context", "clear-tool-context", "refresh-chat-sessions", "select-chat-session", "create-chat-session", "rename-chat-session", "delete-chat-session", "refresh-chat-messages", "run-search-debug", "save-retrieval-settings", "save-retrieval-review", "select-retrieval-review", "delete-retrieval-review", "load-agent-tools", "run-agent-tool", "load-agent-tool-runs", "select-agent-tool-run", "change-view"]);

const ROMAN = ["i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x"];
const FEEDBACK = [["useful", "有用"], ["not_useful", "无用"], ["source_wrong", "来源不准"], ["need_more_context", "需要更多"]];

const draft = ref("");
const lastFeedback = ref("");
const convEl = ref(null);
const editingMessageId = ref("");
const branchDraft = ref("");
const branchSubmitting = ref(false);
const branchError = ref("");

const chatThread = computed(() => {
  return (props.chatMessages || []).flatMap((msg, index) => {
    const items = [];
    if (msg.question) {
      items.push({
        _key: `${msg.id || index}-q`,
        role: "user",
        content: msg.question,
        messageId: msg.id || "",
      });
    }
    if (msg.answer) {
      items.push({
        _key: `${msg.id || index}-a`,
        role: "assistant",
        content: msg.answer,
        sources: msg.sources || [],
      });
    }
    return items;
  });
});

const liveAnswer = computed(() => {
  return props.answerLoading ? (props.answerResult?.answer || "") : "";
});

const latestAnswer = computed(() => {
  return !props.answerLoading && props.answerResult ? props.answerResult : null;
});

function send() {
  if (!draft.value.trim() || props.answerLoading) {
    return;
  }
  emit("submit-question", draft.value);
  draft.value = "";
}

function doFeedback(rating) {
  lastFeedback.value = rating;
  emit("submit-answer-feedback", rating);
}

function startBranchEdit(msg) {
  editingMessageId.value = msg.messageId;
  branchDraft.value = msg.content || "";
  branchError.value = "";
}

function cancelBranchEdit() {
  editingMessageId.value = "";
  branchDraft.value = "";
  branchError.value = "";
}

async function submitBranchEdit(msg) {
  const question = branchDraft.value.trim();
  if (!question || !props.selectedChatSessionId || !msg.messageId) {
    return;
  }
  branchSubmitting.value = true;
  branchError.value = "";
  try {
    const response = await fetch("/api/chat/messages/branch", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: props.selectedChatSessionId,
        parent_message_id: msg.messageId,
        question,
      }),
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(data.error || "分支创建失败");
    }
    cancelBranchEdit();
    emit("refresh-chat-messages");
  } catch (error) {
    branchError.value = error instanceof Error ? error.message : "分支创建失败";
  } finally {
    branchSubmitting.value = false;
  }
}

watch(
  () => [props.answerLoading, props.chatMessages?.length, props.answerResult?.answer?.length],
  async () => {
    await nextTick();
    convEl.value?.scrollTo({ top: convEl.value.scrollHeight, behavior: "smooth" });
  },
);
</script>

<style scoped>
.turn.user .body {
  position: relative;
}

.branch-edit {
  position: absolute;
  top: -2px;
  right: -2px;
  width: 28px;
  height: 28px;
  border: 1px solid var(--line);
  background: var(--paper);
  color: var(--ink-2);
  opacity: 0;
  transition: opacity 0.15s ease, color 0.15s ease;
}

.turn.user:hover .branch-edit,
.branch-edit:focus-visible {
  opacity: 1;
}

.branch-edit:hover {
  color: var(--ink);
}

.branch-editor {
  display: grid;
  gap: 8px;
}

.branch-editor textarea {
  width: 100%;
  min-height: 96px;
  resize: vertical;
}

.branch-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}
</style>

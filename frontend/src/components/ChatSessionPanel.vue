<template>
  <section class="chat-session-panel" aria-labelledby="chat-session-panel-title">
    <div class="col-head">
      <span id="chat-session-panel-title">聊天会话 · 会话</span>
      <span class="num">{{ chatSessions.length }}</span>
    </div>

    <p v-if="!selectedProjectId" class="status-line">请选择项目空间后查看会话。</p>
    <p v-if="chatSessionsError" class="status-line error">{{ chatSessionsError }}</p>
    <p v-if="chatSessionMutationStatus" class="status-line">{{ chatSessionMutationStatus }}</p>
    <p v-if="chatSessionMutationError" class="status-line error">{{ chatSessionMutationError }}</p>

    <button
      type="button"
      class="new-session"
      :disabled="!selectedProjectId || chatSessionMutationSubmitting"
      @click="$emit('create-chat-session', '')"
    >
      ＋ 新建会话
    </button>

    <form class="chat-session-form atlas-inline-form" @submit.prevent="createSession">
      <input v-model="newSessionTitle" :disabled="!selectedProjectId || chatSessionMutationSubmitting" placeholder="命名会话" />
      <button type="submit" :disabled="!selectedProjectId || chatSessionMutationSubmitting">保存</button>
    </form>

    <ul class="sessions">
      <li class="session-item" :class="{ active: !selectedChatSessionId }" @click="$emit('select-chat-session', '')">
        <span class="marker">0</span>
        <span>
          <div class="title">默认会话</div>
          <div class="meta">系统默认 · 历史消息</div>
        </span>
      </li>
      <li
        v-for="session in chatSessions"
        :key="session.id"
        class="session-item"
        :class="{ active: selectedChatSessionId === session.id }"
        @click="$emit('select-chat-session', session.id)"
      >
        <span class="marker">{{ sessionMarker(session) }}</span>
        <span>
          <div class="title">{{ session.title || "未命名会话" }}</div>
          <div class="meta">{{ session.created_at || session.updated_at || "未记录时间" }} · {{ session.message_count ?? 0 }} 轮</div>
        </span>
        <form v-if="renamingSessionId === session.id" class="chat-session-rename" @submit.prevent="renameSession(session.id)">
          <input v-model="renameTitle" :disabled="chatSessionMutationSubmitting" />
          <button type="submit" :disabled="chatSessionMutationSubmitting">保存</button>
          <button type="button" @click="cancelRename">取消</button>
        </form>
        <div v-else class="inline-actions">
          <button type="button" @click="startRename(session)">重命名</button>
          <button type="button" :disabled="deletingChatSessionId === session.id" @click="$emit('delete-chat-session', session.id)">
            {{ deletingChatSessionId === session.id ? "删除中..." : "删除会话" }}
          </button>
        </div>
      </li>
    </ul>

    <div class="chat-history">
      <div class="col-head">
        <span>历史消息</span>
        <button type="button" :disabled="!selectedProjectId || chatMessagesLoading" @click="$emit('refresh-chat-messages')">
          {{ chatMessagesLoading ? "读取中" : "刷新" }}
        </button>
      </div>
      <p v-if="chatMessagesLoading" class="status-line">正在读取历史消息...</p>
      <p v-if="chatMessagesError" class="status-line error">{{ chatMessagesError }}</p>
      <p v-if="chatMessages.length === 0" class="muted-line">暂无聊天记录</p>
      <ol v-else>
        <li v-for="message in chatMessages" :key="message.id">
          <strong>{{ message.question || "未记录问题" }}</strong>
          <p>{{ message.answer || "暂无回答" }}</p>
        </li>
      </ol>
    </div>
  </section>
</template>

<script setup>
import { ref } from "vue";

const props = defineProps({
  selectedProjectId: {
    type: String,
    required: true,
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
});

const emit = defineEmits(["refresh-chat-sessions", "select-chat-session", "create-chat-session", "rename-chat-session", "delete-chat-session", "refresh-chat-messages"]);
const newSessionTitle = ref("");
const renamingSessionId = ref("");
const renameTitle = ref("");
const romanNumerals = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII"];

function sessionMarker(session) {
  const index = chatSessionsIndex(session);
  return romanNumerals[index] || index + 1;
}

function chatSessionsIndex(session) {
  const index = props.chatSessions.findIndex((entry) => entry.id === session?.id);
  return index >= 0 ? index : 0;
}

function createSession() {
  emit("create-chat-session", newSessionTitle.value);
  newSessionTitle.value = "";
}

function startRename(session) {
  renamingSessionId.value = session.id;
  renameTitle.value = session.title || "";
}

function cancelRename() {
  renamingSessionId.value = "";
  renameTitle.value = "";
}

function renameSession(sessionId) {
  emit("rename-chat-session", { sessionId, title: renameTitle.value });
  cancelRename();
}
</script>

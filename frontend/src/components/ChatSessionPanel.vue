<template>
  <section class="chat-session-panel" aria-labelledby="chat-session-title">
    <div class="section-title-row">
      <div>
        <p class="section-kicker">会话</p>
        <h2 id="chat-session-title">项目会话</h2>
      </div>
      <button type="button" :disabled="loading || !selectedProjectId" @click="createSession">
        新建会话
      </button>
    </div>

    <p v-if="!selectedProjectId" class="status-line">未选择项目空间</p>
    <p v-else-if="loading" class="status-line">正在读取会话...</p>
    <p v-else-if="error" class="status-line error">{{ error }}</p>
    <p v-if="mutationStatus" class="status-line">{{ mutationStatus }}</p>
    <p v-if="mutationError" class="status-line error">{{ mutationError }}</p>

    <form class="chat-session-form" @submit.prevent="createSession">
      <label>
        会话标题
        <input v-model.trim="newSessionTitle" name="chat-session-title" placeholder="例如：MVP 架构梳理" />
      </label>
    </form>

    <ul v-if="chatSessions.length" class="chat-session-list">
      <li v-for="session in chatSessions" :key="sessionId(session)">
        <button
          type="button"
          class="chat-session-select"
          :class="{ active: sessionId(session) === selectedChatSessionId }"
          @click="$emit('select-chat-session', sessionId(session))"
        >
          {{ session.title || session.name || "未命名会话" }}
        </button>
        <div class="chat-session-actions">
          <input
            v-model.trim="renameDrafts[sessionId(session)]"
            :aria-label="`重命名 ${session.title || '会话'}`"
            placeholder="新标题"
          />
          <button type="button" @click="renameSession(session)">重命名</button>
          <button type="button" @click="$emit('delete-chat-session', sessionId(session))">删除</button>
        </div>
      </li>
    </ul>
    <p v-else-if="selectedProjectId && !loading" class="muted-line">暂无会话，提问时会写入当前项目。</p>
  </section>
</template>

<script setup>
import { reactive, ref } from "vue";

defineProps({
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
  loading: {
    type: Boolean,
    default: false,
  },
  error: {
    type: String,
    default: "",
  },
  mutationStatus: {
    type: String,
    default: "",
  },
  mutationError: {
    type: String,
    default: "",
  },
});

const emit = defineEmits(["select-chat-session", "create-chat-session", "rename-chat-session", "delete-chat-session"]);
const newSessionTitle = ref("");
const renameDrafts = reactive({});

function sessionId(session) {
  return String(session.id || session.session_id || "");
}

function createSession() {
  emit("create-chat-session", newSessionTitle.value);
  newSessionTitle.value = "";
}

function renameSession(session) {
  const id = sessionId(session);
  const title = renameDrafts[id] || session.title || session.name || "";
  emit("rename-chat-session", { sessionId: id, title });
  renameDrafts[id] = "";
}
</script>

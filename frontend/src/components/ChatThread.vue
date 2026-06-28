<template>
  <section class="chat-thread" aria-labelledby="chat-thread-title">
    <div class="section-title-row">
      <div>
        <p class="section-kicker">对话</p>
        <h2 id="chat-thread-title">会话消息</h2>
      </div>
      <button type="button" :disabled="loading || chatMessages.length === 0" @click="$emit('clear-chat-messages')">
        清空记录
      </button>
    </div>

    <p v-if="loading" class="status-line">正在读取消息...</p>
    <p v-else-if="error" class="status-line error">{{ error }}</p>
    <p v-else-if="chatMessages.length === 0 && !answerStreamingText" class="muted-line">当前会话暂无消息。</p>

    <ol v-if="chatMessages.length" class="chat-message-list">
      <li v-for="message in chatMessages" :key="message.id || message.message_id">
        <div class="chat-message-header">
          <span>{{ message.role || message.type || "message" }}</span>
          <button type="button" @click="$emit('delete-chat-message', message.id || message.message_id)">删除</button>
        </div>
        <p>{{ message.content || message.answer || message.question || message.text || "暂无内容" }}</p>
      </li>
    </ol>

    <div v-if="answerStreamingText" class="chat-streaming-draft">
      <p class="section-kicker">正在生成</p>
      <p>{{ answerStreamingText }}</p>
    </div>
  </section>
</template>

<script setup>
defineProps({
  chatMessages: {
    type: Array,
    default: () => [],
  },
  loading: {
    type: Boolean,
    default: false,
  },
  error: {
    type: String,
    default: "",
  },
  answerStreamingText: {
    type: String,
    default: "",
  },
});

defineEmits(["delete-chat-message", "clear-chat-messages"]);
</script>

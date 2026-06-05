<template>
  <section class="question-panel composer" aria-labelledby="question-panel-title">
    <div class="col-head">
      <span id="question-panel-title">提问</span>
      <button type="button" @click="$emit('check-health')">检查服务</button>
    </div>
    <p class="section-kicker">输入问题</p>

    <div v-if="!selectedProjectId" class="tool-suggest">
      <span>未选择项目空间</span>
      <span class="pill">project_required</span>
    </div>
    <div v-else-if="cloudModelNotice" class="tool-suggest">
      <span>{{ cloudModelNotice || "本轮会把检索到的来源片段发送给云端模型：DeepSeek / OpenAI-compatible API。" }}</span>
      <span class="pill">cloud model</span>
    </div>

    <form class="composer-row" @submit.prevent="submitQuestion">
      <textarea
        v-model="questionText"
        :disabled="loading"
        placeholder="在此输入问题…  Cmd+Enter 发送"
        aria-label="输入问题，例如：这个项目的默认入口是什么？"
        rows="5"
        @keydown.meta.enter.prevent="submitQuestion"
        @keydown.ctrl.enter.prevent="submitQuestion"
      ></textarea>
      <button class="send" type="submit" :disabled="loading || !selectedProjectId">
        {{ loading ? "生成中…" : "发送 ▶" }}
      </button>
    </form>

    <div class="composer-actions">
      <button v-if="loading" type="button" class="btn-ghost" @click="$emit('cancel-answer')">
        取消当前回答
      </button>
      <span class="status">{{ statusMessage }}</span>
    </div>
    <p v-if="error" class="status-line error">{{ error }}</p>
  </section>
</template>

<script setup>
import { ref } from "vue";

defineProps({
  selectedProjectId: {
    type: String,
    required: true,
  },
  loading: {
    type: Boolean,
    default: false,
  },
  error: {
    type: String,
    default: "",
  },
  statusMessage: {
    type: String,
    default: "",
  },
  cloudModelNotice: {
    type: String,
    default: "",
  },
});

const emit = defineEmits(["submit-question", "cancel-answer", "check-health"]);
const questionText = ref("");

function submitQuestion() {
  emit("submit-question", questionText.value);
  questionText.value = "";
}
</script>

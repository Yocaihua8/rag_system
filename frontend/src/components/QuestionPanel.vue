<template>
  <section class="question-panel" aria-labelledby="question-panel-title">
    <div class="section-title-row">
      <div>
        <p class="section-kicker">输入问题</p>
        <h2 id="question-panel-title">项目问答</h2>
      </div>
      <button type="button" @click="$emit('check-health')">检查本地服务</button>
    </div>

    <p v-if="!selectedProjectId" class="status-line">未选择项目空间</p>

    <form class="question-form" @submit.prevent="submitQuestion">
      <label>
        输入问题
        <textarea
          v-model="questionText"
          :disabled="loading"
          placeholder="例如：这个项目的默认入口是什么？"
          rows="5"
        ></textarea>
      </label>
      <div class="actions">
        <button type="submit" :disabled="loading || !selectedProjectId">
          {{ loading ? "提问中..." : "提问" }}
        </button>
        <span class="status">{{ statusMessage }}</span>
      </div>
      <p v-if="error" class="status-line error">{{ error }}</p>
    </form>
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
});

const emit = defineEmits(["submit-question", "check-health"]);
const questionText = ref("");

function submitQuestion() {
  emit("submit-question", questionText.value);
}
</script>

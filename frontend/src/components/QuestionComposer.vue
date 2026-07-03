<template>
  <section class="question-composer" aria-labelledby="question-composer-title">
    <div class="section-title-row">
      <div>
        <p class="section-kicker">聊天</p>
        <h2 id="question-composer-title">问资料</h2>
      </div>
      <button type="button" @click="emit('check-health')">检查本地服务</button>
    </div>

    <p v-if="!selectedProjectId" class="status-line">未选择项目空间</p>

    <form class="question-form" @submit.prevent="submitQuestion">
      <label class="composer-field">
        <span class="sr-only">输入问题</span>
        <textarea
          v-model="questionText"
          :disabled="loading"
          placeholder="直接问你的资料，例如：这个文件夹主要讲了什么？"
          rows="5"
        ></textarea>
      </label>

      <div class="composer-tool-row" aria-label="添加内容和快捷工具">
        <div class="composer-tool-group">
          <button
            type="button"
            class="icon-button"
            data-composer-action="add"
            aria-label="添加"
            title="添加"
          >
            +
          </button>
          <button
            type="button"
            class="icon-button"
            data-composer-action="shortcut"
            aria-label="快捷指令"
            title="快捷指令"
          >
            /
          </button>
          <div class="composer-menu" aria-label="添加">
            <button type="button" @click="emit('open-library')">加入资料</button>
            <button type="button">上传临时文件</button>
            <button type="button" @click="emit('start-assessment-tool')">练习与小测</button>
            <button type="button">整理要点</button>
          </div>
          <div class="composer-menu" aria-label="快捷指令">
            <button type="button">常用指令</button>
            <button type="button" @click="emit('open-tool-panel')">连接工具</button>
            <button type="button" @click="emit('compare-answers', { question: questionText, profileIds: [] })">
              对比回答
            </button>
          </div>
        </div>

        <div class="composer-tool-group align-right" aria-label="回答设置">
          <label class="compact-select">
            <span>回答</span>
            <select>
              <option>本机回答</option>
              <option>云端回答</option>
            </select>
          </label>
          <label class="compact-select">
            <span>深度</span>
            <select>
              <option>标准</option>
              <option>更快</option>
              <option>更细</option>
            </select>
          </label>
        </div>
      </div>

      <div class="actions composer-actions">
        <span class="status">{{ statusMessage }}</span>
        <button
          type="button"
          data-composer-action="cancel-answer"
          :disabled="!loading"
          @click="emit('cancel-answer')"
        >
          取消
        </button>
        <button type="submit" :disabled="loading || !selectedProjectId">
          {{ loading ? "回答中..." : "发送" }}
        </button>
      </div>
      <p v-if="answerCancelStatus" class="status-line">{{ answerCancelStatus }}</p>
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
  answerCancelStatus: {
    type: String,
    default: "",
  },
});

const emit = defineEmits([
  "cancel-answer",
  "check-health",
  "compare-answers",
  "open-library",
  "open-tool-panel",
  "start-assessment-tool",
  "submit-question",
]);
const questionText = ref("");

function submitQuestion() {
  emit("submit-question", questionText.value);
}
</script>

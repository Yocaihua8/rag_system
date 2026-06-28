<template>
  <section class="first-run-wizard" aria-labelledby="first-run-title">
    <div class="section-title-row">
      <div>
        <p class="section-kicker">首次运行</p>
        <h2 id="first-run-title">启动向导</h2>
      </div>
      <button type="button" class="secondary" @click="$emit('dismiss-first-run')">
        稍后
      </button>
    </div>

    <div class="first-run-grid">
      <article class="first-run-step">
        <p class="step-index">1</p>
        <h3>Ollama</h3>
        <p :class="['status-line', ollamaAvailable ? 'success' : '']">{{ ollamaStatusText }}</p>
        <p v-if="ollamaStatusError" class="status-line error">{{ ollamaStatusError }}</p>
        <p class="muted-line">{{ localModelsText }}</p>
        <button type="button" :disabled="ollamaStatusLoading" @click="$emit('refresh-ollama-status')">
          {{ ollamaStatusLoading ? "检测中..." : "重新检测" }}
        </button>
      </article>

      <article class="first-run-step">
        <p class="step-index">2</p>
        <h3>本地模型</h3>
        <div class="model-choice-list">
          <button
            v-for="item in recommendedModels"
            :key="item.model"
            type="button"
            :disabled="Boolean(ollamaPullingModel)"
            @click="$emit('pull-ollama-model', item.model)"
          >
            <span>{{ item.model }}</span>
            <small>{{ item.label }} · {{ item.size_hint }}</small>
          </button>
        </div>
        <progress v-if="ollamaPullProgress" :value="progressPercent" max="100"></progress>
        <p class="status-line">{{ ollamaPullStatus || "选择模型后开始下载" }}</p>
        <p v-if="ollamaPullError" class="status-line error">{{ ollamaPullError }}</p>
      </article>

      <article class="first-run-step">
        <p class="step-index">3</p>
        <h3>第一个知识库</h3>
        <p class="status-line">{{ selectedProjectId ? "已创建项目空间" : "未创建项目空间" }}</p>
        <form class="project-form" @submit.prevent="submitProject">
          <label>
            项目名称
            <input v-model.trim="projectForm.name" name="first-run-project-name" placeholder="我的知识库" />
          </label>
          <label>
            本地目录
            <input v-model.trim="projectForm.path" name="first-run-project-path" placeholder="E:\\Docs\\Knowledge" required />
          </label>
          <button type="submit" :disabled="projectFormSubmitting">
            {{ projectFormSubmitting ? "创建中..." : "创建知识库" }}
          </button>
        </form>
        <p class="status-line">{{ projectFormStatus }}</p>
        <p v-if="projectFormError" class="status-line error">{{ projectFormError }}</p>
      </article>
    </div>
  </section>
</template>

<script setup>
import { computed, reactive } from "vue";

const FALLBACK_RECOMMENDED_MODELS = [
  { model: "qwen2.5:3b", label: "轻量 CPU 可用", size_hint: "~2GB" },
  { model: "qwen2.5:7b", label: "均衡推荐", size_hint: "~5GB" },
  { model: "deepseek-r1:8b", label: "推理增强", size_hint: "~5GB" },
];

const props = defineProps({
  selectedProjectId: {
    type: String,
    default: "",
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
});

const emit = defineEmits(["refresh-ollama-status", "pull-ollama-model", "create-project", "dismiss-first-run"]);

const projectForm = reactive({
  name: "我的知识库",
  path: "",
});

const ollamaAvailable = computed(() => props.ollamaStatus?.available === true);

const recommendedModels = computed(() => {
  const models = props.ollamaStatus?.recommended_models || [];
  return models.length > 0 ? models : FALLBACK_RECOMMENDED_MODELS;
});

const progressPercent = computed(() => {
  const progress = Number(props.ollamaPullProgress?.progress || 0);
  return Math.max(0, Math.min(100, Math.round(progress * 100)));
});

const ollamaStatusText = computed(() => {
  if (props.ollamaStatusLoading) {
    return "正在检测 Ollama";
  }
  if (!props.ollamaStatus) {
    return "等待检测 Ollama";
  }
  return ollamaAvailable.value ? "Ollama 可用" : "Ollama 不可用";
});

const localModelsText = computed(() => {
  const models = props.ollamaStatus?.models || [];
  if (models.length === 0) {
    return "本地暂无推荐模型";
  }
  return `本地模型：${models.join("、")}`;
});

function submitProject() {
  emit("create-project", {
    name: projectForm.name,
    path: projectForm.path,
  });
}
</script>

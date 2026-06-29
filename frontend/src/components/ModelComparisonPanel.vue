<template>
  <section class="model-comparison-panel" aria-labelledby="model-comparison-title">
    <div class="section-title-row">
      <div>
        <p class="section-kicker">模型并排对比</p>
        <h2 id="model-comparison-title">模型并排对比</h2>
      </div>
    </div>

    <form class="comparison-form" @submit.prevent="submitComparison">
      <label>
        问题
        <textarea v-model="question" rows="3" placeholder="输入同一个问题，对比两个模型的回答" />
      </label>
      <div class="comparison-selects">
        <label>
          选择 2 个模型 Profile
          <select v-model="firstProfileId" :disabled="loading">
            <option value="">第一个 Profile</option>
            <option v-for="profile in modelProfiles" :key="profile.id" :value="profile.id">
              {{ profile.name }} / {{ profile.model }}
            </option>
          </select>
        </label>
        <label>
          选择 2 个模型 Profile
          <select v-model="secondProfileId" :disabled="loading">
            <option value="">第二个 Profile</option>
            <option v-for="profile in modelProfiles" :key="profile.id" :value="profile.id">
              {{ profile.name }} / {{ profile.model }}
            </option>
          </select>
        </label>
      </div>
      <button type="submit" :disabled="loading || !selectedProjectId">
        {{ loading ? "对比中..." : "开始对比" }}
      </button>
    </form>

    <p v-if="status" class="status-line">{{ status }}</p>
    <p v-if="error" class="status-line error">{{ error }}</p>
    <p v-if="!selectedProjectId" class="muted-line">请选择项目空间后再对比模型。</p>
    <p v-else-if="modelProfiles.length < 2" class="muted-line">请先在设置中保存至少 2 个模型 Profile。</p>

    <div v-if="modelComparisonResult" class="comparison-result">
      <div
        v-for="result in modelComparisonResult.results || []"
        :key="result.profile_id"
        class="comparison-result-column"
      >
        <p class="section-kicker">{{ result.profile_name || "未命名 Profile" }}</p>
        <h3>{{ result.model || "未知模型" }}</h3>
        <p class="muted-line">mode: {{ result.mode || "local" }} / provider: {{ result.provider || "local" }}</p>
        <p v-if="result.warning" class="status-line error">{{ result.warning }}</p>
        <div class="answer-body">
          <p>{{ result.answer || "暂无回答" }}</p>
        </div>
      </div>
    </div>

    <div v-if="modelComparisonResult" class="source-quality">
      <p class="section-kicker">共用来源质量</p>
      <p>{{ sourceQualityText }}</p>
    </div>
  </section>
</template>

<script setup>
import { computed, ref } from "vue";

const props = defineProps({
  selectedProjectId: {
    type: String,
    required: true,
  },
  modelProfiles: {
    type: Array,
    default: () => [],
  },
  modelComparisonResult: {
    type: Object,
    default: null,
  },
  loading: {
    type: Boolean,
    default: false,
  },
  error: {
    type: String,
    default: "",
  },
  status: {
    type: String,
    default: "",
  },
});

const emit = defineEmits(["compare-answers"]);

const question = ref("");
const firstProfileId = ref("");
const secondProfileId = ref("");

const sourceQualityText = computed(() => {
  const sourceQuality = props.modelComparisonResult?.source_quality;
  if (!sourceQuality) {
    return "来源质量：暂无来源质量摘要";
  }
  return sourceQuality.label || sourceQuality.reason || `来源质量：${sourceQuality.level || "unknown"}`;
});

function submitComparison() {
  emit("compare-answers", {
    question: question.value,
    profileIds: [firstProfileId.value, secondProfileId.value],
  });
}
</script>

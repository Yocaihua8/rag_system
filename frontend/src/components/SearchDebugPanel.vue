<template>
  <section class="search-debug-panel" aria-labelledby="search-debug-title">
    <div class="section-title-row">
      <div>
        <p class="section-kicker">检索调试</p>
        <h2 id="search-debug-title">检索调试</h2>
        <p>查看命中片段、分数和实际上下文。</p>
      </div>
      <button type="submit" form="search-debug-form" :disabled="searchDebugLoading || !selectedProjectId">
        {{ searchDebugLoading ? "诊断中..." : "运行诊断" }}
      </button>
    </div>

    <div class="retrieval-settings-row">
      <div>
        <p class="section-kicker">检索默认值</p>
        <p>{{ retrievalSettingsStatus || defaultSettingsText }}</p>
      </div>
      <button
        type="button"
        :disabled="retrievalSettingsLoading || retrievalSettingsSaving || !selectedProjectId"
        @click="saveRetrievalSettings"
      >
        {{ retrievalSettingsSaving ? "保存中..." : "保存为默认" }}
      </button>
    </div>
    <p v-if="retrievalSettingsError" class="status-line error">{{ retrievalSettingsError }}</p>

    <form id="search-debug-form" class="search-debug-form" @submit.prevent="runSearchDebug">
      <label>
        诊断查询
        <input v-model="searchDebugQuery" placeholder="例如：默认入口、API endpoint" />
      </label>
      <label>
        Top K
        <input v-model.number="searchDebugParameters.topK" type="number" min="1" max="20" />
      </label>
      <label>
        最低分
        <input v-model.number="searchDebugParameters.minScore" type="number" min="0" step="0.1" />
      </label>
      <label class="check-row">
        <input v-model="searchDebugParameters.useKeyword" type="checkbox" />
        关键词
      </label>
      <label class="check-row">
        <input v-model="searchDebugParameters.useVector" type="checkbox" />
        向量
      </label>
    </form>

    <p v-if="!selectedProjectId" class="muted-line">请选择项目空间后运行检索诊断。</p>
    <p v-if="searchDebugStatus" class="status-line">{{ searchDebugStatus }}</p>
    <p v-if="searchDebugError" class="status-line error">{{ searchDebugError }}</p>

    <div class="search-debug-result">
      <p v-if="!searchDebugResult" class="muted-line">暂无检索诊断</p>
      <template v-else>
        <div class="debug-summary-grid">
          <div>
            <p class="section-kicker">来源质量</p>
            <p>{{ sourceQuality.label || sourceQuality.level || "未知" }}</p>
            <small>{{ sourceQuality.reason || "暂无来源质量说明" }}</small>
          </div>
          <div>
            <p class="section-kicker">文档/分块</p>
            <p>{{ debug.document_count ?? 0 }} / {{ debug.chunk_count ?? 0 }}</p>
          </div>
          <div>
            <p class="section-kicker">向量可用</p>
            <p>{{ debug.vector_available ? "是" : "否" }}</p>
          </div>
          <div>
            <p class="section-kicker">本次参数</p>
            <p>top_k={{ parameters.top_k ?? "" }} min_score={{ parameters.min_score ?? "" }}</p>
            <small>keyword={{ parameters.use_keyword ? "on" : "off" }} vector={{ parameters.use_vector ? "on" : "off" }}</small>
          </div>
        </div>

        <div class="debug-hits">
          <p class="section-kicker">命中片段</p>
          <p v-if="hits.length === 0" class="muted-line">暂无命中片段。</p>
          <ol v-else>
            <li v-for="hit in hits" :key="hit.chunk_id || hit.document_id || hit.path">
              <strong>{{ hit.path || "未知来源" }}</strong>
              <small>
                score={{ formatScore(hit.score) }}
                keyword={{ formatScore(hit.keyword_score) }}
                vector={{ formatScore(hit.vector_score) }}
                retrieval={{ hit.retrieval || "" }}
              </small>
              <p>{{ hit.snippet || "无片段预览" }}</p>
            </li>
          </ol>
        </div>
      </template>
    </div>
  </section>
</template>

<script setup>
import { computed, reactive, ref, watch } from "vue";

const props = defineProps({
  selectedProjectId: {
    type: String,
    required: true,
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
});

const emit = defineEmits(["run-search-debug", "save-retrieval-settings"]);

const searchDebugQuery = ref("");
const searchDebugParameters = reactive({
  topK: 5,
  minScore: 0,
  useKeyword: true,
  useVector: true,
});

const debug = computed(() => props.searchDebugResult?.debug || {});
const sourceQuality = computed(() => debug.value.quality || props.searchDebugResult?.source_quality || {});
const parameters = computed(() => debug.value.parameters || {});
const hits = computed(() => props.searchDebugResult?.hits || []);
const defaultSettingsText = computed(() => (
  props.retrievalSettingsLoading ? "正在读取当前项目默认值..." : "未保存项目默认值，使用本地默认参数。"
));

watch(
  () => props.retrievalSettings,
  (settings) => applyRetrievalSettings(settings),
  { immediate: true },
);

function runSearchDebug() {
  emit("run-search-debug", {
    query: searchDebugQuery.value,
    topK: searchDebugParameters.topK,
    minScore: searchDebugParameters.minScore,
    useKeyword: searchDebugParameters.useKeyword,
    useVector: searchDebugParameters.useVector,
  });
}

function saveRetrievalSettings() {
  emit("save-retrieval-settings", {
    topK: searchDebugParameters.topK,
    minScore: searchDebugParameters.minScore,
    useKeyword: searchDebugParameters.useKeyword,
    useVector: searchDebugParameters.useVector,
  });
}

function applyRetrievalSettings(settings) {
  const values = settings || {
    top_k: 5,
    min_score: 0,
    use_keyword: true,
    use_vector: true,
  };
  searchDebugParameters.topK = values.top_k ?? 5;
  searchDebugParameters.minScore = values.min_score ?? 0;
  searchDebugParameters.useKeyword = Boolean(values.use_keyword);
  searchDebugParameters.useVector = Boolean(values.use_vector);
}

function formatScore(score) {
  const value = Number(score);
  return Number.isFinite(value) ? value.toFixed(3) : "0.000";
}
</script>

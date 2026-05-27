<template>
  <section class="view-panel settings-view">
    <header class="topbar">
      <div>
        <p class="section-kicker">设置</p>
        <h2>设置</h2>
        <p>B-141R 已迁移模型设置和模型 Profile；Prompt 预设后续迁移。</p>
      </div>
      <button type="button" :disabled="llmSettingsLoading || modelProfilesLoading" @click="$emit('load-settings')">
        {{ llmSettingsLoading || modelProfilesLoading ? "刷新中..." : "刷新设置" }}
      </button>
    </header>

    <div class="settings-grid">
      <section class="settings-panel">
        <div class="section-title-row">
          <div>
            <p class="section-kicker">模型设置</p>
            <h3>基础 LLM 连接</h3>
          </div>
          <button type="button" :disabled="llmSettingsTesting" @click="$emit('test-llm-settings')">
            {{ llmSettingsTesting ? "测试中..." : "测试连接" }}
          </button>
        </div>

        <form class="project-form" @submit.prevent="submitLlmSettings">
          <label>
            模型提供商
            <select v-model="llmForm.provider" name="provider" :disabled="llmSettingsSubmitting">
              <option value="api">DeepSeek / OpenAI-compatible API</option>
              <option value="ollama">Ollama 本地模式</option>
            </select>
          </label>
          <label>
            API 地址
            <input
              v-model.trim="llmForm.apiBase"
              name="api_base"
              placeholder="例如：https://api.deepseek.com/v1"
              :disabled="llmSettingsSubmitting"
            />
          </label>
          <label>
            模型名称
            <input
              v-model.trim="llmForm.model"
              name="model"
              placeholder="例如：deepseek-chat"
              :disabled="llmSettingsSubmitting"
            />
          </label>
          <label>
            API Key
            <input
              v-model="llmForm.apiKey"
              name="api_key"
              type="password"
              autocomplete="off"
              placeholder="粘贴 API Key；留空不覆盖已有 Key"
              :disabled="llmSettingsSubmitting"
            />
          </label>
          <p class="muted-line">页面只显示 Key 状态，不回显明文；留空不覆盖已有 Key。</p>
          <p v-if="llmSettingsError" class="status-line error">{{ llmSettingsError }}</p>
          <p class="status-line">{{ llmSettingsStatus || llmSettingsSummary }}</p>
          <div class="actions">
            <button type="submit" :disabled="llmSettingsSubmitting">
              {{ llmSettingsSubmitting ? "保存中..." : "保存模型设置" }}
            </button>
          </div>
        </form>
      </section>

      <section class="settings-panel">
        <div class="section-title-row">
          <div>
            <p class="section-kicker">模型 Profile</p>
            <h3>常用模型配置</h3>
          </div>
          <button type="button" :disabled="modelProfilesLoading" @click="$emit('load-model-profiles')">
            {{ modelProfilesLoading ? "刷新中..." : "刷新 Profile" }}
          </button>
        </div>

        <p class="status-line">当前默认：{{ defaultModelProfileLabel }}</p>
        <p v-if="modelProfileMutationError" class="status-line error">{{ modelProfileMutationError }}</p>
        <p class="status-line">{{ modelProfileStatus }}</p>

        <ul class="model-profile-list">
          <li v-for="profile in modelProfiles" :key="profile.id">
            <div>
              <strong>{{ profile.name }}</strong>
              <small>{{ profile.provider }} / {{ profile.model }}</small>
              <small>Key：{{ profile.has_api_key ? profile.api_key_source || "已配置" : "未配置" }}</small>
            </div>
            <div class="actions compact-actions">
              <button type="button" @click="editProfile(profile)">编辑</button>
              <button type="button" :disabled="modelProfileDefaultSubmitting" @click="$emit('set-default-model-profile', profile.id)">
                {{ profile.id === defaultModelProfileId ? "默认" : "设为默认" }}
              </button>
              <button type="button" :disabled="modelProfileTestingId === profile.id" @click="$emit('test-model-profile', profile.id)">
                {{ modelProfileTestingId === profile.id ? "测试中..." : "测试 Profile" }}
              </button>
              <button
                class="danger-link"
                type="button"
                :disabled="modelProfileDeletingId === profile.id"
                @click="$emit('delete-model-profile', profile.id)"
              >
                {{ modelProfileDeletingId === profile.id ? "删除中..." : "删除 Profile" }}
              </button>
            </div>
          </li>
        </ul>
        <p v-if="modelProfiles.length === 0" class="status-line">暂无模型 Profile，可保存当前常用模型配置。</p>
        <p v-if="modelProfileLoadError" class="status-line error">{{ modelProfileLoadError }}</p>

        <div class="actions">
          <button type="button" :disabled="modelProfileDefaultSubmitting" @click="$emit('set-default-model-profile', '')">
            清空默认
          </button>
        </div>

        <form class="project-form" @submit.prevent="submitModelProfile">
          <p class="section-kicker">{{ profileForm.id ? "编辑模型 Profile" : "新建模型 Profile" }}</p>
          <label>
            名称
            <input v-model.trim="profileForm.name" name="name" placeholder="例如：DeepSeek 默认" />
          </label>
          <label>
            模型提供商
            <select v-model="profileForm.provider" name="provider">
              <option value="api">DeepSeek / OpenAI-compatible API</option>
              <option value="ollama">Ollama 本地模式</option>
            </select>
          </label>
          <label>
            API 地址
            <input v-model.trim="profileForm.apiBase" name="api_base" placeholder="例如：https://api.deepseek.com/v1" />
          </label>
          <label>
            模型名称
            <input v-model.trim="profileForm.model" name="model" placeholder="例如：deepseek-chat" />
          </label>
          <label>
            温度
            <input v-model.number="profileForm.temperature" name="temperature" type="number" min="0" max="2" step="0.1" />
          </label>
          <label>
            最大输出 tokens
            <input v-model.number="profileForm.maxTokens" name="max_tokens" type="number" min="1" />
          </label>
          <label>
            API Key 引用
            <select v-model="profileForm.apiKeyRef" name="api_key_ref">
              <option value="">不使用 Key</option>
              <option value="env:RAG_LLM_API_KEY">环境变量 RAG_LLM_API_KEY</option>
              <option value="env:DEEPSEEK_API_KEY">环境变量 DEEPSEEK_API_KEY</option>
              <option value="saved:RAG_LLM_API_KEY">已保存的 RAG_LLM_API_KEY</option>
            </select>
          </label>
          <p class="muted-line">Profile 只保存 Key 引用，不保存或回显 API Key 明文。</p>
          <div class="actions">
            <button type="submit" :disabled="modelProfileSubmitting">
              {{ modelProfileSubmitting ? "保存中..." : "保存 Profile" }}
            </button>
            <button type="button" @click="resetProfileForm">取消编辑</button>
          </div>
        </form>
      </section>
    </div>
  </section>
</template>

<script setup>
import { computed, reactive, watch } from "vue";

const props = defineProps({
  llmSettings: {
    type: Object,
    default: () => ({}),
  },
  llmSettingsLoading: {
    type: Boolean,
    default: false,
  },
  llmSettingsSubmitting: {
    type: Boolean,
    default: false,
  },
  llmSettingsTesting: {
    type: Boolean,
    default: false,
  },
  llmSettingsError: {
    type: String,
    default: "",
  },
  llmSettingsStatus: {
    type: String,
    default: "",
  },
  modelProfiles: {
    type: Array,
    default: () => [],
  },
  defaultModelProfileId: {
    type: String,
    default: "",
  },
  modelProfilesLoading: {
    type: Boolean,
    default: false,
  },
  modelProfileLoadError: {
    type: String,
    default: "",
  },
  modelProfileSubmitting: {
    type: Boolean,
    default: false,
  },
  modelProfileTestingId: {
    type: String,
    default: "",
  },
  modelProfileDeletingId: {
    type: String,
    default: "",
  },
  modelProfileDefaultSubmitting: {
    type: Boolean,
    default: false,
  },
  modelProfileMutationError: {
    type: String,
    default: "",
  },
  modelProfileStatus: {
    type: String,
    default: "",
  },
});

const emit = defineEmits(["load-settings", "save-llm-settings", "test-llm-settings", "load-model-profiles", "save-model-profile", "delete-model-profile", "set-default-model-profile", "test-model-profile"]);

const llmForm = reactive({
  provider: "api",
  apiBase: "",
  model: "",
  apiKey: "",
});

const profileForm = reactive({
  id: "",
  name: "",
  provider: "api",
  apiBase: "",
  model: "",
  temperature: 0.7,
  maxTokens: 2048,
  apiKeyRef: "",
});

watch(
  () => props.llmSettings,
  (settings) => {
    llmForm.provider = settings?.provider || "api";
    llmForm.apiBase = settings?.api_base || "";
    llmForm.model = settings?.model || "";
    llmForm.apiKey = "";
  },
  { immediate: true },
);

const llmSettingsSummary = computed(() => {
  if (props.llmSettingsLoading) {
    return "正在读取模型设置...";
  }
  if (!props.llmSettings || Object.keys(props.llmSettings).length === 0) {
    return "尚未读取模型设置";
  }
  const keyStatus = props.llmSettings.has_api_key ? `Key：${props.llmSettings.api_key_source || "已配置"}` : "Key：未配置";
  return `${props.llmSettings.provider || "api"} / ${props.llmSettings.model || "未填写模型"}；${keyStatus}`;
});

const defaultModelProfileLabel = computed(() => {
  if (!props.defaultModelProfileId) {
    return "未选择";
  }
  const profile = props.modelProfiles.find((entry) => entry.id === props.defaultModelProfileId);
  return profile?.name || props.defaultModelProfileId;
});

function submitLlmSettings() {
  emit("save-llm-settings", { ...llmForm });
}

function editProfile(profile) {
  profileForm.id = profile.id || "";
  profileForm.name = profile.name || "";
  profileForm.provider = profile.provider || "api";
  profileForm.apiBase = profile.api_base || "";
  profileForm.model = profile.model || "";
  profileForm.temperature = profile.temperature ?? 0.7;
  profileForm.maxTokens = profile.max_tokens ?? 2048;
  profileForm.apiKeyRef = profile.api_key_ref || "";
}

function resetProfileForm() {
  profileForm.id = "";
  profileForm.name = "";
  profileForm.provider = "api";
  profileForm.apiBase = "";
  profileForm.model = "";
  profileForm.temperature = 0.7;
  profileForm.maxTokens = 2048;
  profileForm.apiKeyRef = "";
}

function submitModelProfile() {
  emit("save-model-profile", { ...profileForm });
}
</script>

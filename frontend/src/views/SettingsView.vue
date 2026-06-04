<template>
  <div class="page full">
    <div class="settings-frame">
    <header class="section">
      <div>
        <p class="section-kicker">设置</p>
        <h2>设置</h2>
        <p>管理模型连接、常用 Profile 和项目 Prompt 预设。</p>
      </div>
      <button type="button" :disabled="llmSettingsLoading || modelProfilesLoading || promptPresetsLoading" @click="$emit('load-settings')">
        {{ llmSettingsLoading || modelProfilesLoading || promptPresetsLoading ? "刷新中..." : "刷新设置" }}
      </button>
    </header>

    <div class="settings-grid">
      <section class="section settings-panel">
        <div class="section-title-row">
          <div>
            <p class="section-kicker">模型设置</p>
            <h3>基础 LLM 连接</h3>
          </div>
          <button type="button" :disabled="llmSettingsTesting" @click="$emit('test-llm-settings')">
            {{ llmSettingsTesting ? "测试中..." : "测试连接" }}
          </button>
        </div>

        <form class="field-grid" @submit.prevent="submitLlmSettings">
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
            <button type="submit" class="btn-ink" :disabled="llmSettingsSubmitting">
              {{ llmSettingsSubmitting ? "保存中..." : "保存模型设置" }}
            </button>
          </div>
        </form>
      </section>

      <section class="section settings-panel">
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

      <section class="section settings-panel">
        <div class="section-title-row">
          <div>
            <p class="section-kicker">Prompt 预设</p>
            <h3>项目回答风格</h3>
          </div>
          <button type="button" :disabled="promptPresetsLoading" @click="$emit('load-prompt-presets')">
            {{ promptPresetsLoading ? "刷新中..." : "刷新预设" }}
          </button>
        </div>

        <p class="status-line">当前默认 Prompt：{{ defaultPromptPresetLabel }}</p>
        <p v-if="promptPresetMutationError" class="status-line error">{{ promptPresetMutationError }}</p>
        <p v-if="promptPresetLoadError" class="status-line error">{{ promptPresetLoadError }}</p>
        <p class="status-line">{{ promptPresetStatus || promptPresetEmptyMessage }}</p>

        <ul class="model-profile-list">
          <li v-for="preset in promptPresets" :key="preset.id">
            <div>
              <strong>{{ preset.id === selectedPromptPresetId ? `${preset.name}（默认）` : preset.name }}</strong>
              <small>{{ preset.description || "无说明" }}</small>
            </div>
            <div class="actions compact-actions">
              <button type="button" @click="editPromptPreset(preset)">编辑</button>
              <button
                type="button"
                :disabled="promptPresetDefaultSubmitting"
                @click="$emit('set-default-prompt-preset', preset.id)"
              >
                {{ preset.id === selectedPromptPresetId ? "默认" : "设为默认" }}
              </button>
              <button
                class="danger-link"
                type="button"
                :disabled="promptPresetDeletingId === preset.id"
                @click="$emit('delete-prompt-preset', preset.id)"
              >
                {{ promptPresetDeletingId === preset.id ? "删除中..." : "删除预设" }}
              </button>
            </div>
          </li>
        </ul>

        <div class="actions">
          <button
            type="button"
            :disabled="promptPresetDefaultSubmitting || !selectedProjectId"
            @click="$emit('set-default-prompt-preset', '')"
          >
            清空默认 Prompt
          </button>
        </div>

        <form class="project-form" @submit.prevent="submitPromptPreset">
          <p class="section-kicker">{{ promptPresetForm.id ? "编辑 Prompt 预设" : "新建 Prompt 预设" }}</p>
          <label>
            名称
            <input v-model.trim="promptPresetForm.name" name="prompt_name" placeholder="例如：项目问答" :disabled="promptPresetSubmitting || !selectedProjectId" />
          </label>
          <label>
            说明
            <input
              v-model.trim="promptPresetForm.description"
              name="prompt_description"
              placeholder="用于回答项目资料问题"
              :disabled="promptPresetSubmitting || !selectedProjectId"
            />
          </label>
          <label>
            系统提示词
            <textarea
              v-model.trim="promptPresetForm.systemPrompt"
              name="system_prompt"
              placeholder="只基于来源片段回答，资料不足时说明缺口"
              :disabled="promptPresetSubmitting || !selectedProjectId"
            ></textarea>
          </label>
          <label>
            回答格式
            <textarea
              v-model.trim="promptPresetForm.answerFormat"
              name="answer_format"
              placeholder="先结论，再列依据来源"
              :disabled="promptPresetSubmitting || !selectedProjectId"
            ></textarea>
          </label>
          <div class="actions">
            <button type="submit" :disabled="promptPresetSubmitting || !selectedProjectId">
              {{ promptPresetSubmitting ? "保存中..." : "保存预设" }}
            </button>
            <button type="button" @click="resetPromptPresetForm">取消编辑</button>
          </div>
        </form>

        <p class="section-kicker">内置模板</p>
        <ul class="model-profile-list">
          <li v-for="template in promptPresetTemplates" :key="template.name">
            <div>
              <strong>{{ template.name }}</strong>
              <small>{{ template.description || "无说明" }}</small>
            </div>
            <div class="actions compact-actions">
              <button type="button" :disabled="!selectedProjectId" @click="copyPromptPresetTemplate(template)">复制模板</button>
            </div>
          </li>
        </ul>
      </section>
    </div>
    </div>
  </div>
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
  selectedProjectId: {
    type: String,
    default: "",
  },
  promptPresets: {
    type: Array,
    default: () => [],
  },
  promptPresetTemplates: {
    type: Array,
    default: () => [],
  },
  selectedPromptPresetId: {
    type: String,
    default: "",
  },
  promptPresetsLoading: {
    type: Boolean,
    default: false,
  },
  promptPresetLoadError: {
    type: String,
    default: "",
  },
  promptPresetSubmitting: {
    type: Boolean,
    default: false,
  },
  promptPresetDeletingId: {
    type: String,
    default: "",
  },
  promptPresetDefaultSubmitting: {
    type: Boolean,
    default: false,
  },
  promptPresetMutationError: {
    type: String,
    default: "",
  },
  promptPresetStatus: {
    type: String,
    default: "",
  },
});

const emit = defineEmits(["load-settings", "save-llm-settings", "test-llm-settings", "load-model-profiles", "save-model-profile", "delete-model-profile", "set-default-model-profile", "test-model-profile", "load-prompt-presets", "save-prompt-preset", "delete-prompt-preset", "set-default-prompt-preset"]);

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

const promptPresetForm = reactive({
  id: "",
  name: "",
  description: "",
  systemPrompt: "",
  answerFormat: "",
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

watch(
  () => props.selectedProjectId,
  () => {
    resetPromptPresetForm();
  },
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

const defaultPromptPresetLabel = computed(() => {
  if (!props.selectedPromptPresetId) {
    return "未选择";
  }
  const preset = props.promptPresets.find((entry) => entry.id === props.selectedPromptPresetId);
  return preset?.name || props.selectedPromptPresetId;
});

const promptPresetEmptyMessage = computed(() => {
  if (!props.selectedProjectId) {
    return "请选择项目空间后管理 Prompt 预设。";
  }
  if (props.promptPresetsLoading) {
    return "正在读取 Prompt 预设...";
  }
  if (props.promptPresets.length === 0) {
    return "暂无 Prompt 预设，可从模板复制后保存。";
  }
  return "";
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

function editPromptPreset(preset) {
  promptPresetForm.id = preset.id || "";
  promptPresetForm.name = preset.name || "";
  promptPresetForm.description = preset.description || "";
  promptPresetForm.systemPrompt = preset.system_prompt || "";
  promptPresetForm.answerFormat = preset.answer_format || "";
}

function copyPromptPresetTemplate(template) {
  promptPresetForm.id = "";
  promptPresetForm.name = template.name || "";
  promptPresetForm.description = template.description || "";
  promptPresetForm.systemPrompt = template.system_prompt || "";
  promptPresetForm.answerFormat = template.answer_format || "";
}

function resetPromptPresetForm() {
  promptPresetForm.id = "";
  promptPresetForm.name = "";
  promptPresetForm.description = "";
  promptPresetForm.systemPrompt = "";
  promptPresetForm.answerFormat = "";
}

function submitPromptPreset() {
  emit("save-prompt-preset", {
    ...promptPresetForm,
    projectId: props.selectedProjectId,
  });
}
</script>

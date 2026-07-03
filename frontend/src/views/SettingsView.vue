<template>
  <section class="settings-fullscreen" aria-labelledby="settings-title">
    <header class="settings-topbar">
      <button type="button" class="ghost-button" data-settings-action="back" @click="emit('back')">
        返回
      </button>
      <div>
        <p class="section-kicker">设</p>
        <h2 id="settings-title">设置</h2>
      </div>
      <button type="button" :disabled="isRefreshing" @click="emit('load-settings')">
        {{ isRefreshing ? "刷新中..." : "刷新" }}
      </button>
    </header>

    <div class="settings-page-layout">
      <aside class="settings-menu" aria-label="设置菜单">
        <button
          type="button"
          :class="{ active: settingsPage === 'answer' }"
          data-settings-page="answer"
          @click="emit('change-settings-page', 'answer')"
        >
          回答
        </button>
        <button
          type="button"
          :class="{ active: settingsPage === 'data' }"
          data-settings-page="data"
          @click="emit('change-settings-page', 'data')"
        >
          资料
        </button>
        <button
          type="button"
          :class="{ active: settingsPage === 'appearance' }"
          data-settings-page="appearance"
          @click="emit('change-settings-page', 'appearance')"
        >
          外观
        </button>
      </aside>

      <section v-if="settingsPage === 'data'" class="settings-page-panel">
        <div class="section-title-row">
          <div>
            <p class="section-kicker">资料</p>
            <h3>资料保存位置</h3>
          </div>
        </div>
        <div class="settings-option-list">
          <article class="settings-option-card">
            <strong>本地资料</strong>
            <p>资料保存在当前本机工作区。第一版沿用现有项目资料位置。</p>
            <button type="button" disabled>选择位置</button>
          </article>
          <article class="settings-option-card">
            <strong>备份</strong>
            <p>备份恢复需要后续接口支持，当前不会伪装成功。</p>
            <button type="button" disabled>备份不可用</button>
          </article>
          <article class="settings-option-card">
            <strong>恢复</strong>
            <p>恢复资料前需要完整导入和校验能力，后续单独接入。</p>
            <button type="button" disabled>恢复不可用</button>
          </article>
        </div>
      </section>

      <section v-else-if="settingsPage === 'appearance'" class="settings-page-panel">
        <div class="section-title-row">
          <div>
            <p class="section-kicker">外观</p>
            <h3>显示偏好</h3>
          </div>
        </div>
        <div class="settings-option-list">
          <article class="settings-option-card">
            <strong>深色模式</strong>
            <p>第一版先保留入口，具体主题切换后续接入。</p>
            <label class="toggle-row">
              <input type="checkbox" disabled />
              暂未开启
            </label>
          </article>
          <article class="settings-option-card">
            <strong>回答方式</strong>
            <p>聊天框中也可临时切换回答方式。</p>
            <select>
              <option>标准</option>
              <option>更快</option>
              <option>更细</option>
            </select>
          </article>
        </div>
      </section>

      <section v-else class="settings-page-panel">
        <div class="section-title-row">
          <div>
            <p class="section-kicker">回答</p>
            <h3>回答方式</h3>
          </div>
          <button type="button" :disabled="llmSettingsTesting" @click="emit('test-llm-settings')">
            {{ llmSettingsTesting ? "测试中..." : "测试连接" }}
          </button>
        </div>

        <div class="settings-option-list">
          <article class="settings-option-card">
            <strong>本机回答</strong>
            <p>优先使用本机开源模型，适合离线资料整理。</p>
            <button type="button" @click="setLocalAnswer">使用本机回答</button>
          </article>
          <article class="settings-option-card">
            <strong>本机快速</strong>
            <p>{{ defaultModelProfileLabel === "未选择" ? "可在连接详情中选择常用模型。" : defaultModelProfileLabel }}</p>
            <button type="button" :disabled="modelProfilesLoading" @click="emit('load-model-profiles')">
              {{ modelProfilesLoading ? "刷新中..." : "刷新模型" }}
            </button>
          </article>
          <article class="settings-option-card">
            <strong>在线回答</strong>
            <p>{{ llmSettingsSummary }}</p>
            <button type="button" @click="setOnlineAnswer">使用在线回答</button>
          </article>
        </div>

        <div class="settings-detail-block">
          <button
            type="button"
            class="ghost-button"
            data-settings-action="connection-details"
            @click="connectionDetailsOpen = !connectionDetailsOpen"
          >
            连接详情
          </button>

          <div v-if="connectionDetailsOpen" class="settings-detail-grid">
            <form class="project-form" @submit.prevent="submitLlmSettings">
              <p class="section-kicker">在线连接</p>
              <label>
                服务地址
                <input
                  v-model.trim="llmForm.apiBase"
                  name="api_base"
                  placeholder="例如：https://api.example.com/v1"
                  :disabled="llmSettingsSubmitting"
                />
              </label>
              <label>
                模型名
                <input
                  v-model.trim="llmForm.model"
                  name="model"
                  placeholder="例如：deepseek-chat"
                  :disabled="llmSettingsSubmitting"
                />
              </label>
              <label>
                Key 引用
                <input
                  v-model="llmForm.apiKey"
                  name="api_key"
                  type="password"
                  autocomplete="off"
                  placeholder="留空不覆盖已有 Key"
                  :disabled="llmSettingsSubmitting"
                />
              </label>
              <p class="muted-line">只保存引用，不回显明文；留空不覆盖已有 Key。</p>
              <p v-if="llmSettingsError" class="status-line error">{{ llmSettingsError }}</p>
              <p class="status-line">{{ llmSettingsStatus || llmSettingsSummary }}</p>
              <div class="actions">
                <button type="submit" :disabled="llmSettingsSubmitting">
                  {{ llmSettingsSubmitting ? "保存中..." : "保存连接" }}
                </button>
              </div>
            </form>

            <section class="settings-subsection">
              <div class="section-title-row">
                <div>
                  <p class="section-kicker">常用回答</p>
                  <h4>模型列表</h4>
                </div>
                <button type="button" :disabled="modelProfilesLoading" @click="emit('load-model-profiles')">
                  {{ modelProfilesLoading ? "刷新中..." : "刷新" }}
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
                  </div>
                  <div class="actions compact-actions">
                    <button type="button" @click="editProfile(profile)">编辑</button>
                    <button type="button" :disabled="modelProfileDefaultSubmitting" @click="emit('set-default-model-profile', profile.id)">
                      {{ profile.id === defaultModelProfileId ? "默认" : "设为默认" }}
                    </button>
                    <button type="button" :disabled="modelProfileTestingId === profile.id" @click="emit('test-model-profile', profile.id)">
                      {{ modelProfileTestingId === profile.id ? "测试中..." : "测试" }}
                    </button>
                    <button class="danger-link" type="button" :disabled="modelProfileDeletingId === profile.id" @click="emit('delete-model-profile', profile.id)">
                      {{ modelProfileDeletingId === profile.id ? "删除中..." : "删除" }}
                    </button>
                  </div>
                </li>
              </ul>
              <p v-if="modelProfiles.length === 0" class="status-line">暂无常用回答配置。</p>
              <p v-if="modelProfileLoadError" class="status-line error">{{ modelProfileLoadError }}</p>

              <form class="project-form" @submit.prevent="submitModelProfile">
                <p class="section-kicker">{{ profileForm.id ? "编辑常用回答" : "新建常用回答" }}</p>
                <label>
                  名称
                  <input v-model.trim="profileForm.name" name="name" placeholder="例如：本机快速" />
                </label>
                <label>
                  服务地址
                  <input v-model.trim="profileForm.apiBase" name="api_base" placeholder="本机可留空" />
                </label>
                <label>
                  模型名
                  <input v-model.trim="profileForm.model" name="model" placeholder="例如：qwen2.5:7b" />
                </label>
                <label>
                  Key 引用
                  <select v-model="profileForm.apiKeyRef" name="api_key_ref">
                    <option value="">不使用 Key</option>
                    <option value="env:RAG_LLM_API_KEY">环境变量 RAG_LLM_API_KEY</option>
                    <option value="env:DEEPSEEK_API_KEY">环境变量 DEEPSEEK_API_KEY</option>
                    <option value="saved:RAG_LLM_API_KEY">已保存的 RAG_LLM_API_KEY</option>
                  </select>
                </label>
                <div class="actions">
                  <button type="submit" :disabled="modelProfileSubmitting">
                    {{ modelProfileSubmitting ? "保存中..." : "保存" }}
                  </button>
                  <button type="button" @click="resetProfileForm">取消编辑</button>
                </div>
              </form>
            </section>

            <section class="settings-subsection">
              <div class="section-title-row">
                <div>
                  <p class="section-kicker">回答提示</p>
                  <h4>回答模板</h4>
                </div>
                <button type="button" :disabled="promptPresetsLoading" @click="emit('load-prompt-presets')">
                  {{ promptPresetsLoading ? "刷新中..." : "刷新" }}
                </button>
              </div>
              <p class="status-line">当前默认：{{ defaultPromptPresetLabel }}</p>
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
                    <button type="button" :disabled="promptPresetDefaultSubmitting" @click="emit('set-default-prompt-preset', preset.id)">
                      {{ preset.id === selectedPromptPresetId ? "默认" : "设为默认" }}
                    </button>
                    <button class="danger-link" type="button" :disabled="promptPresetDeletingId === preset.id" @click="emit('delete-prompt-preset', preset.id)">
                      {{ promptPresetDeletingId === preset.id ? "删除中..." : "删除" }}
                    </button>
                  </div>
                </li>
              </ul>
              <form class="project-form" @submit.prevent="submitPromptPreset">
                <p class="section-kicker">{{ promptPresetForm.id ? "编辑回答模板" : "新建回答模板" }}</p>
                <label>
                  名称
                  <input v-model.trim="promptPresetForm.name" name="prompt_name" placeholder="例如：资料问答" :disabled="promptPresetSubmitting || !selectedProjectId" />
                </label>
                <label>
                  说明
                  <input v-model.trim="promptPresetForm.description" name="prompt_description" placeholder="用于回答资料问题" :disabled="promptPresetSubmitting || !selectedProjectId" />
                </label>
                <label>
                  系统提示词
                  <textarea v-model.trim="promptPresetForm.systemPrompt" name="system_prompt" placeholder="只根据资料回答" :disabled="promptPresetSubmitting || !selectedProjectId"></textarea>
                </label>
                <label>
                  回答格式
                  <textarea v-model.trim="promptPresetForm.answerFormat" name="answer_format" placeholder="先结论，再列依据来源" :disabled="promptPresetSubmitting || !selectedProjectId"></textarea>
                </label>
                <div class="actions">
                  <button type="submit" :disabled="promptPresetSubmitting || !selectedProjectId">
                    {{ promptPresetSubmitting ? "保存中..." : "保存模板" }}
                  </button>
                  <button type="button" @click="resetPromptPresetForm">取消编辑</button>
                </div>
              </form>
            </section>
          </div>
        </div>
      </section>
    </div>
  </section>
</template>

<script setup>
import { computed, reactive, ref, watch } from "vue";

const props = defineProps({
  settingsPage: {
    type: String,
    default: "answer",
  },
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

const emit = defineEmits(["back", "change-settings-page", "load-settings", "save-llm-settings", "test-llm-settings", "load-model-profiles", "save-model-profile", "delete-model-profile", "set-default-model-profile", "test-model-profile", "load-prompt-presets", "save-prompt-preset", "delete-prompt-preset", "set-default-prompt-preset"]);

const connectionDetailsOpen = ref(false);

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

const isRefreshing = computed(() => {
  return props.llmSettingsLoading || props.modelProfilesLoading || props.promptPresetsLoading;
});

const llmSettingsSummary = computed(() => {
  if (props.llmSettingsLoading) {
    return "正在读取回答设置...";
  }
  if (!props.llmSettings || Object.keys(props.llmSettings).length === 0) {
    return "尚未读取回答设置";
  }
  const keyStatus = props.llmSettings.has_api_key ? `Key：${props.llmSettings.api_key_source || "已配置"}` : "Key：未配置";
  return `${props.llmSettings.model || "未填写模型"}；${keyStatus}`;
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
    return "请选择工作区后管理回答模板。";
  }
  if (props.promptPresetsLoading) {
    return "正在读取回答模板...";
  }
  if (props.promptPresets.length === 0) {
    return "暂无回答模板，可从模板复制后保存。";
  }
  return "";
});

function setLocalAnswer() {
  llmForm.provider = "ollama";
  emit("save-llm-settings", { ...llmForm });
}

function setOnlineAnswer() {
  llmForm.provider = "api";
  emit("save-llm-settings", { ...llmForm });
}

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

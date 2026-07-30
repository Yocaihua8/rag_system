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
          :class="{ active: settingsPage === 'obsidian' }"
          data-settings-page="obsidian"
          @click="emit('change-settings-page', 'obsidian')"
        >
          Obsidian
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

      <section v-else-if="settingsPage === 'obsidian'" class="settings-page-panel" data-obsidian-settings>
        <div class="section-title-row">
          <div>
            <p class="section-kicker">Obsidian</p>
            <h3>桌面插件连接</h3>
          </div>
          <button
            type="button"
            :disabled="obsidianConnectionsLoading || !selectedProjectId"
            @click="emit('load-obsidian-connections')"
          >
            {{ obsidianConnectionsLoading ? "刷新中..." : "刷新连接" }}
          </button>
        </div>

        <p class="status-line">
          每个项目最多保留一个活动连接。插件只同步当前 Vault，并且写回前仍需在学习计划页预览和确认。
        </p>
        <p v-if="!selectedProjectId" class="status-line">请先选择项目后管理 Obsidian 连接。</p>
        <p v-if="obsidianConnectionError" class="status-line error">{{ obsidianConnectionError }}</p>

        <ul v-if="obsidianConnections.length" class="obsidian-connection-list">
          <li
            v-for="connection in obsidianConnections"
            :key="connection.id"
            :data-obsidian-connection-id="connection.id"
          >
            <div class="obsidian-connection-heading">
              <div>
                <strong>{{ connection.vault_name || "未命名 Vault" }}</strong>
                <small>{{ obsidianConnectionStatusLabel(connection.status) }}</small>
              </div>
              <span :class="['obsidian-status-badge', connection.sync_status]">
                {{ obsidianSyncStatusLabel(connection.sync_status) }}
              </span>
            </div>
            <dl class="obsidian-connection-details">
              <div>
                <dt>输出目录</dt>
                <dd>{{ connection.output_root || "未设置" }}</dd>
              </div>
              <div>
                <dt>最近同步</dt>
                <dd>{{ formatObsidianTimestamp(connection.last_synced_at) }}</dd>
              </div>
              <div>
                <dt>连接时间</dt>
                <dd>{{ formatObsidianTimestamp(connection.created_at) }}</dd>
              </div>
            </dl>
            <div v-if="connection.status === 'active'" class="actions compact-actions">
              <button
                type="button"
                class="danger-link"
                :disabled="obsidianRevokingId === connection.id"
                @click="revokeObsidianConnection(connection)"
              >
                {{ obsidianRevokingId === connection.id ? "撤销中..." : "撤销连接" }}
              </button>
            </div>
            <p v-else-if="connection.revoked_at" class="status-line">
              撤销时间：{{ formatObsidianTimestamp(connection.revoked_at) }}
            </p>
          </li>
        </ul>
        <p
          v-else-if="selectedProjectId && !obsidianConnectionsLoading && !obsidianConnectionError"
          class="status-line"
        >
          当前项目尚未连接 Obsidian。
        </p>

        <section class="settings-subsection obsidian-pairing-section">
          <div>
            <p class="section-kicker">受控配对</p>
            <h4>生成一次性配对码</h4>
          </div>
          <p class="status-line">
            配对码仅在短时间内有效。请在 Obsidian 桌面插件中输入；服务端不会向本页返回或回显连接令牌。
          </p>
          <form class="project-form" data-obsidian-pairing-form @submit.prevent="submitObsidianPairing">
            <label>
              发布输出目录（可选）
              <input
                v-model.trim="obsidianPairingForm.outputRoot"
                name="obsidian_output_root"
                placeholder="默认：Knowledge Island/项目名"
                :disabled="obsidianPairingLoading || Boolean(activeObsidianConnection)"
              />
            </label>
            <div class="actions">
              <button
                type="submit"
                :disabled="!selectedProjectId || obsidianPairingLoading || Boolean(activeObsidianConnection)"
              >
                {{ obsidianPairingLoading ? "生成中..." : "生成配对码" }}
              </button>
            </div>
          </form>
          <p v-if="activeObsidianConnection" class="status-line">
            当前项目已有活动连接，撤销后才能生成新的配对码。
          </p>
          <p v-if="obsidianPairingError" class="status-line error">{{ obsidianPairingError }}</p>

          <article v-if="pairingDetails?.code" class="obsidian-pairing-result" data-obsidian-pairing-result>
            <span>一次性配对码</span>
            <code>{{ pairingDetails.code }}</code>
            <dl>
              <div>
                <dt>输出目录</dt>
                <dd>{{ pairingDetails.output_root || "使用项目默认目录" }}</dd>
              </div>
              <div>
                <dt>过期时间</dt>
                <dd>{{ formatObsidianTimestamp(pairingDetails.expires_at) }}</dd>
              </div>
              <div v-if="pairingDetails.ttl_seconds">
                <dt>有效时长</dt>
                <dd>{{ pairingDetails.ttl_seconds }} 秒</dd>
              </div>
            </dl>
            <p>请立即复制到 Obsidian 插件完成配对；过期后需重新生成。</p>
          </article>
        </section>
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
  obsidianConnections: {
    type: Array,
    default: () => [],
  },
  obsidianConnectionsLoading: {
    type: Boolean,
    default: false,
  },
  obsidianConnectionError: {
    type: String,
    default: "",
  },
  obsidianPairing: {
    type: Object,
    default: null,
  },
  obsidianPairingLoading: {
    type: Boolean,
    default: false,
  },
  obsidianPairingError: {
    type: String,
    default: "",
  },
  obsidianRevokingId: {
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

const emit = defineEmits([
  "back",
  "change-settings-page",
  "load-settings",
  "save-llm-settings",
  "test-llm-settings",
  "load-model-profiles",
  "save-model-profile",
  "delete-model-profile",
  "set-default-model-profile",
  "test-model-profile",
  "load-prompt-presets",
  "save-prompt-preset",
  "delete-prompt-preset",
  "set-default-prompt-preset",
  "load-obsidian-connections",
  "start-obsidian-pairing",
  "revoke-obsidian-connection",
]);

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

const obsidianPairingForm = reactive({
  outputRoot: "",
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
    obsidianPairingForm.outputRoot = "";
  },
);

const isRefreshing = computed(() => {
  return (
    props.llmSettingsLoading
    || props.modelProfilesLoading
    || props.promptPresetsLoading
    || props.obsidianConnectionsLoading
  );
});

const activeObsidianConnection = computed(() => (
  props.obsidianConnections.find((connection) => connection.status === "active") || null
));

const pairingDetails = computed(() => (
  props.obsidianPairing?.pairing || props.obsidianPairing || null
));

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

function submitObsidianPairing() {
  if (!props.selectedProjectId || activeObsidianConnection.value) {
    return;
  }
  emit("start-obsidian-pairing", {
    projectId: props.selectedProjectId,
    outputRoot: obsidianPairingForm.outputRoot,
  });
}

function revokeObsidianConnection(connection) {
  if (!props.selectedProjectId || !connection?.id) {
    return;
  }
  emit("revoke-obsidian-connection", {
    projectId: props.selectedProjectId,
    connectionId: connection.id,
  });
}

function obsidianConnectionStatusLabel(status) {
  return {
    active: "活动连接",
    revoked: "已撤销",
  }[status] || "未知状态";
}

function obsidianSyncStatusLabel(status) {
  return {
    idle: "空闲",
    syncing: "同步中",
    error: "同步异常",
  }[status] || "未知";
}

function formatObsidianTimestamp(value) {
  const timestamp = String(value || "").trim();
  if (!timestamp) {
    return "尚未同步";
  }
  const parsed = new Date(timestamp);
  return Number.isNaN(parsed.getTime()) ? timestamp : parsed.toLocaleString();
}
</script>

<style scoped>
.obsidian-connection-list {
  display: grid;
  gap: 12px;
  list-style: none;
  margin: 0;
  padding: 0;
}

.obsidian-connection-list > li,
.obsidian-pairing-result {
  background: #f6f6f6;
  border: 1px solid #dddddd;
  border-radius: 8px;
  display: grid;
  gap: 12px;
  padding: 14px;
}

.obsidian-connection-heading {
  align-items: flex-start;
  display: flex;
  gap: 12px;
  justify-content: space-between;
}

.obsidian-connection-heading > div {
  display: grid;
  gap: 4px;
}

.obsidian-connection-heading small,
.obsidian-pairing-result > span,
.obsidian-pairing-result p {
  color: #666666;
}

.obsidian-status-badge {
  background: #e5e5e5;
  border-radius: 999px;
  color: #555555;
  flex: none;
  font-size: 12px;
  padding: 4px 8px;
}

.obsidian-status-badge.syncing {
  background: #dbeafe;
  color: #1d4ed8;
}

.obsidian-status-badge.error {
  background: #fee2e2;
  color: #b91c1c;
}

.obsidian-connection-details,
.obsidian-pairing-result dl {
  display: grid;
  gap: 10px;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  margin: 0;
}

.obsidian-connection-details div,
.obsidian-pairing-result dl div {
  min-width: 0;
}

.obsidian-connection-details dt,
.obsidian-pairing-result dt {
  color: #777777;
  font-size: 12px;
}

.obsidian-connection-details dd,
.obsidian-pairing-result dd {
  margin: 4px 0 0;
  overflow-wrap: anywhere;
}

.obsidian-pairing-section {
  border-left: 0;
  border-top: 1px solid #eeeeee;
  padding-left: 0;
  padding-top: 18px;
}

.obsidian-pairing-section h4 {
  margin: 0;
}

.obsidian-pairing-result code {
  background: #111111;
  border-radius: 6px;
  color: #ffffff;
  font-size: 20px;
  letter-spacing: 0.08em;
  overflow-wrap: anywhere;
  padding: 12px;
}

.obsidian-pairing-result p {
  margin: 0;
}

@media (max-width: 760px) {
  .obsidian-connection-details,
  .obsidian-pairing-result dl {
    grid-template-columns: 1fr;
  }
}
</style>

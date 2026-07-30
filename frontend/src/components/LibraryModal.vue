<template>
  <teleport to="body">
    <div v-if="open" class="library-modal-backdrop">
      <section class="library-modal" role="dialog" aria-modal="true" aria-labelledby="library-modal-title">
        <header class="library-modal-header">
          <div>
            <p class="section-kicker">资料库</p>
            <h2 id="library-modal-title">管理资料</h2>
          </div>
          <button type="button" class="ghost-button" aria-label="关闭资料库" @click="emit('close')">关闭</button>
        </header>

        <nav class="library-modal-tabs" aria-label="资料库操作">
          <button
            type="button"
            :class="{ active: step === 'upload' }"
            data-library-action="upload"
            @click="emit('back-to-upload')"
          >
            加入库
          </button>
          <button
            type="button"
            :class="{ active: step === 'select' }"
            data-library-action="choose-material"
            @click="emit('choose-material')"
          >
            选择资料
          </button>
        </nav>

        <section v-if="step === 'select'" class="library-modal-body">
          <div class="library-empty-note">
            <h3>先在左侧选择工作区</h3>
            <p>选好工作区后，再从这里把资料加入当前聊天范围。</p>
          </div>
          <div class="library-list-header">
            <h3>资料夹</h3>
            <button type="button" class="ghost-button" @click="emit('refresh-collections')">刷新</button>
          </div>
          <p v-if="documentCollectionsLoading" class="status-line">正在读取资料夹...</p>
          <p v-else-if="documentCollectionsLoadError" class="status-line error">{{ documentCollectionsLoadError }}</p>
          <div v-else class="library-folder-list" data-library-folder-list>
            <button
              type="button"
              class="library-folder-item"
              :class="{ active: selectedDocumentCollectionId === '' }"
              @click="emit('select-collection', '')"
            >
              全部资料
            </button>
            <button
              type="button"
              class="library-folder-item"
              :class="{ active: selectedDocumentCollectionId === 'unassigned' }"
              @click="emit('select-collection', 'unassigned')"
            >
              未分组
            </button>
            <button
              v-for="collection in documentCollections"
              :key="collection.id"
              type="button"
              class="library-folder-item"
              :class="{ active: selectedDocumentCollectionId === collection.id }"
              @click="emit('select-collection', collection.id)"
            >
              <span>{{ collection.name }}</span>
              <small>{{ collection.document_count ?? 0 }}</small>
            </button>
          </div>
          <div class="library-list-header">
            <h3>已加入库的资料</h3>
            <button type="button" class="ghost-button" @click="emit('refresh-documents')">刷新</button>
          </div>
          <p v-if="documentsLoading" class="status-line">正在读取资料...</p>
          <p v-else-if="documentsLoadError" class="status-line error">{{ documentsLoadError }}</p>
          <div v-else-if="documents.length" class="library-document-list">
            <button
              v-for="document in documents"
              :key="document.id"
              type="button"
              class="library-document-item"
              @click="emit('select-document', document.id)"
            >
              <span>{{ document.title || document.filename || '未命名资料' }}</span>
              <small>{{ document.collection_name || '未分组' }}</small>
            </button>
          </div>
          <p v-else class="status-line">还没有资料。先用“加入库”上传文件、文件夹、笔记或网页。</p>
        </section>

        <section v-else class="library-modal-body">
          <div class="library-import-grid">
            <label class="library-import-card">
              <strong>文件</strong>
              <span>一次选择多个文件</span>
              <input type="file" multiple @change="handleFileInput" />
            </label>
            <label class="library-import-card">
              <strong>文件夹</strong>
              <span>一次加入整个文件夹</span>
              <input type="file" multiple webkitdirectory @change="handleFolderInput" />
            </label>
            <form class="library-import-card" @submit.prevent="submitNote">
              <strong>笔记</strong>
              <textarea v-model="noteText" rows="4" placeholder="粘贴一段笔记"></textarea>
              <button type="submit" :disabled="!noteText.trim()">加入</button>
            </form>
            <form class="library-import-card" @submit.prevent="submitUrl">
              <strong>网页摘录</strong>
              <input v-model="urlText" type="url" placeholder="https://example.com" />
              <button type="submit" :disabled="!urlText.trim()">加入</button>
            </form>
            <button
              type="button"
              class="library-import-card library-import-card-button"
              data-library-source="more"
              @click="advancedSourcesOpen = !advancedSourcesOpen"
            >
              <strong>更多来源</strong>
              <span>代码仓库、笔记库等收在这里</span>
            </button>
          </div>
          <section v-if="advancedSourcesOpen" class="library-advanced-sources" data-library-advanced-sources>
            <form class="library-import-card wide" @submit.prevent="submitRepo">
              <strong>GitHub 仓库</strong>
              <span>输入仓库地址后导入仓库资料。导入完成后按结果选择工作区。</span>
              <input v-model="repoUrl" type="url" placeholder="https://github.com/example/repo" />
              <button type="submit" :disabled="!repoUrl.trim()">加入</button>
            </form>
            <article class="library-import-card library-import-card-disabled">
              <strong>Notion</strong>
              <span>稍后支持。当前请先导出为文件后加入库。</span>
            </article>
            <article class="library-import-card library-obsidian-card" data-library-obsidian>
              <div class="library-obsidian-heading">
                <div>
                  <strong>Obsidian 桌面插件</strong>
                  <span>持续同步当前项目笔记，并在确认后接收 Knowledge Island 发布内容。</span>
                </div>
                <span :class="['library-connection-badge', { active: activeObsidianConnection }]">
                  {{ activeObsidianConnection ? "已连接" : "未连接" }}
                </span>
              </div>

              <p v-if="obsidianConnectionsLoading" class="status-line">正在读取 Obsidian 连接...</p>
              <p v-else-if="obsidianConnectionsError" class="status-line error">
                {{ obsidianConnectionsError }}
              </p>
              <dl v-else-if="activeObsidianConnection" class="library-obsidian-details">
                <div>
                  <dt>Vault</dt>
                  <dd>{{ activeObsidianConnection.vault_name || "未命名 Vault" }}</dd>
                </div>
                <div>
                  <dt>同步状态</dt>
                  <dd>{{ obsidianSyncStatusLabel(activeObsidianConnection.sync_status) }}</dd>
                </div>
                <div>
                  <dt>输出目录</dt>
                  <dd>{{ activeObsidianConnection.output_root || "未设置" }}</dd>
                </div>
                <div>
                  <dt>最近同步</dt>
                  <dd>{{ formatObsidianTimestamp(activeObsidianConnection.last_synced_at) }}</dd>
                </div>
              </dl>
              <p v-else class="status-line">
                当前项目尚未连接 Obsidian。请先到设置页生成一次性配对码，再由桌面插件完成连接。
              </p>

              <div class="library-obsidian-actions">
                <button
                  type="button"
                  class="ghost-button"
                  :disabled="obsidianConnectionsLoading"
                  @click="emit('refresh-obsidian-connections')"
                >
                  {{ obsidianConnectionsLoading ? "刷新中..." : "刷新状态" }}
                </button>
                <button type="button" @click="emit('open-obsidian-settings')">
                  {{ activeObsidianConnection ? "管理连接" : "打开设置并配对" }}
                </button>
              </div>

              <form class="library-obsidian-readonly-import" @submit.prevent="submitObsidianVault">
                <strong>一次性只读导入</strong>
                <span>
                  这是原有的本机 Vault 路径导入，只读取一次，不会建立插件连接，也不会向 Vault 写回。
                </span>
                <input
                  v-model.trim="obsidianVaultPath"
                  name="obsidian_vault_path"
                  placeholder="例如：D:\Notes\My Vault"
                />
                <button type="submit" :disabled="!obsidianVaultPath.trim() || importSubmitting">
                  {{ importSubmitting ? "导入中..." : "只读导入 Vault" }}
                </button>
              </form>
            </article>
          </section>
          <ImportResultList :status="importStatus" :error="importError" />
        </section>
      </section>
    </div>
  </teleport>
</template>

<script setup>
import { computed, ref } from "vue";
import ImportResultList from "./ImportResultList.vue";

const props = defineProps({
  open: {
    type: Boolean,
    default: false,
  },
  step: {
    type: String,
    default: "upload",
  },
  documents: {
    type: Array,
    default: () => [],
  },
  documentsLoading: {
    type: Boolean,
    default: false,
  },
  documentsLoadError: {
    type: String,
    default: "",
  },
  documentCollections: {
    type: Array,
    default: () => [],
  },
  selectedDocumentCollectionId: {
    type: String,
    default: "",
  },
  documentCollectionsLoading: {
    type: Boolean,
    default: false,
  },
  documentCollectionsLoadError: {
    type: String,
    default: "",
  },
  importStatus: {
    type: String,
    default: "",
  },
  importError: {
    type: String,
    default: "",
  },
  importSubmitting: {
    type: Boolean,
    default: false,
  },
  obsidianConnections: {
    type: Array,
    default: () => [],
  },
  obsidianConnectionsLoading: {
    type: Boolean,
    default: false,
  },
  obsidianConnectionsError: {
    type: String,
    default: "",
  },
});

const emit = defineEmits([
  "back-to-upload",
  "choose-material",
  "close",
  "import-files",
  "import-folder",
  "import-github-repo",
  "import-note",
  "import-obsidian-vault",
  "import-url",
  "open-obsidian-settings",
  "refresh-collections",
  "refresh-documents",
  "refresh-obsidian-connections",
  "select-collection",
  "select-document",
]);

const noteText = ref("");
const urlText = ref("");
const repoUrl = ref("");
const obsidianVaultPath = ref("");
const advancedSourcesOpen = ref(false);
const activeObsidianConnection = computed(() => (
  props.obsidianConnections.find((connection) => connection.status === "active") || null
));

function handleFileInput(event) {
  const files = Array.from(event.target.files || []);
  if (files.length) {
    emit("import-files", files);
  }
  event.target.value = "";
}

function handleFolderInput(event) {
  const files = Array.from(event.target.files || []);
  if (files.length) {
    emit("import-folder", files);
  }
  event.target.value = "";
}

function submitNote() {
  const content = noteText.value.trim();
  if (!content) {
    return;
  }
  emit("import-note", { title: "临时笔记", content });
  noteText.value = "";
}

function submitUrl() {
  const url = urlText.value.trim();
  if (!url) {
    return;
  }
  emit("import-url", { url });
  urlText.value = "";
}

function submitRepo() {
  const repositoryUrl = repoUrl.value.trim();
  if (!repositoryUrl) {
    return;
  }
  emit("import-github-repo", { repoUrl: repositoryUrl });
  repoUrl.value = "";
}

function submitObsidianVault() {
  const vaultPath = obsidianVaultPath.value.trim();
  if (!vaultPath) {
    return;
  }
  emit("import-obsidian-vault", { vaultPath });
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
.library-modal-backdrop {
  align-items: stretch;
  background: rgba(17, 17, 17, 0.28);
  display: flex;
  inset: 0;
  justify-content: flex-end;
  padding: 24px;
  position: fixed;
  z-index: 40;
}

.library-modal {
  background: #ffffff;
  border: 1px solid #dddddd;
  border-radius: 8px;
  box-shadow: 0 24px 60px rgba(17, 17, 17, 0.18);
  display: grid;
  grid-template-rows: auto auto minmax(0, 1fr);
  max-width: 760px;
  overflow: hidden;
  width: min(760px, 100%);
}

.library-modal-header,
.library-list-header,
.library-modal-tabs {
  align-items: center;
  display: flex;
  gap: 12px;
  justify-content: space-between;
}

.library-modal-header {
  border-bottom: 1px solid #e6e6e6;
  padding: 18px 20px;
}

.library-modal-tabs {
  justify-content: flex-start;
  padding: 14px 20px 0;
}

.library-modal-tabs button.active {
  background: #eeeeee;
  color: #111111;
}

.library-modal-body {
  display: grid;
  gap: 16px;
  overflow: auto;
  padding: 20px;
}

.library-import-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.library-import-card {
  background: #f6f6f6;
  border: 1px solid #dddddd;
  border-radius: 8px;
  color: #666666;
  display: grid;
  gap: 10px;
  padding: 14px;
}

.library-import-card-button {
  cursor: pointer;
  min-height: 126px;
  text-align: left;
  width: 100%;
}

.library-import-card strong {
  color: #111111;
}

.library-import-card.wide {
  grid-column: 1 / -1;
}

.library-advanced-sources {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.library-advanced-sources .wide {
  grid-column: span 1;
}

.library-import-card-disabled {
  opacity: 0.72;
}

.library-obsidian-card {
  grid-column: 1 / -1;
}

.library-obsidian-heading,
.library-obsidian-actions {
  align-items: center;
  display: flex;
  gap: 12px;
  justify-content: space-between;
}

.library-obsidian-heading > div,
.library-obsidian-readonly-import {
  display: grid;
  gap: 8px;
}

.library-connection-badge {
  background: #e5e5e5;
  border-radius: 999px;
  color: #666666;
  flex: none;
  font-size: 12px;
  padding: 4px 8px;
}

.library-connection-badge.active {
  background: #dcfce7;
  color: #166534;
}

.library-obsidian-details {
  display: grid;
  gap: 8px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  margin: 0;
}

.library-obsidian-details div {
  background: #ffffff;
  border: 1px solid #e2e2e2;
  border-radius: 6px;
  display: grid;
  gap: 4px;
  min-width: 0;
  padding: 10px;
}

.library-obsidian-details dt {
  color: #777777;
  font-size: 12px;
}

.library-obsidian-details dd {
  color: #111111;
  margin: 0;
  overflow-wrap: anywhere;
}

.library-obsidian-readonly-import {
  border-top: 1px solid #dddddd;
  margin-top: 4px;
  padding-top: 14px;
}

.library-document-list,
.library-folder-list {
  display: grid;
  gap: 8px;
}

.library-document-item,
.library-folder-item {
  align-items: center;
  background: #ffffff;
  border: 1px solid #dddddd;
  color: #111111;
  display: flex;
  justify-content: space-between;
  text-align: left;
}

.library-folder-item.active {
  background: #eeeeee;
  border-color: #111111;
}

.library-empty-note {
  background: #f4f4f4;
  border: 1px solid #d6d6d6;
  border-radius: 8px;
  padding: 14px;
}

@media (max-width: 760px) {
  .library-modal-backdrop {
    padding: 10px;
  }

  .library-import-grid {
    grid-template-columns: 1fr;
  }

  .library-advanced-sources {
    grid-template-columns: 1fr;
  }

  .library-obsidian-details {
    grid-template-columns: 1fr;
  }
}
</style>

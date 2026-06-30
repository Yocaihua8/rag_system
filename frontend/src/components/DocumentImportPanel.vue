<template>
  <section class="document-import-panel" aria-labelledby="document-import-title">
    <div class="section-title-row">
      <div>
        <p class="section-kicker">导入资料</p>
        <h2 id="document-import-title">导入资料</h2>
      </div>
    </div>

    <p v-if="!selectedProjectId" class="status-line">未选择项目空间</p>
    <p v-if="importError" class="status-line error">{{ importError }}</p>
    <p v-if="importPreviewError" class="status-line error">{{ importPreviewError }}</p>
    <p v-else-if="importStatus" class="status-line">{{ importStatus }}</p>

    <div class="import-grid">
      <section class="import-form">
        <p class="section-kicker">本地目录</p>
        <h3>同步当前项目目录</h3>
        <p class="muted-line">读取当前项目空间绑定的本机目录，可先导入预检，再同步已有项目。</p>
        <div class="actions">
          <button
            type="button"
            :disabled="importSubmitting || importPreviewLoading || !selectedProjectId"
            @click="$emit('preview-import')"
          >
            {{ importPreviewLoading ? "预检中..." : "预检当前项目目录" }}
          </button>
          <button
            type="button"
            :disabled="importSubmitting || !selectedProjectId"
            @click="$emit('sync-directory')"
          >
            {{ importSubmitting ? "同步中..." : "同步当前项目目录" }}
          </button>
        </div>
        <div v-if="importPreview" class="import-preview" aria-label="预检结果">
          <h4>导入预检结果</h4>
          <p>可导入 {{ importPreview.importable ?? 0 }}，跳过 {{ importPreview.skipped ?? 0 }}</p>
          <ul v-if="importPreview.skipped_details?.length" class="skipped-details">
            <li v-for="item in importPreview.skipped_details" :key="`${item.path}-${item.reason}`">
              <strong>{{ item.path }}</strong>
              <span>{{ item.reason }}</span>
            </li>
          </ul>
        </div>
      </section>

      <section class="import-form">
        <p class="section-kicker">浏览器文件夹</p>
        <h3>选择本机文件夹导入</h3>
        <p class="muted-line">通过浏览器授权读取文件夹内文本资料；会创建浏览器导入项目空间。</p>
        <input ref="folderInput" type="file" webkitdirectory multiple hidden @change="submitFolder" />
        <div class="actions">
          <button type="button" :disabled="importSubmitting" @click="openFolderPicker">
            {{ importSubmitting ? "导入中..." : "选择本机文件夹导入" }}
          </button>
        </div>
      </section>

      <section class="import-form">
        <p class="section-kicker">文件上传</p>
        <h3>选择文件上传导入</h3>
        <p class="muted-line">一次选择一个或多个临时文件；有当前项目空间时导入当前项目。</p>
        <input ref="fileInput" type="file" multiple hidden @change="submitFiles" />
        <div class="actions">
          <button type="button" :disabled="importSubmitting" @click="openFilePicker">
            {{ importSubmitting ? "导入中..." : "选择文件上传导入" }}
          </button>
        </div>
      </section>

      <form class="import-form" @submit.prevent="submitGithubRepo">
        <p class="section-kicker">GitHub 仓库</p>
        <h3>导入 GitHub 仓库</h3>
        <p class="muted-line">通过本机 git clone 拉取仓库，并创建新的项目空间。</p>
        <label>
          仓库地址
          <input
            v-model.trim="githubRepoForm.repoUrl"
            :disabled="importSubmitting"
            placeholder="https://github.com/owner/repo.git"
          />
        </label>
        <label>
          分支名
          <input v-model.trim="githubRepoForm.branch" :disabled="importSubmitting" placeholder="默认分支" />
        </label>
        <label>
          项目名称
          <input v-model.trim="githubRepoForm.projectName" :disabled="importSubmitting" placeholder="默认使用仓库名" />
        </label>
        <div class="actions">
          <button type="submit" :disabled="importSubmitting">
            {{ importSubmitting ? "导入中..." : "导入 GitHub 仓库" }}
          </button>
        </div>
      </form>

      <section class="import-form">
        <p class="section-kicker">Notion 导出</p>
        <h3>导入 Notion zip</h3>
        <p class="muted-line">选择 Notion 导出的 Markdown zip 包；只导入其中的 Markdown / 文本文件。</p>
        <input ref="notionZipInput" type="file" accept=".zip" hidden @change="submitNotionZip" />
        <div class="actions">
          <button type="button" :disabled="importSubmitting || !selectedProjectId" @click="openNotionZipPicker">
            {{ importSubmitting ? "导入中..." : "导入 Notion zip" }}
          </button>
        </div>
      </section>

      <form class="import-form" @submit.prevent="submitObsidianVault">
        <p class="section-kicker">Obsidian vault</p>
        <h3>导入 Obsidian vault</h3>
        <p class="muted-line">输入本机 vault 目录路径；会递归导入 Markdown / 文本文件并跳过 .obsidian 配置目录。</p>
        <label>
          Vault 本机路径
          <input
            v-model.trim="obsidianVaultPath"
            :disabled="importSubmitting"
            placeholder="例如：D:\\Notes\\MyVault"
          />
        </label>
        <div class="actions">
          <button type="submit" :disabled="importSubmitting || !selectedProjectId">
            {{ importSubmitting ? "导入中..." : "导入 Obsidian vault" }}
          </button>
        </div>
      </form>

      <form class="import-form" @submit.prevent="submitNote">
        <p class="section-kicker">文本笔记</p>
        <h3>导入文本笔记</h3>
        <label>
          笔记标题
          <input v-model.trim="noteForm.title" :disabled="importSubmitting" placeholder="例如：会议纪要" />
        </label>
        <label>
          笔记正文
          <textarea
            v-model="noteForm.content"
            :disabled="importSubmitting"
            placeholder="输入要加入当前项目空间的文本笔记"
            rows="5"
          ></textarea>
        </label>
        <div class="actions">
          <button type="submit" :disabled="importSubmitting || !selectedProjectId">
            {{ importSubmitting ? "导入中..." : "导入文本笔记" }}
          </button>
        </div>
      </form>

      <form class="import-form" @submit.prevent="submitUrl">
        <p class="section-kicker">URL 摘录</p>
        <h3>保存网页来源</h3>
        <label>
          网页地址
          <input v-model.trim="urlForm.url" :disabled="importSubmitting" placeholder="https://example.com/article" />
        </label>
        <label>
          网页标题
          <input v-model.trim="urlForm.title" :disabled="importSubmitting" placeholder="网页标题" />
        </label>
        <label>
          网页正文或摘要
          <textarea
            v-model="urlForm.content"
            :disabled="importSubmitting"
            placeholder="粘贴网页正文或摘要；当前不会自动抓取网页"
            rows="5"
          ></textarea>
        </label>
        <div class="actions">
          <button type="submit" :disabled="importSubmitting || !selectedProjectId">
            {{ importSubmitting ? "导入中..." : "导入 URL 摘录" }}
          </button>
        </div>
      </form>

      <form class="import-form" @submit.prevent="previewWebFetchUrl">
        <p class="section-kicker">网页抓取</p>
        <h3>抓取公开网页</h3>
        <p class="muted-line">仅处理公开 http/https 页面；后端检查 robots.txt、网络边界和正文大小。</p>
        <label>
          网页地址
          <input
            v-model.trim="webFetchForm.url"
            :disabled="importSubmitting || webFetchPreviewLoading"
            placeholder="https://example.com/article"
          />
        </label>
        <div class="actions">
          <button type="submit" :disabled="importSubmitting || webFetchPreviewLoading || !selectedProjectId">
            {{ webFetchPreviewLoading ? "抓取预览中..." : "抓取网页预览" }}
          </button>
          <button
            type="button"
            :disabled="importSubmitting || !selectedProjectId || !webFetchPreview"
            @click="commitWebFetchPreview"
          >
            {{ importSubmitting ? "导入中..." : "确认导入网页快照" }}
          </button>
        </div>
        <p v-if="webFetchPreviewError" class="status-line error">{{ webFetchPreviewError }}</p>
        <div v-if="webFetchPreview" class="import-preview" aria-label="网页抓取预览">
          <h4>{{ webFetchPreview.title }}</h4>
          <dl class="metadata-list">
            <div>
              <dt>最终 URL</dt>
              <dd>{{ webFetchPreview.final_url }}</dd>
            </div>
            <div>
              <dt>正文大小</dt>
              <dd>{{ webFetchPreview.content_length }} 字节</dd>
            </div>
            <div>
              <dt>抓取时间</dt>
              <dd>{{ webFetchPreview.fetched_at }}</dd>
            </div>
          </dl>
          <pre class="web-fetch-preview-content">{{ webFetchPreview.content }}</pre>
        </div>
      </form>
    </div>
  </section>
</template>

<script setup>
import { reactive, ref } from "vue";

const props = defineProps({
  selectedProjectId: {
    type: String,
    required: true,
  },
  importSubmitting: {
    type: Boolean,
    default: false,
  },
  importError: {
    type: String,
    default: "",
  },
  importStatus: {
    type: String,
    default: "",
  },
  importPreview: {
    type: Object,
    default: null,
  },
  importPreviewLoading: {
    type: Boolean,
    default: false,
  },
  importPreviewError: {
    type: String,
    default: "",
  },
  webFetchPreview: {
    type: Object,
    default: null,
  },
  webFetchPreviewLoading: {
    type: Boolean,
    default: false,
  },
  webFetchPreviewError: {
    type: String,
    default: "",
  },
});

const emit = defineEmits([
  "import-note",
  "import-url",
  "preview-web-fetch",
  "commit-web-fetch",
  "import-files",
  "import-folder",
  "import-notion-zip",
  "import-obsidian-vault",
  "import-github-repo",
  "sync-directory",
  "preview-import",
]);

const fileInput = ref(null);
const folderInput = ref(null);
const notionZipInput = ref(null);
const obsidianVaultPath = ref("");

const githubRepoForm = reactive({
  repoUrl: "",
  branch: "",
  projectName: "",
});

const noteForm = reactive({
  title: "",
  content: "",
});

const urlForm = reactive({
  url: "",
  title: "",
  content: "",
});

const webFetchForm = reactive({
  url: "",
});

function submitNote() {
  emit("import-note", {
    title: noteForm.title,
    content: noteForm.content,
  });
}

function submitUrl() {
  emit("import-url", {
    url: urlForm.url,
    title: urlForm.title,
    content: urlForm.content,
  });
}

function previewWebFetchUrl() {
  emit("preview-web-fetch", {
    url: webFetchForm.url,
  });
}

function commitWebFetchPreview() {
  emit("commit-web-fetch", {
    preview: props.webFetchPreview,
  });
}

function openFilePicker() {
  fileInput.value?.click();
}

function openFolderPicker() {
  folderInput.value?.click();
}

function openNotionZipPicker() {
  notionZipInput.value?.click();
}

function submitFiles(event) {
  emit("import-files", event.target.files);
  event.target.value = "";
}

function submitFolder(event) {
  emit("import-folder", event.target.files);
  event.target.value = "";
}

function submitNotionZip(event) {
  const [file] = Array.from(event.target.files || []);
  emit("import-notion-zip", file);
  event.target.value = "";
}

function submitObsidianVault() {
  emit("import-obsidian-vault", {
    vaultPath: obsidianVaultPath.value,
  });
}

function submitGithubRepo() {
  emit("import-github-repo", {
    repoUrl: githubRepoForm.repoUrl,
    branch: githubRepoForm.branch,
    projectName: githubRepoForm.projectName,
  });
}
</script>

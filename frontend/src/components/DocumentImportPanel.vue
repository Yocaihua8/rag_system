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
    <p v-else-if="importStatus" class="status-line">{{ importStatus }}</p>

    <div class="import-grid">
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
    </div>
  </section>
</template>

<script setup>
import { reactive, ref } from "vue";

defineProps({
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
});

const emit = defineEmits(["import-note", "import-url", "import-files"]);

const fileInput = ref(null);

const noteForm = reactive({
  title: "",
  content: "",
});

const urlForm = reactive({
  url: "",
  title: "",
  content: "",
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

function openFilePicker() {
  fileInput.value?.click();
}

function submitFiles(event) {
  emit("import-files", event.target.files);
  event.target.value = "";
}
</script>

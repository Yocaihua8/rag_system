<template>
  <section class="project-space-panel" aria-labelledby="project-space-title">
    <div class="section-title-row">
      <div>
        <p class="section-kicker">当前项目</p>
        <h2 id="project-space-title">项目空间</h2>
      </div>
      <button type="button" :disabled="loading" @click="$emit('refresh-projects')">
        {{ loading ? "刷新中..." : "刷新" }}
      </button>
    </div>

    <p v-if="loadError" class="status-line error">{{ loadError }}</p>
    <p v-else-if="projects.length === 0" class="status-line">未选择项目空间</p>

    <label class="field-block">
      选择项目空间
      <select :value="selectedProjectId" :disabled="loading || projects.length === 0" @change="handleProjectChange">
        <option value="">未选择项目空间</option>
        <option v-for="project in projects" :key="project.id" :value="project.id">
          {{ project.name }}
        </option>
      </select>
    </label>

    <p class="muted-line">
      {{ selectedProjectStatus }}
    </p>

    <form class="project-form" @submit.prevent="submitProject">
      <p class="section-kicker">新建项目空间</p>
      <label>
        项目名称
        <input v-model.trim="form.name" name="name" placeholder="例如：我的项目" />
      </label>
      <label>
        本地目录
        <input v-model.trim="form.path" name="path" placeholder="例如：E:\\Code\\project" required />
      </label>
      <div class="actions">
        <button type="submit" :disabled="formSubmitting">
          {{ formSubmitting ? "创建中..." : "创建项目空间" }}
        </button>
        <span class="status">{{ formStatus || statusMessage }}</span>
      </div>
      <p v-if="formError" class="status-line error">{{ formError }}</p>
    </form>
  </section>
</template>

<script setup>
import { computed, reactive } from "vue";

const props = defineProps({
  projects: {
    type: Array,
    required: true,
  },
  selectedProjectId: {
    type: String,
    required: true,
  },
  loading: {
    type: Boolean,
    default: false,
  },
  loadError: {
    type: String,
    default: "",
  },
  formSubmitting: {
    type: Boolean,
    default: false,
  },
  formError: {
    type: String,
    default: "",
  },
  formStatus: {
    type: String,
    default: "",
  },
  statusMessage: {
    type: String,
    default: "",
  },
});

const emit = defineEmits(["refresh-projects", "select-project", "create-project"]);

const form = reactive({
  name: "",
  path: "",
});

const selectedProject = computed(() => {
  return props.projects.find((project) => project.id === props.selectedProjectId) || null;
});

const selectedProjectStatus = computed(() => {
  if (!selectedProject.value) {
    return "未选择项目空间";
  }
  if (selectedProject.value.root_exists === false) {
    return "项目目录不存在";
  }
  return selectedProject.value.root || "未记录本地目录";
});

function handleProjectChange(event) {
  emit("select-project", event.target.value);
}

function submitProject() {
  emit("create-project", {
    name: form.name,
    path: form.path,
  });
}
</script>

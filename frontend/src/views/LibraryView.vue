<template>
  <section class="view-panel">
    <header class="topbar">
      <div>
        <p class="section-kicker">资料库</p>
        <h2>资料库</h2>
        <p>B-141C 已迁移项目空间基础，文件导入、文档集合和批次历史后续迁移。</p>
      </div>
    </header>

    <ProjectSpacePanel
      :projects="projects"
      :selected-project-id="selectedProjectId"
      :loading="projectsLoading"
      :load-error="projectLoadError"
      :form-submitting="projectFormSubmitting"
      :form-error="projectFormError"
      :form-status="projectFormStatus"
      :status-message="projectStatusMessage"
      @refresh-projects="$emit('refresh-projects')"
      @select-project="(projectId) => $emit('select-project', projectId)"
      @create-project="(payload) => $emit('create-project', payload)"
    />
  </section>
</template>

<script setup>
import ProjectSpacePanel from "../components/ProjectSpacePanel.vue";

defineProps({
  projects: {
    type: Array,
    required: true,
  },
  selectedProjectId: {
    type: String,
    required: true,
  },
  projectsLoading: {
    type: Boolean,
    default: false,
  },
  projectLoadError: {
    type: String,
    default: "",
  },
  projectFormSubmitting: {
    type: Boolean,
    default: false,
  },
  projectFormError: {
    type: String,
    default: "",
  },
  projectFormStatus: {
    type: String,
    default: "",
  },
  projectStatusMessage: {
    type: String,
    default: "",
  },
});

defineEmits(["refresh-projects", "select-project", "create-project"]);
</script>

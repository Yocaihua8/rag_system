<template>
  <main class="workspace-shell" :class="{ 'sidebar-collapsed': sidebarCollapsed }">
    <WorkspaceSidebar
      v-if="!sidebarCollapsed"
      :current-view="currentView"
      :sidebar-mode="sidebarMode"
      :projects="projects"
      :selected-project-id="selectedProjectId"
      :library-target-project-id="libraryTargetProjectId"
      :chat-sessions="chatSessions"
      :selected-chat-session-id="selectedChatSessionId"
      @collapse-sidebar="sidebarCollapsed = true"
      @change-view="emit('change-view', $event)"
      @open-library="emit('open-library')"
      @back-to-threads="emit('back-to-threads')"
      @select-library-target-project="emit('select-library-target-project', $event)"
      @select-project="emit('select-project', $event)"
      @select-chat-session="emit('select-chat-session', $event)"
      @create-chat-session="emit('create-chat-session', $event)"
    />

    <section class="workspace-main">
      <header class="topbar">
        <button
          type="button"
          class="icon-button topbar-menu-button"
          aria-label="打开侧边栏"
          data-shell-action="open-sidebar"
          @click="sidebarCollapsed = false"
        >
          ☰
        </button>
        <div>
          <p class="eyebrow">Knowledge Island</p>
          <h2>{{ activeTitle }}</h2>
          <p>{{ activeDescription }}</p>
        </div>
        <div class="status-pills" aria-label="服务状态">
          <span>{{ currentProjectName }}</span>
          <span>{{ visibleChatSessions.length }} 条线程</span>
        </div>
      </header>

      <slot />
    </section>
  </main>
</template>

<script setup>
import { computed, ref } from "vue";
import WorkspaceSidebar from "./WorkspaceSidebar.vue";

const navItems = [
  { key: "chat", title: "聊天", description: "从当前工作区开始提问，资料、练习和工具都从输入框添加。" },
  { key: "settings", title: "设置", description: "管理回答方式、模型、资料位置、备份和外观。" },
];

const sidebarCollapsed = ref(isNarrowScreen());

const props = defineProps({
  currentView: {
    type: String,
    required: true,
  },
  sidebarMode: {
    type: String,
    default: "threads",
  },
  projects: {
    type: Array,
    default: () => [],
  },
  selectedProjectId: {
    type: String,
    default: "",
  },
  libraryTargetProjectId: {
    type: String,
    default: "",
  },
  chatSessions: {
    type: Array,
    default: () => [],
  },
  selectedChatSessionId: {
    type: String,
    default: "",
  },
});

const emit = defineEmits([
  "back-to-threads",
  "change-view",
  "create-chat-session",
  "open-library",
  "select-chat-session",
  "select-library-target-project",
  "select-project",
]);

const activeTitle = computed(() => {
  return navItems.find((item) => item.key === props.currentView)?.title || "聊天";
});

const activeDescription = computed(() => {
  return navItems.find((item) => item.key === props.currentView)?.description || navItems[0].description;
});

const visibleChatSessions = computed(() => {
  if (!props.selectedProjectId) {
    return props.chatSessions;
  }
  return props.chatSessions.filter((session) => {
    return !session.project_id || session.project_id === props.selectedProjectId;
  });
});

const currentProjectName = computed(() => {
  return props.projects.find((project) => project.id === props.selectedProjectId)?.name || "未选择工作区";
});

function isNarrowScreen() {
  return Boolean(
    typeof window !== "undefined"
      && typeof window.matchMedia === "function"
      && window.matchMedia("(max-width: 760px)").matches,
  );
}
</script>

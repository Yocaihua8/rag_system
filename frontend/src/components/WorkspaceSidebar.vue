<template>
  <aside class="workspace-left" data-workspace-sidebar>
    <header class="brand-block">
      <span class="brand-mark" aria-hidden="true">KI</span>
      <div>
        <h1>Knowledge Island</h1>
        <p>本地资料助手</p>
      </div>
      <button
        type="button"
        class="icon-button sidebar-collapse-button"
        aria-label="收起侧边栏"
        data-shell-action="collapse-sidebar"
        @click="emit('collapse-sidebar')"
      >
        ☰
      </button>
    </header>

    <nav class="main-nav" aria-label="主导航">
      <button
        type="button"
        :class="{ active: currentView === 'chat' }"
        :aria-current="currentView === 'chat' ? 'page' : undefined"
        data-view-key="chat"
        title="聊天"
        @click="emit('change-view', 'chat')"
      >
        <span aria-hidden="true">□</span>
        聊
      </button>
      <button type="button" data-nav-action="library" title="库" @click="emit('open-library')">
        <span aria-hidden="true">▭</span>
        库
      </button>
      <button
        type="button"
        :class="{ active: currentView === 'settings' }"
        :aria-current="currentView === 'settings' ? 'page' : undefined"
        data-view-key="settings"
        title="设置"
        @click="emit('change-view', 'settings')"
      >
        <span aria-hidden="true">○</span>
        设
      </button>
    </nav>

    <section class="sidebar-section" aria-label="工作区和聊天">
      <template v-if="sidebarMode === 'workspace-select'">
        <div class="sidebar-title-row">
          <div>
            <p class="section-kicker">选择资料后</p>
            <h2>选择工作区</h2>
          </div>
          <button type="button" class="ghost-button" @click="emit('back-to-threads')">返回</button>
        </div>
        <div class="sidebar-list">
          <button
            v-for="project in projects"
            :key="project.id"
            type="button"
            class="sidebar-item"
            :class="{ active: project.id === activeLibraryTargetProjectId }"
            data-sidebar-workspace
            @click="emit('select-library-target-project', project.id)"
          >
            <span>{{ project.name }}</span>
            <small>{{ formatCount(project.document_count) }}</small>
          </button>
        </div>
      </template>

      <template v-else>
        <div class="sidebar-title-row">
          <div>
            <p class="section-kicker">工作区</p>
            <h2>{{ currentProjectName }}</h2>
          </div>
          <button type="button" class="ghost-button" data-sidebar-action="open-library" @click="emit('open-library')">
            加入资料
          </button>
        </div>

        <div class="sidebar-list project-list">
          <button
            v-for="project in projects"
            :key="project.id"
            type="button"
            class="sidebar-item"
            :class="{ active: project.id === selectedProjectId }"
            @click="emit('select-project', project.id)"
          >
            <span>{{ project.name }}</span>
            <small>{{ formatCount(project.document_count) }}</small>
          </button>
        </div>

        <div class="sidebar-title-row compact">
          <h2>线程</h2>
          <button
            type="button"
            class="ghost-button"
            data-sidebar-action="create-chat-session"
            @click="emit('create-chat-session', '')"
          >
            新建
          </button>
        </div>
        <label class="sidebar-search">
          <span class="sr-only">搜索线程</span>
          <input type="search" placeholder="搜索线程" />
        </label>
        <div class="sidebar-list thread-list">
          <button
            v-for="session in visibleChatSessions"
            :key="session.id"
            type="button"
            class="sidebar-item thread-item"
            :class="{ active: session.id === selectedChatSessionId }"
            @click="emit('select-chat-session', session.id)"
          >
            <span>{{ session.title || '新的聊天' }}</span>
            <small>{{ formatCount(session.message_count) }}</small>
          </button>
        </div>
      </template>
    </section>
  </aside>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  currentView: {
    type: String,
    default: "chat",
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
  "collapse-sidebar",
  "create-chat-session",
  "open-library",
  "select-chat-session",
  "select-library-target-project",
  "select-project",
]);

const currentProjectName = computed(() => {
  return props.projects.find((project) => project.id === props.selectedProjectId)?.name || "未选择工作区";
});

const activeLibraryTargetProjectId = computed(() => {
  return props.libraryTargetProjectId || props.selectedProjectId;
});

const visibleChatSessions = computed(() => {
  if (!props.selectedProjectId) {
    return props.chatSessions;
  }
  return props.chatSessions.filter((session) => {
    return !session.project_id || session.project_id === props.selectedProjectId;
  });
});

function formatCount(value) {
  if (typeof value !== "number") {
    return "";
  }
  return `${value}`;
}
</script>

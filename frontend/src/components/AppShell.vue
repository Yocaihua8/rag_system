<template>
  <main class="workspace-shell">
    <aside class="workspace-left">
      <header class="brand-block">
        <h1>知识岛</h1>
        <p>本地知识工作台</p>
      </header>

      <nav class="main-nav" aria-label="主导航">
        <button
          type="button"
          :class="{ active: currentView === 'workbench' }"
          :aria-current="currentView === 'workbench' ? 'page' : undefined"
          data-view-key="workbench"
          @click="$emit('change-view', 'workbench')"
        >
          工作台
        </button>
        <button
          type="button"
          :class="{ active: currentView === 'library' }"
          :aria-current="currentView === 'library' ? 'page' : undefined"
          data-view-key="library"
          @click="$emit('change-view', 'library')"
        >
          资料库
        </button>
        <button
          type="button"
          :class="{ active: currentView === 'assessment' }"
          :aria-current="currentView === 'assessment' ? 'page' : undefined"
          data-view-key="assessment"
          @click="$emit('change-view', 'assessment')"
        >
          评估
        </button>
        <button
          type="button"
          :class="{ active: currentView === 'settings' }"
          :aria-current="currentView === 'settings' ? 'page' : undefined"
          data-view-key="settings"
          @click="$emit('change-view', 'settings')"
        >
          设置
        </button>
      </nav>
    </aside>

    <section class="workspace-main">
      <header class="topbar">
        <div>
          <p class="eyebrow">B-142 Vue Workbench</p>
          <h2>{{ activeTitle }}</h2>
        <p>Vue 工作台已接入流式问答、会话历史、消息管理、检索调试、检索复盘、Agent 只读工具和工具来源上下文；legacy 静态前端仍作为 fallback 保留到 B-143。</p>
        </div>
        <div class="status-pills" aria-label="服务状态">
          <span>FastAPI</span>
          <span>Vue 3</span>
          <span>Vite</span>
        </div>
      </header>

      <slot />
    </section>
  </main>
</template>

<script setup>
import { computed } from "vue";

const navItems = [
  { key: "workbench", label: "工作台", title: "项目问答" },
  { key: "library", label: "资料库", title: "资料库" },
  { key: "assessment", label: "评估", title: "掌握评估" },
  { key: "settings", label: "设置", title: "设置" },
];

const props = defineProps({
  currentView: {
    type: String,
    required: true,
  },
});

defineEmits(["change-view"]);

const activeTitle = computed(() => {
  return navItems.find((item) => item.key === props.currentView)?.title || "项目问答";
});
</script>

<template>
  <main class="workspace-shell">
    <aside class="workspace-left">
      <header class="brand-block">
        <h1>知识岛</h1>
        <p>Vue 前端迁移工作台</p>
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
          <p class="eyebrow">B-141 Vue Migration</p>
          <h2>{{ activeTitle }}</h2>
        <p>B-141 已按薄片迁移项目问答、检索调试、项目级检索默认值、Agent 只读工具、工具来源上下文、资料库、设置和评估基础闭环；SSE 和会话后续迁移。</p>
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

<template>
  <div class="atlas-shell" :data-theme="isDark ? 'dark' : undefined" data-rule="strong">
    <header class="masthead">
      <div class="brand">
        <span class="brand-mark">
          <svg width="34" height="34" viewBox="0 0 40 40" fill="none" class="island-mark">
            <rect x="0.5" y="0.5" width="39" height="39" stroke="currentColor" stroke-opacity="0.35" />
            <g stroke="var(--accent)" fill="none" stroke-width="1">
              <path d="M20 9 L29 25 L11 25 Z" fill="var(--accent)" fill-opacity="0.12" />
              <path d="M20 13 L26 24 L14 24 Z" />
              <path d="M20 17 L23 23 L17 23 Z" />
            </g>
            <path d="M5 31 Q11 28 17 30 Q23 32 29 29 Q33 27 35 29" stroke="var(--accent)" stroke-width="0.9" fill="none" opacity="0.7" />
            <path d="M5 35 Q12 32 20 34 Q28 36 35 33" stroke="var(--accent)" stroke-width="0.7" fill="none" opacity="0.4" />
          </svg>
        </span>
        <span class="brand-text">
          <h1>知识岛 · Knowledge Island</h1>
          <span class="vol" title="本地优先的个人 AI 知识库；导入资料、检索来源、提问和评估掌握情况">海图志 · Vol. I · 2026 · {{ currentProjectName }}</span>
        </span>
      </div>
      <nav class="nav" aria-label="主导航">
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
        <span class="folio">FOL. {{ folioNumber }}</span>
      </nav>
    </header>

    <slot />

    <div class="ki-foot">— 知识岛 · 海图志版 · 本地优先 · 个人第二大脑 · MMXXVI —</div>
  </div>
</template>

<script setup>
import { computed, ref } from "vue";

const navItems = [
  { key: "workbench", label: "工作台", folio: "I" },
  { key: "library", label: "资料库", folio: "II" },
  { key: "assessment", label: "评估", folio: "III" },
  { key: "settings", label: "设置", folio: "IV" },
];

const props = defineProps({
  currentView: {
    type: String,
    required: true,
  },
  projects: {
    type: Array,
    default: () => [],
  },
  selectedProjectId: {
    type: String,
    default: "",
  },
});

defineEmits(["change-view"]);

const isDark = ref(false);

const currentProjectName = computed(() => {
  const project = props.projects.find((entry) => entry.id === props.selectedProjectId);
  return project?.name || "未选择项目";
});

const folioNumber = computed(() => {
  return navItems.find((item) => item.key === props.currentView)?.folio || "I";
});
</script>

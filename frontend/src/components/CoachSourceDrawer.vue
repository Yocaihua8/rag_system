<template>
  <div v-if="open" class="coach-drawer-backdrop" data-coach-source-action="backdrop" @click.self="emit('close')">
    <aside class="coach-source-drawer" aria-label="项目知识来源">
      <header class="coach-drawer-header">
        <div>
          <p class="section-kicker">来源</p>
          <h2>{{ title }}</h2>
        </div>
        <button type="button" data-coach-source-action="close" @click="emit('close')">关闭</button>
      </header>

      <p class="coach-scope-notice">以下内容来自当前项目的已导入资料。</p>
      <p v-if="visibleSources.length === 0" class="muted-line">暂无可用来源。</p>
      <ol v-else class="coach-source-list">
        <li v-for="source in visibleSources" :key="source.id || source.path || source.source_path">
          <strong>{{ source.path || source.source_path || "未知路径" }}</strong>
          <p v-if="source.excerpt" class="coach-source-excerpt">{{ source.excerpt }}</p>
          <p v-else class="muted-line">无片段预览。</p>
          <dl v-if="source.locator && Object.keys(source.locator).length" class="coach-source-locator">
            <template v-for="entry in locatorEntries(source.locator)" :key="entry[0]">
              <dt>{{ entry[0] }}</dt>
              <dd>{{ entry[1] }}</dd>
            </template>
          </dl>
        </li>
      </ol>
    </aside>
  </div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  open: {
    type: Boolean,
    default: false,
  },
  title: {
    type: String,
    default: "知识来源",
  },
  sourceIds: {
    type: Array,
    default: () => [],
  },
  sources: {
    type: [Object, Array],
    default: () => ({}),
  },
});

const emit = defineEmits(["close"]);

const sourceIndex = computed(() => {
  if (Array.isArray(props.sources)) {
    return Object.fromEntries(
      props.sources
        .filter((source) => source && typeof source === "object")
        .map((source) => [source.id || source.path || source.source_path, source]),
    );
  }
  return props.sources || {};
});

const visibleSources = computed(() => {
  if (props.sourceIds.length > 0) {
    return props.sourceIds.map((sourceId) => sourceIndex.value[sourceId]).filter(Boolean);
  }
  return Object.values(sourceIndex.value);
});

function locatorEntries(locator) {
  if (!locator || typeof locator !== "object" || Array.isArray(locator)) {
    return [];
  }
  return Object.entries(locator).map(([key, value]) => [
    key,
    typeof value === "object" && value !== null ? JSON.stringify(value) : String(value),
  ]);
}
</script>

<style scoped>
.coach-drawer-backdrop {
  position: fixed;
  inset: 0;
  z-index: 40;
  display: flex;
  justify-content: flex-end;
  background: rgb(17 17 17 / 28%);
}

.coach-source-drawer {
  width: min(460px, 92vw);
  height: 100%;
  overflow-y: auto;
  padding: var(--space-5);
  color: var(--text-primary);
  background: var(--surface-card);
  border-left: 1px solid var(--border);
  box-shadow: var(--shadow-lg);
}

.coach-drawer-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-4);
}

.coach-drawer-header h2 {
  margin: var(--space-1) 0 0;
}

.coach-scope-notice {
  padding: var(--space-3);
  color: var(--text-secondary);
  background: var(--surface-sunken);
  border-radius: var(--radius);
}

.coach-source-list {
  display: grid;
  gap: var(--space-3);
  padding: 0;
  list-style: none;
}

.coach-source-list li {
  padding: var(--space-4);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
}

.coach-source-excerpt {
  margin: var(--space-2) 0;
  white-space: pre-wrap;
}

.coach-source-locator {
  display: grid;
  grid-template-columns: max-content 1fr;
  gap: var(--space-1) var(--space-3);
  margin: var(--space-3) 0 0;
  color: var(--text-secondary);
  font-size: var(--text-sm);
}

.coach-source-locator dt {
  font-weight: var(--weight-medium);
}

.coach-source-locator dd {
  margin: 0;
  overflow-wrap: anywhere;
}
</style>

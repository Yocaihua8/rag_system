<template>
  <section class="import-result-list" data-import-result-list>
    <div class="import-result-header">
      <div>
        <h3>本次结果</h3>
        <p>{{ summary }}</p>
      </div>
      <button type="button" class="ghost-button" data-import-result-toggle @click="toggleOpen">
        {{ isOpen ? "收起" : "展开" }}
      </button>
    </div>
    <div v-if="isOpen" class="import-result-details" data-import-result-details>
      <p v-if="status" class="status-line">{{ status }}</p>
      <p v-if="error" class="status-line error">{{ error }}</p>
      <p v-if="!status && !error" class="status-line">还没有新的加入结果。</p>
    </div>
  </section>
</template>

<script setup>
import { computed, ref, watch } from "vue";

const props = defineProps({
  status: {
    type: String,
    default: "",
  },
  error: {
    type: String,
    default: "",
  },
});

const isOpen = ref(false);
const hasResult = computed(() => Boolean(props.status || props.error));
const summary = computed(() => {
  if (props.error) {
    return "加入资料时遇到问题";
  }
  if (props.status) {
    return "已更新本次加入结果";
  }
  return "默认收起，加入资料后会自动展开。";
});

watch(
  hasResult,
  (value) => {
    if (value) {
      isOpen.value = true;
    }
  },
  { immediate: true },
);

function toggleOpen() {
  isOpen.value = !isOpen.value;
}
</script>

<style scoped>
.import-result-list {
  background: #ffffff;
  border: 1px solid #dddddd;
  border-radius: 8px;
  display: grid;
  gap: 12px;
  padding: 14px;
}

.import-result-header {
  align-items: center;
  display: flex;
  gap: 14px;
  justify-content: space-between;
}

.import-result-header h3,
.import-result-header p {
  margin: 0;
}

.import-result-header p {
  color: #666666;
}

.import-result-details {
  border-top: 1px solid #eeeeee;
  display: grid;
  gap: 8px;
  padding-top: 12px;
}
</style>

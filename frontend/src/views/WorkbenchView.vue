<template>
  <section class="view-panel">
    <p class="section-kicker">工作台</p>
    <h2>项目问答</h2>
    <p>B-141B 后续迁移问答、来源、Agent 工具和检索调试。</p>
    <div class="actions">
      <button type="button" @click="$emit('check-health')">检查本地服务</button>
      <span class="status">{{ statusMessage }}</span>
    </div>
  </section>
</template>

<script setup>
defineProps({
  statusMessage: {
    type: String,
    required: true,
  },
});

defineEmits(["check-health"]);
</script>

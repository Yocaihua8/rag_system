<template>
  <main class="app-shell">
    <section class="hero-panel">
      <p class="eyebrow">B-141A Vue + Vite foundation</p>
      <h1>知识岛</h1>
      <p class="lead">
        当前是前端工程化骨架阶段。完整业务界面仍由 legacy 静态前端提供，后续将按页面逐步迁移到 Vue 组件。
      </p>
      <div class="actions">
        <button type="button" @click="checkHealth">检查本地服务</button>
        <span class="status">{{ statusMessage }}</span>
      </div>
    </section>
  </main>
</template>

<script setup>
import { ref } from "vue";

const statusMessage = ref("等待检查");

async function checkHealth() {
  statusMessage.value = "检查中...";
  try {
    const response = await fetch("/api/health");
    const data = await response.json();
    statusMessage.value = data.status === "ok" ? "本地服务正常" : "服务状态异常";
  } catch (error) {
    statusMessage.value = "本地服务暂时不可用";
  }
}
</script>

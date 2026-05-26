<template>
  <AppShell :current-view="appState.currentView" @change-view="showView">
    <component
      :is="currentViewComponent"
      :status-message="statusMessage"
      @check-health="checkHealth"
    />
  </AppShell>
</template>

<script setup>
import { computed, ref } from "vue";

import { apiGet } from "./api/client.js";
import AppShell from "./components/AppShell.vue";
import { appState, showView } from "./state/app-state.js";
import AssessmentView from "./views/AssessmentView.vue";
import LibraryView from "./views/LibraryView.vue";
import SettingsView from "./views/SettingsView.vue";
import WorkbenchView from "./views/WorkbenchView.vue";

const viewComponents = {
  workbench: WorkbenchView,
  library: LibraryView,
  assessment: AssessmentView,
  settings: SettingsView,
};

const statusMessage = ref("等待检查");

const currentViewComponent = computed(() => {
  return viewComponents[appState.currentView] || WorkbenchView;
});

async function checkHealth() {
  statusMessage.value = "检查中...";
  try {
    const data = await apiGet("/api/health");
    statusMessage.value = data.status === "ok" ? "本地服务正常" : "服务状态异常";
  } catch (error) {
    statusMessage.value = "本地服务暂时不可用";
  }
}
</script>

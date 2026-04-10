import { createApp, onMounted, ref } from "vue";
import "./style.css";

const App = {
  setup() {
    const question = ref("");
    const answer = ref("");
    const hits = ref<string[]>([]);
    const history = ref<Array<{ id: string; question: string; answer: string; created_at: string }>>([]);
    const lastTaskId = ref("");
    const status = ref("");

    const apiBase = "/api";
    const exportsPath = ref("F:\\PersonalRAG\\knowledge_base\\exports");

    function parseErrorDetail(detail: unknown): string {
      if (!detail) return "Unknown error";
      if (typeof detail === "string") return detail;
      if (typeof detail === "object") {
        const record = detail as Record<string, unknown>;
        const parts: string[] = [];
        if (typeof record.message === "string" && record.message) {
          parts.push(record.message);
        }
        if (typeof record.error === "string" && record.error) {
          parts.push(record.error);
        }
        if (typeof record.task_id === "string" && record.task_id) {
          parts.push(`task=${record.task_id}`);
        }
        if (record.result && typeof record.result === "object") {
          const result = record.result as Record<string, unknown>;
          const errorCount = Number(result.error_count || 0);
          if (errorCount > 0) {
            parts.push(`errors=${errorCount}`);
          }
        }
        if (parts.length > 0) {
          return parts.join(" | ");
        }
        return JSON.stringify(record);
      }
      return String(detail);
    }

    async function postJson(path: string, body?: unknown) {
      const res = await fetch(`${apiBase}${path}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: body === undefined ? undefined : JSON.stringify(body),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        const detail = parseErrorDetail((data as Record<string, unknown>)?.detail);
        throw new Error(`HTTP ${res.status}: ${detail}`);
      }
      return data as Record<string, unknown>;
    }

    async function getJson(path: string) {
      const res = await fetch(`${apiBase}${path}`);
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        const detail = parseErrorDetail((data as Record<string, unknown>)?.detail);
        throw new Error(`HTTP ${res.status}: ${detail}`);
      }
      return data as Record<string, unknown>;
    }

    async function pollTask(taskId: string): Promise<Record<string, unknown>> {
      for (let i = 0; i < 60; i += 1) {
        const task = await getJson(`/task/${taskId}`);
        const taskStatus = String(task.status || "running");
        const progress = Number(task.progress || 0);
        const message = String(task.message || "");
        status.value = `[${taskStatus}] ${progress}% ${message}`.trim();
        if (taskStatus === "done" || taskStatus === "failed" || taskStatus === "unknown") {
          return task;
        }
        await new Promise((resolve) => setTimeout(resolve, 500));
      }
      throw new Error("Task polling timeout");
    }

    async function query() {
      status.value = "Running...";
      try {
        const data = await postJson("/query", { question: question.value, top_k: 5 });
        answer.value = (data.answer as string) || "";
        hits.value = (data.hits as string[]) || [];
        await loadHistory();
        status.value = "Done";
      } catch (err) {
        answer.value = "";
        hits.value = [];
        status.value = err instanceof Error ? err.message : String(err);
      }
    }

    async function loadHistory() {
      try {
        const data = await getJson("/history?limit=5");
        const items = (data.items as Array<{ id: string; question: string; answer: string; created_at: string }>) || [];
        history.value = items;
      } catch (err) {
        status.value = err instanceof Error ? err.message : String(err);
      }
    }

    async function checkHealth() {
      try {
        const data = await getJson("/health");
        const serviceStatus = String(data.status || "unknown");
        status.value = serviceStatus === "ok" ? "API ready" : `API status: ${serviceStatus}`;
      } catch (err) {
        status.value = err instanceof Error ? err.message : String(err);
      }
    }

    async function buildIndex() {
      status.value = "Building...";
      try {
        const data = await postJson("/build");
        const taskId = String(data.task_id || "");
        lastTaskId.value = taskId;
        if (taskId) {
          const task = await pollTask(taskId);
          if (String(task.status) !== "done") {
            throw new Error(String(task.message || "Build failed"));
          }
        }
        status.value = taskId ? `Build done (task=${taskId})` : "Build done";
      } catch (err) {
        status.value = err instanceof Error ? err.message : String(err);
      }
    }

    async function ingestFiles() {
      status.value = "Selecting files...";
      try {
        const bridge = (window as unknown as { pywebview?: { api?: { pick_files?: () => Promise<string[]> } } })
          .pywebview?.api;
        if (!bridge?.pick_files) {
          throw new Error("pywebview bridge not available");
        }

        const selected = await bridge.pick_files();
        if (!selected || selected.length === 0) {
          status.value = "Import cancelled";
          return;
        }

        status.value = "Importing...";
        const data = await postJson("/ingest", { paths: selected });
        const taskId = String(data.task_id || "");
        lastTaskId.value = taskId;
        if (taskId) {
          const task = await pollTask(taskId);
          if (String(task.status) !== "done") {
            throw new Error(String(task.message || "Import failed"));
          }
        }
        const result = (data.result as Record<string, unknown>) || {};
        const importedCount = Number(result.imported_count || 0);
        const skippedCount = Number(result.skipped_count || 0);
        status.value = taskId
          ? `Import done (task=${taskId}): imported=${importedCount}, skipped=${skippedCount}`
          : `Import done: imported=${importedCount}, skipped=${skippedCount}`;
      } catch (err) {
        status.value = err instanceof Error ? err.message : String(err);
      }
    }

    async function ingestFolder() {
      status.value = "Selecting folder...";
      try {
        const bridge = (window as unknown as { pywebview?: { api?: { pick_folder?: () => Promise<string> } } })
          .pywebview?.api;
        if (!bridge?.pick_folder) {
          throw new Error("pywebview bridge not available");
        }

        const selected = await bridge.pick_folder();
        if (!selected) {
          status.value = "Import cancelled";
          return;
        }

        status.value = "Importing folder...";
        const data = await postJson("/ingest", { paths: [selected] });
        const taskId = String(data.task_id || "");
        lastTaskId.value = taskId;
        if (taskId) {
          const task = await pollTask(taskId);
          if (String(task.status) !== "done") {
            throw new Error(String(task.message || "Import failed"));
          }
        }
        const result = (data.result as Record<string, unknown>) || {};
        const importedCount = Number(result.imported_count || 0);
        const skippedCount = Number(result.skipped_count || 0);
        status.value = taskId
          ? `Import done (task=${taskId}): imported=${importedCount}, skipped=${skippedCount}`
          : `Import done: imported=${importedCount}, skipped=${skippedCount}`;
      } catch (err) {
        status.value = err instanceof Error ? err.message : String(err);
      }
    }

    async function openExports() {
      try {
        const bridge = (
          window as unknown as {
            pywebview?: { api?: { open_path?: (path: string) => Promise<boolean>; get_exports_path?: () => Promise<string> } };
          }
        )
          .pywebview?.api;
        if (!bridge?.open_path) {
          throw new Error("pywebview bridge not available");
        }
        if (bridge.get_exports_path) {
          const resolved = await bridge.get_exports_path();
          if (resolved) {
            exportsPath.value = resolved;
          }
        }
        const ok = await bridge.open_path(exportsPath.value);
        status.value = ok ? "Exports folder opened" : "Exports path not found";
      } catch (err) {
        status.value = err instanceof Error ? err.message : String(err);
      }
    }

    async function checkLastTask() {
      try {
        if (!lastTaskId.value) {
          status.value = "No task yet";
          return;
        }
        const task = await getJson(`/task/${lastTaskId.value}`);
        const taskStatus = String(task.status || "unknown");
        const progress = Number(task.progress || 0);
        const message = String(task.message || "");
        status.value = `[${taskStatus}] ${progress}% ${message} (task=${lastTaskId.value})`.trim();
      } catch (err) {
        status.value = err instanceof Error ? err.message : String(err);
      }
    }

    function formatHistoryTime(value: string): string {
      if (!value) return "";
      const d = new Date(value);
      if (Number.isNaN(d.getTime())) return value;
      return d.toLocaleString();
    }

    onMounted(async () => {
      await checkHealth();
      await loadHistory();
    });

    return {
      question,
      answer,
      hits,
      history,
      lastTaskId,
      status,
      query,
      checkHealth,
      loadHistory,
      buildIndex,
      ingestFiles,
      ingestFolder,
      openExports,
      formatHistoryTime,
      checkLastTask,
    };
  },
  template: `
    <div class="app">
      <header class="header">
        <div class="title">Python RAG Desktop Assistant</div>
        <div class="subtitle">Python-led desktop app</div>
      </header>

      <section class="panel">
        <div class="panel-title">Quick Actions</div>
        <div class="row">
          <button class="btn" @click="ingestFiles">Import Markdown</button>
          <button class="btn" @click="ingestFolder">Import Folder</button>
          <button class="btn" @click="buildIndex">Build Index</button>
          <button class="btn" @click="checkHealth">Check API</button>
          <button class="btn" @click="checkLastTask">Check Last Task</button>
          <button class="btn" @click="openExports">Open Exports</button>
          <div class="status">{{ status }}</div>
        </div>
        <div class="row" v-if="lastTaskId">
          <div class="status">Last Task ID: {{ lastTaskId }}</div>
        </div>
      </section>

      <section class="panel">
        <div class="panel-title">Ask</div>
        <textarea v-model="question" placeholder="Type your question"></textarea>
        <div class="row">
          <button class="btn" @click="query">Query</button>
          <button class="btn" @click="loadHistory">Load History</button>
        </div>
        <div class="answer" v-if="answer">
          <div class="answer-title">Answer</div>
          <div class="answer-text">{{ answer }}</div>
        </div>
        <div class="hits" v-if="hits.length">
          <div class="answer-title">Hits</div>
          <ul>
            <li v-for="h in hits" :key="h">{{ h }}</li>
          </ul>
        </div>
        <div class="hits" v-if="history.length">
          <div class="answer-title">Recent History</div>
          <ul>
            <li v-for="item in history" :key="item.id">
              <strong>Q:</strong> {{ item.question }}<br />
              <strong>A:</strong> {{ item.answer }}<br />
              <small>{{ formatHistoryTime(item.created_at) }}</small>
            </li>
          </ul>
        </div>
      </section>
    </div>
  `,
};

createApp(App).mount("#app");

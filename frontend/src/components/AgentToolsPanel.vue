<template>
  <section class="agent-tools-panel" aria-labelledby="agent-tools-title">
    <div class="section-title-row">
      <div>
        <p class="section-kicker">Agent 工具</p>
        <h2 id="agent-tools-title">Agent 工具</h2>
        <p>当前只开放只读工具，并记录工具调用。</p>
      </div>
      <button type="button" :disabled="agentToolsLoading" @click="$emit('load-agent-tools')">
        {{ agentToolsLoading ? "刷新中..." : "刷新工具" }}
      </button>
    </div>

    <p v-if="!selectedProjectId" class="muted-line">请选择项目空间后运行只读工具。</p>
    <p v-if="agentToolsError" class="status-line error">{{ agentToolsError }}</p>
    <p v-if="agentToolStatus" class="status-line">{{ agentToolStatus }}</p>
    <p v-if="agentToolError" class="status-line error">{{ agentToolError }}</p>

    <div class="agent-tool-actions">
      <button
        type="button"
        :disabled="!selectedProjectId || agentToolSubmittingName === 'project_overview'"
        @click="runProjectOverview"
      >
        {{ agentToolSubmittingName === "project_overview" ? "运行中..." : "项目概览：运行" }}
      </button>
      <label>
        工具参数：query
        <input v-model="sourceQuery" placeholder="检索来源，例如：默认入口、API endpoint" />
      </label>
      <button
        type="button"
        :disabled="!selectedProjectId || agentToolSubmittingName === 'search_sources'"
        @click="runSearchSources"
      >
        {{ agentToolSubmittingName === "search_sources" ? "运行中..." : "检索来源：运行" }}
      </button>
    </div>

    <div class="agent-tools-layout">
      <section class="agent-tool-list">
        <div class="section-title-row compact">
          <p class="section-kicker">只读工具</p>
        </div>
        <ul v-if="agentTools.length" class="agent-tools-list">
          <li v-for="tool in agentTools" :key="tool.name">
            <strong>{{ tool.label || tool.title || tool.name }}</strong>
            <p>{{ tool.description || "暂无工具说明" }}</p>
            <small>参数：{{ formatToolParameters(tool) }}</small>
            <small>适用场景：{{ formatToolScenarios(tool) }}</small>
            <button
              type="button"
              :disabled="!selectedProjectId || agentToolSubmittingName === tool.name"
              @click="runListedTool(tool)"
            >
              {{ tool.label || tool.name }}：运行
            </button>
          </li>
        </ul>
        <p v-else class="muted-line">暂无可用只读工具</p>
      </section>

      <section class="agent-tool-output">
        <p class="section-kicker">工具结果</p>
        <pre class="answer compact-answer">{{ formatToolResult(agentToolResult) }}</pre>
      </section>
    </div>

    <div class="agent-tools-layout">
      <section>
        <div class="section-title-row compact">
          <p class="section-kicker">运行历史</p>
          <button type="button" :disabled="agentToolRunsLoading || !selectedProjectId" @click="$emit('load-agent-tool-runs')">
            {{ agentToolRunsLoading ? "刷新中..." : "刷新历史" }}
          </button>
        </div>
        <p v-if="agentToolRunsError" class="status-line error">{{ agentToolRunsError }}</p>
        <ul v-if="agentToolRuns.length" class="tool-runs">
          <li v-for="run in agentToolRuns" :key="run.id">
            <span>{{ run.tool_name }} / {{ run.status }}{{ run.arguments?.query ? ` / ${run.arguments.query}` : "" }}{{ run.error ? ` / ${run.error}` : "" }}</span>
            <button type="button" @click="$emit('select-agent-tool-run', run.id)">查看详情</button>
          </li>
        </ul>
        <p v-else class="muted-line">暂无工具运行历史</p>
      </section>

      <section>
        <p class="section-kicker">工具运行详情</p>
        <p v-if="agentToolDetailLoading" class="status-line">正在读取工具运行详情...</p>
        <p v-if="agentToolDetailError" class="status-line error">{{ agentToolDetailError }}</p>
        <pre class="answer compact-answer">{{ formatToolRunDetail(selectedAgentToolRun) }}</pre>
      </section>
    </div>
  </section>
</template>

<script setup>
import { ref } from "vue";

const props = defineProps({
  selectedProjectId: {
    type: String,
    required: true,
  },
  agentTools: {
    type: Array,
    default: () => [],
  },
  agentToolsLoading: {
    type: Boolean,
    default: false,
  },
  agentToolsError: {
    type: String,
    default: "",
  },
  agentToolRuns: {
    type: Array,
    default: () => [],
  },
  agentToolRunsLoading: {
    type: Boolean,
    default: false,
  },
  agentToolRunsError: {
    type: String,
    default: "",
  },
  selectedAgentToolRun: {
    type: Object,
    default: null,
  },
  agentToolResult: {
    type: Object,
    default: null,
  },
  agentToolStatus: {
    type: String,
    default: "",
  },
  agentToolError: {
    type: String,
    default: "",
  },
  agentToolSubmittingName: {
    type: String,
    default: "",
  },
  agentToolDetailLoading: {
    type: Boolean,
    default: false,
  },
  agentToolDetailError: {
    type: String,
    default: "",
  },
});

const emit = defineEmits(["load-agent-tools", "run-agent-tool", "load-agent-tool-runs", "select-agent-tool-run"]);

const sourceQuery = ref("");

function runProjectOverview() {
  emit("run-agent-tool", {
    toolName: "project_overview",
    argumentsPayload: {},
  });
}

function runSearchSources() {
  emit("run-agent-tool", {
    toolName: "search_sources",
    argumentsPayload: {
      query: sourceQuery.value.trim(),
    },
  });
}

function runListedTool(tool) {
  if (tool.name === "search_sources") {
    runSearchSources();
    return;
  }
  emit("run-agent-tool", {
    toolName: tool.name,
    argumentsPayload: {},
  });
}

function formatToolParameters(tool) {
  const parameters = tool.parameters_schema || tool.parameters || tool.arguments || {};
  if (parameters.properties && typeof parameters.properties === "object") {
    const required = Array.isArray(parameters.required) ? parameters.required : [];
    const entries = Object.entries(parameters.properties);
    if (entries.length === 0) {
      return "无参数";
    }
    return entries.map(([name, value]) => `${name}: ${value.description || value.type || "参数"}${required.includes(name) ? "，必填" : ""}`).join("；");
  }
  const entries = Object.entries(parameters);
  return entries.length ? entries.map(([name, value]) => `${name}: ${String(value)}`).join("，") : "无参数";
}

function formatToolScenarios(tool) {
  const scenarios = tool.use_cases || tool.scenarios || [];
  return Array.isArray(scenarios) ? scenarios.join("，") : String(scenarios || tool.description || "参考工具说明");
}

function formatToolResult(data) {
  if (!data) {
    return "暂无工具结果";
  }
  const result = data.result || {};
  const run = data.run || {};
  if (run.tool_name === "search_sources") {
    const hits = Array.isArray(result.hits) ? result.hits : [];
    return [
      `工具：${run.tool_name}`,
      `运行 ID：${run.id || ""}`,
      `状态：${run.status || ""}`,
      `查询：${result.query || ""}`,
      `命中：${result.hit_count ?? hits.length}`,
      ...hits.map((hit, index) => `${index + 1}. ${hit.path || "未知来源"}：${hit.snippet || "无片段预览"}`),
    ].join("\n");
  }
  return [
    `工具：${run.tool_name || "project_overview"}`,
    `运行 ID：${run.id || ""}`,
    `状态：${run.status || "success"}`,
    `项目：${result.project_name || "未知"}`,
    `文档：${result.document_count ?? 0}`,
    `分块：${result.chunk_count ?? 0}`,
    `向量：${result.vector_count ?? 0}`,
    `对话：${result.chat_message_count ?? 0}`,
  ].join("\n");
}

function formatToolRunDetail(run) {
  if (!run) {
    return "请选择一条工具运行查看详情";
  }
  return [
    `工具：${run.tool_name || ""}`,
    `状态：${run.status || ""}`,
    `时间：${run.created_at || ""}`,
    `arguments：${JSON.stringify(run.arguments || {}, null, 2)}`,
    `result：${JSON.stringify(run.result || {}, null, 2)}`,
    `error：${run.error || "无"}`,
  ].join("\n");
}
</script>

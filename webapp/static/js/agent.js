import { apiGet, apiPost } from "./api.js";
import { state } from "./state.js";

export async function listAgentTools() {
  return apiGet("/api/agent/tools");
}

export async function listAgentToolRuns() {
  if (!state.selectedProjectId) {
    return { runs: [] };
  }
  return apiGet(`/api/agent/tools/runs?project_id=${encodeURIComponent(state.selectedProjectId)}`);
}

export async function getAgentToolRunDetail(runId) {
  return apiGet(`/api/agent/tools/runs/detail?run_id=${encodeURIComponent(runId)}`);
}

export async function runAgentTool(toolName, argumentsPayload = {}) {
  if (!state.selectedProjectId) {
    throw new Error("请先创建或选择项目空间");
  }
  return apiPost("/api/agent/tools/run", {
    project_id: state.selectedProjectId,
    tool: toolName,
    arguments: argumentsPayload,
  });
}

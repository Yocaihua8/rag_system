import { apiGet, apiPost } from "./client.js";

export async function listAgentTools() {
  const data = await apiGet("/api/agent/tools");
  return data.tools || [];
}

export async function listAgentToolRuns(projectId) {
  if (!projectId) {
    throw new Error("请先创建或选择项目空间");
  }
  const data = await apiGet(`/api/agent/tools/runs?project_id=${encodeURIComponent(projectId)}`);
  return data.runs || [];
}

export async function getAgentToolRunDetail(runId) {
  if (!runId) {
    throw new Error("请选择工具运行记录");
  }
  const data = await apiGet(`/api/agent/tools/runs/detail?run_id=${encodeURIComponent(runId)}`);
  return data.run || null;
}

export async function runAgentTool({ projectId, toolName, argumentsPayload = {} }) {
  if (!projectId) {
    throw new Error("请先创建或选择项目空间");
  }
  if (!toolName) {
    throw new Error("请选择只读工具");
  }
  return apiPost("/api/agent/tools/run", {
    project_id: projectId,
    tool: toolName,
    arguments: argumentsPayload,
  });
}

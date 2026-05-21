import { apiPost } from "./api.js";
import { state } from "./state.js";

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

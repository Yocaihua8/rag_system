import { apiPost } from "./client.js";

export async function runSearchDebug({ projectId, query, topK = 5, minScore = 0, useKeyword = true, useVector = true }) {
  const trimmedQuery = (query || "").trim();
  if (!projectId) {
    throw new Error("请先创建或选择项目空间");
  }
  if (!trimmedQuery) {
    throw new Error("请输入检索诊断查询");
  }
  return apiPost("/api/search/debug", {
    project_id: projectId,
    query: trimmedQuery,
    top_k: Number(topK),
    min_score: Number(minScore),
    use_keyword: Boolean(useKeyword),
    use_vector: Boolean(useVector),
  });
}

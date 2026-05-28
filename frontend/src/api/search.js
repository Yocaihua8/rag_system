import { apiGet, apiPost } from "./client.js";

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

export async function saveRetrievalReview({ projectId, query, note = "", topK = 5, minScore = 0, useKeyword = true, useVector = true }) {
  const trimmedQuery = (query || "").trim();
  if (!projectId) {
    throw new Error("请先创建或选择项目空间");
  }
  if (!trimmedQuery) {
    throw new Error("请输入检索复盘查询");
  }
  const data = await apiPost("/api/retrieval/reviews", {
    project_id: projectId,
    query: trimmedQuery,
    note,
    top_k: Number(topK),
    min_score: Number(minScore),
    use_keyword: Boolean(useKeyword),
    use_vector: Boolean(useVector),
  });
  return data.review || null;
}

export async function listRetrievalReviews(projectId) {
  if (!projectId) {
    return [];
  }
  const data = await apiGet(`/api/retrieval/reviews?project_id=${encodeURIComponent(projectId)}`);
  return data.reviews || [];
}

export async function getRetrievalReviewDetail(reviewId) {
  if (!reviewId) {
    throw new Error("请选择检索复盘记录");
  }
  const data = await apiGet(`/api/retrieval/reviews/detail?review_id=${encodeURIComponent(reviewId)}`);
  return data.review || null;
}

export async function deleteRetrievalReview(reviewId) {
  if (!reviewId) {
    throw new Error("请选择检索复盘记录");
  }
  const data = await apiPost("/api/retrieval/reviews/delete", {
    review_id: reviewId,
  });
  return data.reviews || [];
}

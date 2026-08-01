import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  analyzeCoachProject,
  answerCoachAssessment,
  confirmLearningPlan,
  generateLearningPlan,
  getCoachCoverage,
  getCoachKnowledgePoints,
  getCoachOverview,
  getCoachSkills,
  getCurrentLearningPlan,
  startCoachAssessment,
  updateLearningPlan,
} from "./coach.js";

function jsonResponse(data, init = {}) {
  return new Response(JSON.stringify(data), {
    status: init.status || 200,
    headers: { "Content-Type": "application/json" },
  });
}

function postBodyAt(index) {
  return JSON.parse(fetch.mock.calls[index][1].body);
}

describe("coach api helpers", () => {
  beforeEach(() => {
    globalThis.fetch = vi.fn().mockResolvedValue(jsonResponse({}));
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("normalizes project ids for analysis and all coach views", async () => {
    fetch
      .mockResolvedValueOnce(jsonResponse({ analysis: { id: "a1" } }))
      .mockResolvedValueOnce(jsonResponse({ overview: { id: "o1" } }))
      .mockResolvedValueOnce(jsonResponse({ knowledge_points: { items: [] } }))
      .mockResolvedValueOnce(jsonResponse({ skills: { items: [] } }))
      .mockResolvedValueOnce(jsonResponse({ coverage: { summary: {} } }));

    await expect(analyzeCoachProject("  project / 1  ")).resolves.toEqual({ id: "a1" });
    expect(postBodyAt(0)).toEqual({ project_id: "project / 1" });

    await expect(getCoachOverview(" project / 1 ")).resolves.toEqual({ id: "o1" });
    await expect(getCoachKnowledgePoints(" project / 1 ")).resolves.toEqual({ items: [] });
    await expect(getCoachSkills(" project / 1 ")).resolves.toEqual({ items: [] });
    await expect(getCoachCoverage(" project / 1 ")).resolves.toEqual({ summary: {} });
    expect(fetch.mock.calls.slice(1).map(([path]) => path)).toEqual([
      "http://127.0.0.1:8765/api/coach/overview?project_id=project+%2F+1",
      "http://127.0.0.1:8765/api/coach/knowledge-points?project_id=project+%2F+1",
      "http://127.0.0.1:8765/api/coach/skills?project_id=project+%2F+1",
      "http://127.0.0.1:8765/api/coach/coverage?project_id=project+%2F+1",
    ]);
  });

  it("starts, resumes, and answers targeted assessments with trimmed values", async () => {
    fetch
      .mockResolvedValueOnce(jsonResponse({ session: { id: "s1" } }))
      .mockResolvedValueOnce(jsonResponse({ session: { id: "s1", resumed: true } }))
      .mockResolvedValueOnce(jsonResponse({ result: { status: "mastered" } }));

    await expect(startCoachAssessment({
      projectId: " p1 ",
      targetType: " knowledge_point ",
      targetId: " kp1 ",
    })).resolves.toEqual({ id: "s1" });
    expect(postBodyAt(0)).toEqual({
      project_id: "p1",
      restart: false,
      target_type: "knowledge_point",
      target_id: "kp1",
    });

    await startCoachAssessment({ projectId: "p1", sessionId: " s1 ", restart: true });
    expect(postBodyAt(1)).toEqual({
      project_id: "p1",
      restart: true,
      session_id: "s1",
    });

    await expect(answerCoachAssessment({
      projectId: " p1 ",
      sessionId: " s1 ",
      questionId: " q1 ",
      answer: "  项目入口在 app.py  ",
      evaluationMode: " rule ",
    })).resolves.toEqual({ result: { status: "mastered" } });
    expect(postBodyAt(2)).toEqual({
      project_id: "p1",
      session_id: "s1",
      question_id: "q1",
      answer: "项目入口在 app.py",
      evaluation_mode: "rule",
    });
  });

  it("maps learning plan edits, progress, confirmation, and current query", async () => {
    fetch
      .mockResolvedValueOnce(jsonResponse({ plan: { id: "plan1" } }))
      .mockResolvedValueOnce(jsonResponse({ current: { draft: { id: "plan1" } } }))
      .mockResolvedValueOnce(jsonResponse({ plan: { id: "plan1", revision: 2 } }))
      .mockResolvedValueOnce(jsonResponse({ plan: { id: "plan1", status: "confirmed" } }))
      .mockResolvedValueOnce(jsonResponse({ plan: { id: "plan1", status: "confirmed" } }));

    await generateLearningPlan({ projectId: " p1 ", maxItems: "6" });
    expect(postBodyAt(0)).toEqual({ project_id: "p1", max_items: 6 });

    await expect(getCurrentLearningPlan(" p1 ")).resolves.toEqual({ draft: { id: "plan1" } });
    expect(fetch.mock.calls[1][0]).toBe("http://127.0.0.1:8765/api/coach/learning-plans/current?project_id=p1");

    await updateLearningPlan({
      projectId: "p1",
      planId: " plan1 ",
      items: [{ stable_key: "i1" }],
      expectedRevision: 1,
      expectedItemsHash: " items ",
    });
    expect(postBodyAt(2)).toEqual({
      project_id: "p1",
      plan_id: "plan1",
      items: [{ stable_key: "i1" }],
      expected_revision: 1,
      expected_items_hash: "items",
    });

    await updateLearningPlan({
      projectId: "p1",
      planId: " plan1 ",
      itemStatuses: { i1: "done" },
      expectedProgressHash: " progress ",
    });
    expect(postBodyAt(3)).toEqual({
      project_id: "p1",
      plan_id: "plan1",
      item_statuses: { i1: "done" },
      expected_progress_hash: "progress",
    });

    await confirmLearningPlan({
      projectId: "p1",
      planId: " plan1 ",
      expectedRevision: 2,
      expectedItemsHash: " confirmed ",
    });
    expect(postBodyAt(4)).toEqual({
      project_id: "p1",
      plan_id: "plan1",
      expected_revision: 2,
      expected_items_hash: "confirmed",
    });
  });

  it("validates required UI state and leaves API errors to the shared client", async () => {
    await expect(analyzeCoachProject(" ")).rejects.toThrow("请先创建或选择项目空间");
    await expect(answerCoachAssessment({
      projectId: "p1",
      sessionId: "s1",
      questionId: "q1",
      answer: " ",
    })).rejects.toThrow("请输入评估回答");
    await expect(updateLearningPlan({
      projectId: "p1",
      planId: "plan1",
    })).rejects.toThrow("请选择编辑计划内容或更新任务进度");
    await expect(updateLearningPlan({
      projectId: "p1",
      planId: "plan1",
      items: [],
      itemStatuses: {},
    })).rejects.toThrow("请选择编辑计划内容或更新任务进度");

    fetch.mockResolvedValueOnce(jsonResponse({ error: "analysis_stale" }, { status: 409 }));
    await expect(generateLearningPlan({ projectId: "p1" })).rejects.toThrow("analysis_stale");
  });
});

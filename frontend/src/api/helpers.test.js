import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { runAgentTool, listAgentTools } from "./agent.js";
import { askQuestion, compareAnswers, submitAnswerFeedback } from "./answer.js";
import { loadAssessmentLibrary, startAssessmentSession, submitAssessmentAnswer } from "./assessment.js";
import {
  addDocumentToCollection,
  createDocumentCollection,
  listDocumentCollections,
} from "./document-collections.js";
import { deleteDocument, getDocument, listDocuments } from "./documents.js";
import {
  importBrowserFiles,
  importGithubRepo,
  importPlainTextNote,
  importUrlExcerpt,
  previewProjectImport,
} from "./imports.js";
import { getOllamaStatus, pullOllamaModel } from "./ollama.js";
import {
  createProject,
  getRetrievalSettings,
  loadProjects,
  saveRetrievalSettings,
  selectProject,
} from "./projects.js";
import { deleteRetrievalReview, listRetrievalReviews, runSearchDebug } from "./search.js";
import {
  listPromptPresets,
  saveLlmSettings,
  saveModelProfile,
  savePromptPreset,
  setDefaultPromptPreset,
} from "./settings.js";
import { appState } from "../state/app-state.js";

function jsonResponse(data, init = {}) {
  return new Response(JSON.stringify(data), {
    status: init.status || 200,
    headers: { "Content-Type": "application/json" },
  });
}

function postBodyAt(callIndex = 0) {
  return JSON.parse(fetch.mock.calls[callIndex][1].body);
}

describe("frontend api helpers", () => {
  beforeEach(() => {
    localStorage.clear();
    appState.projects = [];
    appState.selectedProjectId = "";
    globalThis.fetch = vi.fn().mockResolvedValue(jsonResponse({}));
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("project helpers restore valid local selection and persist newly created projects", async () => {
    localStorage.setItem("knowledge-island:selected-project-id", "p2");
    fetch
      .mockResolvedValueOnce(jsonResponse({ projects: [{ id: "p1", name: "一" }, { id: "p2", name: "二" }] }))
      .mockResolvedValueOnce(jsonResponse({ project: { id: "p3", name: "三" } }));

    await expect(loadProjects()).resolves.toHaveLength(2);
    expect(appState.selectedProjectId).toBe("p2");

    await expect(createProject({ name: "三", path: "E:/Code/demo" })).resolves.toEqual({ id: "p3", name: "三" });
    expect(fetch.mock.calls[1][0]).toBe("/api/projects");
    expect(postBodyAt(1)).toEqual({ name: "三", path: "E:/Code/demo" });
    expect(appState.selectedProjectId).toBe("p3");
    expect(localStorage.getItem("knowledge-island:selected-project-id")).toBe("p3");
  });

  it("retrieval setting helpers encode project ids and coerce saved values", async () => {
    fetch
      .mockResolvedValueOnce(jsonResponse({ settings: { top_k: 8 } }))
      .mockResolvedValueOnce(jsonResponse({ settings: { top_k: 3, min_score: 0.25 } }));

    await expect(getRetrievalSettings("项目 1")).resolves.toEqual({ top_k: 8 });
    expect(fetch.mock.calls[0][0]).toBe("/api/projects/retrieval-settings?project_id=%E9%A1%B9%E7%9B%AE%201");

    await expect(saveRetrievalSettings({
      projectId: "p1",
      topK: "3",
      minScore: "0.25",
      useKeyword: 1,
      useVector: "",
    })).resolves.toEqual({ top_k: 3, min_score: 0.25 });
    expect(postBodyAt(1)).toEqual({
      project_id: "p1",
      top_k: 3,
      min_score: 0.25,
      use_keyword: true,
      use_vector: false,
    });
  });

  it("answer helpers trim questions, include optional context, and validate required state", async () => {
    fetch
      .mockResolvedValueOnce(jsonResponse({ answer: "ok" }))
      .mockResolvedValueOnce(jsonResponse({ comparison: [] }))
      .mockResolvedValueOnce(jsonResponse({ saved: true }));

    await expect(askQuestion({
      projectId: "p1",
      question: "  什么是默认入口？ ",
      toolRunId: "run-1",
      parentMessageId: "m1",
    })).resolves.toEqual({ answer: "ok" });
    expect(postBodyAt(0)).toEqual({
      project_id: "p1",
      question: "什么是默认入口？",
      tool_run_id: "run-1",
      parent_message_id: "m1",
    });

    await expect(compareAnswers({ projectId: "p1", question: "Q", profileIds: ["a", "b"] })).resolves.toEqual({
      comparison: [],
    });
    expect(fetch.mock.calls[1][0]).toBe("/api/answer/compare");

    await expect(submitAnswerFeedback({ projectId: "p1", messageId: "m1", rating: "useful" })).resolves.toEqual({
      saved: true,
    });
    await expect(askQuestion({ projectId: "", question: "Q" })).rejects.toThrow("请先创建或选择项目空间");
    await expect(compareAnswers({ projectId: "p1", question: "Q", profileIds: ["a", "a"] })).rejects.toThrow(
      "请选择 2 个模型 Profile",
    );
  });

  it("search helpers post normalized debug/review payloads and return safe empty lists without a project", async () => {
    fetch
      .mockResolvedValueOnce(jsonResponse({ hits: [] }))
      .mockResolvedValueOnce(jsonResponse({ reviews: [{ id: "r1" }] }));

    await expect(runSearchDebug({
      projectId: "p1",
      query: "  chunk ",
      topK: "10",
      minScore: "0.5",
      useKeyword: "",
      useVector: 1,
    })).resolves.toEqual({ hits: [] });
    expect(postBodyAt(0)).toEqual({
      project_id: "p1",
      query: "chunk",
      top_k: 10,
      min_score: 0.5,
      use_keyword: false,
      use_vector: true,
    });

    await expect(listRetrievalReviews("")).resolves.toEqual([]);
    await expect(deleteRetrievalReview("r1")).resolves.toEqual([{ id: "r1" }]);
    expect(fetch.mock.calls[1][0]).toBe("/api/retrieval/reviews/delete");
  });

  it("document helpers build read/delete routes and skip empty project list requests", async () => {
    fetch
      .mockResolvedValueOnce(jsonResponse({ documents: [{ id: "d1" }] }))
      .mockResolvedValueOnce(jsonResponse({ document: { id: "d1" } }))
      .mockResolvedValueOnce(jsonResponse({ ok: true }));

    await expect(listDocuments("")).resolves.toEqual([]);
    await expect(listDocuments("p 1", "uncategorized")).resolves.toEqual([{ id: "d1" }]);
    expect(fetch.mock.calls[0][0]).toBe("/api/documents?project_id=p+1&collection_id=uncategorized");

    await expect(getDocument("doc/1")).resolves.toEqual({ id: "d1" });
    expect(fetch.mock.calls[1][0]).toBe("/api/document?document_id=doc%2F1");

    await expect(deleteDocument("d1")).resolves.toEqual({ ok: true });
    expect(postBodyAt(2)).toEqual({ document_id: "d1" });
  });

  it("document collection helpers validate selections and post normalized payloads", async () => {
    fetch
      .mockResolvedValueOnce(jsonResponse({ collections: [{ id: "c1" }] }))
      .mockResolvedValueOnce(jsonResponse({ collection: { id: "c2" } }))
      .mockResolvedValueOnce(jsonResponse({ ok: true }));

    await expect(listDocumentCollections("p1")).resolves.toEqual([{ id: "c1" }]);
    expect(fetch.mock.calls[0][0]).toBe("/api/document-collections?project_id=p1");

    await expect(createDocumentCollection({ projectId: "p1", name: "  资料 " })).resolves.toEqual({
      collection: { id: "c2" },
    });
    expect(postBodyAt(1)).toEqual({ project_id: "p1", name: "资料" });

    await expect(addDocumentToCollection({ collectionId: "c1", documentId: "d1" })).resolves.toEqual({ ok: true });
    expect(postBodyAt(2)).toEqual({ collection_id: "c1", document_ids: ["d1"] });
    await expect(createDocumentCollection({ projectId: "p1", name: " " })).rejects.toThrow("请输入文档集合名称");
  });

  it("import helpers trim text payloads and transform browser files", async () => {
    fetch
      .mockResolvedValueOnce(jsonResponse({ imported: true }))
      .mockResolvedValueOnce(jsonResponse({ imported: true }))
      .mockResolvedValueOnce(jsonResponse({ preview: { importable: 1 } }))
      .mockResolvedValueOnce(jsonResponse({ uploaded: true }))
      .mockResolvedValueOnce(jsonResponse({ queued: true }));

    await importPlainTextNote({ projectId: "p1", title: "  会议 ", content: "  纪要 " });
    expect(postBodyAt(0)).toEqual({ project_id: "p1", title: "会议", content: "纪要" });

    await importUrlExcerpt({ projectId: "p1", url: " https://example.test ", title: " T ", content: " C " });
    expect(postBodyAt(1)).toEqual({
      project_id: "p1",
      url: "https://example.test",
      title: "T",
      content: "C",
    });

    await expect(previewProjectImport({ projectId: "p1" })).resolves.toEqual({ importable: 1 });
    expect(fetch.mock.calls[2][0]).toBe("/api/import/preview?project_id=p1");

    const textFile = new File(["hello"], "note.txt", { type: "text/plain" });
    const pdfFile = new File([new Uint8Array([80, 68, 70])], "paper.pdf", { type: "application/pdf" });
    await importBrowserFiles({ projectId: "", files: [textFile, pdfFile] });
    expect(postBodyAt(3)).toEqual({
      source_type: "file_upload",
      project_name: "browser-upload",
      files: [
        { relative_path: "note.txt", content: "hello" },
        { relative_path: "paper.pdf", content_base64: "UERG", size: 3 },
      ],
    });

    await expect(importGithubRepo({ repoUrl: " https://github.com/acme/demo ", branch: " main " })).resolves.toEqual({
      queued: true,
    });
    expect(postBodyAt(4)).toEqual({
      repo_url: "https://github.com/acme/demo",
      branch: "main",
      project_name: "",
    });
  });

  it("settings helpers map UI field names to API payloads", async () => {
    fetch
      .mockResolvedValueOnce(jsonResponse({ settings: { provider: "api" } }))
      .mockResolvedValueOnce(jsonResponse({ profile: { id: "m1" } }))
      .mockResolvedValueOnce(jsonResponse({ preset: { id: "pr1" } }))
      .mockResolvedValueOnce(jsonResponse({ ok: true }));

    await expect(saveLlmSettings({
      provider: "api",
      apiBase: "https://api.example.test/v1",
      model: "demo",
      apiKey: "",
    })).resolves.toEqual({ provider: "api" });
    expect(postBodyAt(0)).toEqual({
      provider: "api",
      api_base: "https://api.example.test/v1",
      model: "demo",
      api_key: "",
    });

    await expect(saveModelProfile({
      name: "  DeepSeek ",
      provider: "api",
      apiBase: "https://api.deepseek.com/v1",
      model: " deepseek-chat ",
      temperature: 0.2,
      maxTokens: 800,
      apiKeyRef: "env:RAG_LLM_API_KEY",
    })).resolves.toEqual({ profile: { id: "m1" } });
    expect(fetch.mock.calls[1][0]).toBe("/api/model-profiles");
    expect(postBodyAt(1).name).toBe("DeepSeek");
    expect(postBodyAt(1).model).toBe("deepseek-chat");

    await expect(savePromptPreset({
      projectId: "p1",
      name: "  代码解释 ",
      description: " desc ",
      systemPrompt: " prompt ",
      answerFormat: " markdown ",
    })).resolves.toEqual({ preset: { id: "pr1" } });
    expect(postBodyAt(2)).toEqual({
      project_id: "p1",
      preset_id: "",
      name: "代码解释",
      description: "desc",
      system_prompt: "prompt",
      answer_format: "markdown",
    });

    await expect(setDefaultPromptPreset({ projectId: "p1", presetId: "" })).resolves.toEqual({ ok: true });
    await expect(listPromptPresets("")).rejects.toThrow("请先创建或选择项目空间");
  });

  it("agent, assessment, and ollama helpers keep validation in front of requests", async () => {
    fetch
      .mockResolvedValueOnce(jsonResponse({ tools: [{ name: "search_sources" }] }))
      .mockResolvedValueOnce(jsonResponse({ run: { id: "run1" } }))
      .mockResolvedValueOnce(jsonResponse({ session: { id: "s1" } }))
      .mockResolvedValueOnce(jsonResponse({ result: { status: "已掌握" } }))
      .mockResolvedValueOnce(jsonResponse({ library: { total: 1 } }))
      .mockResolvedValueOnce(jsonResponse({ running: true }));

    await expect(listAgentTools()).resolves.toEqual([{ name: "search_sources" }]);
    await expect(runAgentTool({ projectId: "p1", toolName: "search_sources", argumentsPayload: { query: "RAG" } })).resolves.toEqual({
      run: { id: "run1" },
    });
    expect(postBodyAt(1)).toEqual({
      project_id: "p1",
      tool: "search_sources",
      arguments: { query: "RAG" },
    });

    await expect(startAssessmentSession("p1")).resolves.toEqual({ session: { id: "s1" } });
    await expect(submitAssessmentAnswer({ projectId: "p1", question: { id: "q1" }, answer: "  答案 " })).resolves.toEqual({
      result: { status: "已掌握" },
    });
    expect(postBodyAt(3)).toEqual({
      project_id: "p1",
      question: { id: "q1" },
      answer: "答案",
    });
    await expect(loadAssessmentLibrary("p1")).resolves.toEqual({ total: 1 });

    await expect(getOllamaStatus()).resolves.toEqual({ running: true });
    await expect(pullOllamaModel({ model: "" })).rejects.toThrow("请选择要下载的模型");
    await expect(runAgentTool({ projectId: "p1", toolName: "" })).rejects.toThrow("请选择只读工具");
    selectProject("");
  });
});

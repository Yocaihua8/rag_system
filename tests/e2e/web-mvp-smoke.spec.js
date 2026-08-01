import { expect, test } from "@playwright/test";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";

test("creates a project, imports a note, and answers from local sources", async ({ page }) => {
  const apiBase = process.env.KI_E2E_API_BASE_URL || "http://127.0.0.1:18765";
  const workspaceDir = await fs.mkdtemp(path.join(os.tmpdir(), "knowledge-island-workspace-"));

  await page.goto("/");
  await expect(page.getByRole("navigation", { name: "主导航" })).toBeVisible();

  const createProjectForm = page.locator(".first-run-wizard .project-form");
  await createProjectForm.getByLabel("项目名称").fill("E2E 知识库");
  await createProjectForm.getByLabel("本地目录").fill(workspaceDir);
  await createProjectForm.getByRole("button", { name: "创建知识库" }).click();
  await expect(page.getByText("E2E 知识库").first()).toBeVisible();

  await page.locator('[data-nav-action="library"]').click();
  const libraryModal = page.getByRole("dialog", { name: "管理资料" });
  await expect(libraryModal).toBeVisible();

  const noteCard = libraryModal.locator(".library-import-card").filter({ hasText: "笔记" });
  await noteCard.getByPlaceholder("粘贴一段笔记").fill(
    "知识岛 E2E 测试资料说明：端到端测试应覆盖知识库创建、文本笔记加入和聊天问答。",
  );
  await noteCard.getByRole("button", { name: "加入" }).click();
  await expect(libraryModal.getByText(/文本笔记已导入/)).toBeVisible();

  await libraryModal.getByRole("button", { name: "选择资料" }).click();
  await expect(libraryModal.locator("[data-library-folder-list]")).toBeVisible();
  await expect(libraryModal.locator(".library-document-item")).toHaveCount(1);
  await libraryModal.getByRole("button", { name: /关闭/ }).click();
  await expect(libraryModal).toBeHidden();

  const composer = page.locator(".question-composer");
  await composer.getByLabel("输入问题").fill("端到端测试应覆盖什么？");
  await composer.getByRole("button", { name: "发送" }).click();

  await expect(composer.getByText("回答已生成")).toBeVisible();
  const answerPanel = page.locator(".answer-panel");
  await expect(answerPanel.getByRole("heading", { name: "回答" })).toBeVisible();
  await expect(answerPanel).toContainText("端到端测试");

  await page.locator('[data-evidence-action="toggle"]').click();
  const evidenceDrawer = page.locator(".evidence-drawer");
  await expect(evidenceDrawer.getByRole("heading", { name: "回答依据" })).toBeVisible();
  await expect(evidenceDrawer).toContainText("端到端测试");

  const projectsResponsePromise = page.waitForResponse(
    (response) => response.url() === `${apiBase}/api/projects` && response.request().method() === "GET",
  );
  const projects = await page.evaluate(async (baseURL) => {
    const response = await fetch(`${baseURL}/api/projects`);
    if (!response.ok) {
      throw new Error(`projects request failed: ${response.status}`);
    }
    return response.json();
  }, apiBase);
  const projectsResponse = await projectsResponsePromise;
  expect(await projectsResponse.headerValue("Access-Control-Allow-Origin")).toBe(
    "http://127.0.0.1:4173",
  );
  const projectId = projects.projects[0].id;

  const streamResult = await page.evaluate(
    ({ baseURL, selectedProjectId }) => new Promise((resolve, reject) => {
      const query = new URLSearchParams({
        project_id: selectedProjectId,
        question: "端到端测试资料说明了什么？",
      });
      const source = new EventSource(`${baseURL}/api/answer/stream?${query.toString()}`);
      const timeout = setTimeout(() => {
        source.close();
        reject(new Error("SSE timeout"));
      }, 15_000);
      source.addEventListener("done", (event) => {
        clearTimeout(timeout);
        source.close();
        resolve(JSON.parse(event.data));
      });
      source.addEventListener("answer_error", (event) => {
        clearTimeout(timeout);
        source.close();
        reject(new Error(event.data));
      });
    }),
    { baseURL: apiBase, selectedProjectId: projectId },
  );
  expect(streamResult.answer).toContain("端到端测试");

  const workflow = await page.evaluate(async ({ baseURL, selectedProjectId }) => {
    async function post(pathname, body) {
      const response = await fetch(`${baseURL}${pathname}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(`${pathname} failed: ${response.status} ${JSON.stringify(data)}`);
      }
      return data;
    }

    await post("/api/coach/analyze", { project_id: selectedProjectId });
    const learningPlan = await post("/api/coach/learning-plans/generate", {
      project_id: selectedProjectId,
    });
    const pairing = await post("/api/obsidian/pairing/start", {
      project_id: selectedProjectId,
    });
    const connection = await post("/api/obsidian/pairing/complete", {
      code: pairing.pairing.code,
      vault_id: "e2e-vault",
      vault_name: "E2E Vault",
    });
    const publication = await post("/api/obsidian/publications/preview", {
      project_id: selectedProjectId,
      artifact_types: ["project_understanding"],
    });
    const confirmed = await post("/api/obsidian/publications/confirm", {
      project_id: selectedProjectId,
      publication_id: publication.publication.id,
    });
    return {
      plan: learningPlan.plan,
      connection: connection.connection,
      publication: confirmed.publication,
    };
  }, { baseURL: apiBase, selectedProjectId: projectId });

  expect(workflow.plan.items.length).toBeGreaterThan(0);
  expect(workflow.connection.vault_id).toBe("e2e-vault");
  expect(workflow.publication.status).toBe("queued");
});

import { expect, test } from "@playwright/test";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";

test("creates a project, imports a note, and answers from local sources", async ({ page }) => {
  const workspaceDir = await fs.mkdtemp(path.join(os.tmpdir(), "knowledge-island-workspace-"));

  await page.goto("/");
  await expect(page.getByRole("navigation", { name: "主导航" })).toBeVisible();

  const createProjectForm = page.locator(".first-run-wizard .project-form");
  await createProjectForm.getByLabel("项目名称").fill("E2E 知识库");
  await createProjectForm.getByLabel("本地目录").fill(workspaceDir);
  await createProjectForm.getByRole("button", { name: "创建知识库" }).click();
  await expect(page.getByText("E2E 知识库").first()).toBeVisible();

  await page.getByRole("button", { name: /库/ }).first().click();
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
});

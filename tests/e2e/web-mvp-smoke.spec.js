import { expect, test } from "@playwright/test";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";

test("creates a project, imports a note, and answers from local sources", async ({ page }) => {
  const workspaceDir = await fs.mkdtemp(path.join(os.tmpdir(), "knowledge-island-workspace-"));

  await page.goto("/");
  await expect(page.getByRole("navigation", { name: "主导航" })).toBeVisible();

  await page.getByRole("button", { name: "资料库" }).click();
  await expect(page.locator(".view-panel").getByRole("heading", { name: "资料库" })).toBeVisible();

  const projectPanel = page.locator(".project-space-panel");
  await projectPanel.getByLabel("项目名称").fill("E2E 知识库");
  await projectPanel.getByLabel("本地目录").fill(workspaceDir);
  await projectPanel.getByRole("button", { name: "创建项目空间" }).click();
  await expect(projectPanel.getByText("已创建项目空间：E2E 知识库")).toBeVisible();

  const importPanel = page.locator(".document-import-panel");
  await importPanel.getByLabel("笔记标题").fill("E2E 测试笔记");
  await importPanel
    .getByLabel("笔记正文")
    .fill("知识岛 E2E 测试资料说明：端到端测试应覆盖项目空间创建、文本笔记导入和工作台问答。");
  await importPanel.getByRole("button", { name: "导入文本笔记" }).click();
  await expect(importPanel.getByText("文本笔记已导入")).toBeVisible();

  await page.getByRole("button", { name: "工作台" }).click();
  const composer = page.locator(".question-composer");
  await composer.getByLabel("输入问题").fill("端到端测试应覆盖什么？");
  await composer.getByRole("button", { name: "提问" }).click();

  await expect(composer.getByText("回答已生成")).toBeVisible();
  const answerPanel = page.locator(".answer-panel");
  await expect(answerPanel.getByRole("heading", { name: "回答" })).toBeVisible();
  await expect(answerPanel).toContainText("端到端测试");
  await expect(answerPanel).toContainText("来源");
});

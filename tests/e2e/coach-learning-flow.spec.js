import { expect, test } from "@playwright/test";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";

const apiBase = (
  process.env.KI_E2E_API_BASE_URL || "http://127.0.0.1:18765"
).replace(/\/+$/, "");

async function postJson(request, url, data) {
  const endpoint = `${apiBase}${url}`;
  const response = await request.post(endpoint, { data });
  expect(response.ok(), `${endpoint}: ${await response.text()}`).toBeTruthy();
  return response.json();
}

test("completes a plan-linked SQL learning session with retry and recovery", async ({
  page,
  request,
}) => {
  const workspaceDir = await fs.mkdtemp(
    path.join(os.tmpdir(), "knowledge-island-coach-learning-"),
  );
  await fs.writeFile(
    path.join(workspaceDir, "schema.sql"),
    [
      "CREATE TABLE tasks (",
      "  id INTEGER PRIMARY KEY,",
      "  title TEXT NOT NULL,",
      "  status TEXT",
      ");",
      "",
    ].join("\n"),
    "utf8",
  );

  const created = await postJson(request, "/api/projects", {
    name: "E2E 逐点学习",
    path: workspaceDir,
  });
  const projectId = created.project.id;
  await postJson(request, "/api/import", { project_id: projectId });
  await postJson(request, "/api/coach/analyze", { project_id: projectId });
  const generated = await postJson(
    request,
    "/api/coach/learning-plans/generate",
    { project_id: projectId },
  );
  const learningItem = generated.plan.items.find(
    (item) => item.item_type === "learning",
  );
  expect(learningItem).toBeTruthy();
  await postJson(request, "/api/coach/learning-plans/confirm", {
    project_id: projectId,
    plan_id: generated.plan.id,
    expected_items_hash: generated.plan.items_hash,
  });

  await page.addInitScript((selectedProjectId) => {
    localStorage.setItem(
      "knowledge-island:selected-project-id",
      selectedProjectId,
    );
  }, projectId);
  await page.goto("/");
  await expect(page.getByText("E2E 逐点学习").first()).toBeVisible();
  await page.locator('[data-view-key="learning-plan"]').click();
  await expect(page.getByRole("heading", { name: "当前项目学习计划" })).toBeVisible();
  const confirmedTab = page.locator('[data-learning-plan-tab="confirmed"]');
  if (await confirmedTab.isVisible()) {
    await confirmedTab.click();
  }
  const planItem = page
    .locator(".learning-plan-progress li")
    .filter({ hasText: learningItem.objective });
  await planItem.locator('[data-learning-plan-action="start-learning"]').click();

  const overlay = page.locator("[data-coach-learning-backdrop]");
  await expect(overlay).toBeVisible();
  await expect(overlay).toContainText("知识点 1 /");
  await overlay.locator('[data-coach-learning-action="begin-learning"]').click();
  await overlay.locator('[data-coach-learning-action="begin-question"]').click();
  await expect(overlay.locator(".coach-learning-exercise")).toHaveCount(1);
  await expect(overlay.getByText("样例表").first()).toBeVisible();
  await expect(overlay.getByText("tasks", { exact: true }).first()).toBeVisible();
  await expect(overlay.locator(".coach-learning-fixture table")).toHaveCount(1);

  const answer = overlay.locator('[data-coach-learning-field="answer"]');
  await answer.fill("SELECT id, title FROM tasks");
  await overlay.locator('[data-coach-learning-action="submit"]').evaluate(
    (form) => form.requestSubmit(),
  );
  await expect(overlay).toContainText("得分 0%");
  await expect(overlay).toContainText("结果行与题目要求不一致");
  await expect(overlay.locator('[data-coach-learning-action="retry"]')).toBeVisible();

  await overlay.locator('[data-coach-learning-action="close"]').click();
  await expect(overlay).toBeHidden();
  await page.reload();
  await expect(page.getByText("E2E 逐点学习").first()).toBeVisible();
  const resume = page.locator('[data-composer-action="start-learning"]');
  await expect(resume).toContainText("继续逐点学习");
  await resume.click();
  await expect(overlay).toBeVisible();
  await expect(overlay).toContainText("第 1 次作答");

  await overlay.locator('[data-coach-learning-action="retry"]').click();
  const formattedSql = [
    "SELECT id, title",
    "FROM tasks",
    "WHERE status IS NULL",
  ].join("\n");
  await answer.fill(formattedSql);
  await expect(answer).toHaveValue(formattedSql);
  await overlay.locator('[data-coach-learning-action="submit"]').evaluate(
    (form) => form.requestSubmit(),
  );
  await expect(overlay).toContainText("得分 100%");
  await expect(overlay).toContainText("第 2 次作答");
  await overlay.locator('[data-coach-learning-action="next"]').click();
  await expect(overlay).toContainText("本次逐点学习已完成");

  await overlay.locator('[data-coach-learning-action="close"]').click();
  await page.locator('[data-view-key="learning-plan"]').click();
  await page.locator('[data-learning-plan-action="refresh"]').click();
  await expect(planItem.locator('[data-learning-plan-field="status"]')).toHaveValue(
    "done",
  );
});

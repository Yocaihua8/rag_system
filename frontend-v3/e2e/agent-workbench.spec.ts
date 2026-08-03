import { expect, test } from '@playwright/test'

const projectRoot = process.env.KI_V3_E2E_PROJECT_ROOT
const apiBaseUrl = process.env.KI_V3_E2E_API_BASE_URL

test('creates a real project and restores a completed Agent task after refresh', async ({ page }) => {
  if (!projectRoot || !apiBaseUrl) {
    throw new Error('KI_V3_E2E_PROJECT_ROOT and KI_V3_E2E_API_BASE_URL are required')
  }

  await page.goto('/#/projects')
  const projectsResponse = await page.request.get(`${apiBaseUrl}/projects`)
  const projects = (await projectsResponse.json()).data.items as Array<{ id: string }>
  if (projects.length === 0) {
    await page.getByRole('button', { name: '添加项目' }).click()
    await page.getByLabel('项目名称').fill('E2E 本地项目')
    await page.getByLabel('现有文件夹路径').fill(projectRoot)
    await page.getByRole('button', { name: '确认添加' }).click()
  }
  await expect(page.getByRole('heading', { name: 'E2E 本地项目' })).toBeVisible()

  await page.getByRole('button', { name: '扫描项目资料' }).click()
  await expect(page.getByLabel('已索引资料')).toContainText('README.md')
  await expect(page.getByLabel('已索引资料')).toContainText('src/main.py')
  await expect(page.getByRole('heading', { name: '项目洞察' }).locator('..')).toContainText('已索引文件')
  await page.getByRole('button', { name: '生成资料事实报告' }).click()
  await expect(page.getByRole('heading', { name: '处理完成' })).toBeVisible({ timeout: 30_000 })
  await page.getByRole('button', { name: '查看结果' }).click()
  const sourceFactsDrawer = page.locator('aside[aria-label="详细过程"]')
  await expect(sourceFactsDrawer).toContainText('项目资料事实报告')
  await sourceFactsDrawer.getByRole('button', { name: '导出结果' }).click()
  await expect(sourceFactsDrawer.getByLabel('导出确认')).toContainText('不会修改项目文件，也不能自动撤销')
  await sourceFactsDrawer.getByRole('button', { name: '确认导出' }).click()
  await expect(sourceFactsDrawer).toContainText('已导出')
  await page.goto('/#/projects')
  await expect(page.getByRole('heading', { name: 'E2E 本地项目' })).toBeVisible()
  const selectedProjectResponse = await page.request.get(`${apiBaseUrl}/projects`)
  const selectedProject = ((await selectedProjectResponse.json()).data.items as Array<{ id: string }>)[0]
  if (!selectedProject) throw new Error('E2E project was not created')

  const graph = {
    nodes: [
      { id: 'trigger', type: 'trigger.manual', config: {} },
      { id: 'analyze', type: 'project.analyze', config: { analysis_kind: 'sources' } },
      { id: 'artifact', type: 'artifact.create', config: { format: 'json' } },
      { id: 'respond', type: 'agent.respond', config: {} },
    ],
    edges: [
      { id: 'trigger-analyze', source: 'trigger', source_port: 'out', target: 'analyze', target_port: 'in' },
      { id: 'analyze-artifact', source: 'analyze', source_port: 'out', target: 'artifact', target_port: 'in' },
      { id: 'artifact-respond', source: 'artifact', source_port: 'out', target: 'respond', target_port: 'in' },
    ],
  }
  const workflowResponse = await page.request.post(`${apiBaseUrl}/workflows`, {
    headers: { 'Idempotency-Key': 'e2e-workflow-create' },
    data: { workflow_key: 'project.safe.e2e.v1', name: 'E2E 受限检查', description: '', scope_type: 'global', graph },
  })
  expect(workflowResponse.ok()).toBeTruthy()
  const workflowData = (await workflowResponse.json()).data
  const publishResponse = await page.request.post(`${apiBaseUrl}/workflows/${workflowData.workflow.id}/publish`, {
    headers: { 'Idempotency-Key': 'e2e-workflow-publish' },
    data: { version_id: workflowData.version.id, expected_checksum: workflowData.version.checksum, expected_version: workflowData.workflow.version },
  })
  expect(publishResponse.ok()).toBeTruthy()
  const published = (await publishResponse.json()).data
  const bindResponse = await page.request.post(`${apiBaseUrl}/workflows/${workflowData.workflow.id}/bindings`, {
    headers: { 'Idempotency-Key': 'e2e-workflow-bind' },
    data: { project_id: selectedProject.id, workflow_version_id: workflowData.version.id, expected_workflow_version: published.workflow.version, expected_binding_version: 0 },
  })
  expect(bindResponse.ok()).toBeTruthy()

  await page.getByRole('link', { name: '工作流' }).click()
  await page.getByRole('button', { name: '查看工作流' }).click()
  const composer = page.getByLabel('本次任务')
  await composer.fill('检查 E2E 项目的当前资料')
  await page.getByRole('button', { name: '启动此工作流' }).click()

  await expect(page.getByRole('heading', { name: '处理完成' })).toBeVisible({
    timeout: 30_000,
  })
  await expect(page.locator('.message--assistant')).toHaveCount(1)
  await page.getByRole('button', { name: '查看结果' }).click()
  const detailsDrawer = page.locator('aside[aria-label="详细过程"]')
  await expect(detailsDrawer).toContainText('1 个结果')
  await expect(detailsDrawer).toContainText('文件总数')
  await expect(detailsDrawer).toContainText('README.md')
  await detailsDrawer.getByRole('button', { name: '关闭详细过程' }).click()

  const taskUrl = page.url()
  expect(taskUrl).toContain('#/tasks/')
  await page.reload()
  await expect(page.getByRole('heading', { name: '处理完成' })).toBeVisible({
    timeout: 15_000,
  })
  await expect(page.locator('.message--assistant')).toHaveCount(1)
})

test('shows a persisted approval and requires a second confirmation before resolving it', async ({ page }) => {
  if (!apiBaseUrl) throw new Error('KI_V3_E2E_API_BASE_URL is required')

  const projectsResponse = await page.request.get(`${apiBaseUrl}/projects`)
  const project = ((await projectsResponse.json()).data.items as Array<{ id: string }>)[0]
  if (!project) throw new Error('E2E project fixture was not created')
  const fixtureResponse = await page.request.post(`${apiBaseUrl.replace('/api/v3', '')}/__e2e__/approval`, {
    data: { project_id: project.id },
  })
  expect(fixtureResponse.ok(), await fixtureResponse.text()).toBeTruthy()
  const fixture = await fixtureResponse.json() as { task_id: string; approval_id: string }

  await page.goto(`/#/tasks/${fixture.task_id}`)
  await expect(page.getByRole('heading', { name: '需要你确认一次' })).toBeVisible()
  await expect(page.getByText('github.create_issue')).toBeVisible()
  await expect(page.getByText('owner/e2e-repository')).toBeVisible()
  await page.getByRole('button', { name: '查看并确认' }).click()
  await expect(page.getByRole('heading', { name: '最后确认：执行这项操作？' })).toBeVisible()
  const resolveResponse = page.waitForResponse((response) => response.url().includes(`/approvals/${fixture.approval_id}/resolve`))
  await page.getByRole('button', { name: '确认执行' }).click()
  const resolved = await resolveResponse
  expect(resolved.ok(), await resolved.text()).toBeTruthy()

  await expect.poll(async () => {
    const response = await page.request.get(`${apiBaseUrl}/approvals/${fixture.approval_id}`)
    return (await response.json()).data.approval.status
  }).toBe('approved')
  await expect(page.getByRole('heading', { name: '需要你确认一次' })).not.toBeVisible()
})

test('keeps the task composer reachable at 320 by 560 without horizontal overflow', async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 560 })
  await page.goto('/#/tasks/new')
  await expect(page.locator('.composer-region')).toBeVisible()

  const layout = await page.evaluate(() => {
    const composer = document.querySelector('.composer-region')?.getBoundingClientRect()
    return {
      documentWidth: document.documentElement.scrollWidth,
      viewportWidth: window.innerWidth,
      composerBottom: composer?.bottom ?? Number.POSITIVE_INFINITY,
      composerTop: composer?.top ?? Number.POSITIVE_INFINITY,
    }
  })

  expect(layout.documentWidth).toBeLessThanOrEqual(layout.viewportWidth)
  expect(layout.composerTop).toBeGreaterThanOrEqual(0)
  expect(layout.composerBottom).toBeLessThanOrEqual(560)
  await expect(page.getByRole('navigation', { name: '主导航' })).toBeVisible()
})

test('keeps an offline draft and never submits it automatically', async ({ page, context }) => {
  await page.goto('/#/tasks/new')
  const composer = page.getByLabel('告诉 Agent 你想完成什么')
  await expect(composer).toBeVisible()

  await context.setOffline(true)
  await page.evaluate(() => window.dispatchEvent(new Event('offline')))
  await composer.fill('离线期间只保存这份草稿')
  await expect(page.getByText(/当前离线：可以继续写草稿/)).toBeVisible()
  await expect(page.getByRole('button', { name: '开始处理' })).toBeDisabled()

  await context.setOffline(false)
  await page.evaluate(() => window.dispatchEvent(new Event('online')))
  await expect(composer).toHaveValue('离线期间只保存这份草稿')
  await expect(page).toHaveURL(/#\/tasks\/new$/)
})

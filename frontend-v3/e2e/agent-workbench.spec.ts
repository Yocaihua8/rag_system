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

  await page.getByRole('link', { name: '任务' }).click()
  await page.getByRole('button', { name: /找出问题/ }).click()
  const composer = page.getByLabel('告诉 Agent 你想完成什么')
  await expect(composer).toHaveValue('请检查项目，找出最需要先处理的问题。')
  await expect(page.getByRole('button', { name: '开始处理' })).toBeEnabled()
  await composer.press('Enter')

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

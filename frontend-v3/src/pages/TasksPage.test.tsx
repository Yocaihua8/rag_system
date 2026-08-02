import { cleanup, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { useUiStore } from '../store/uiStore'
import { TasksPage } from './TasksPage'

describe('TasksPage', () => {
  afterEach(() => {
    cleanup()
    useUiStore.setState({ drawer: null })
  })
  it('shows one approval state with a complete impact explanation', () => {
    render(
      <TasksPage
        projectId="project-1"
        projectName="Knowledge Island"
        taskId="task-1"
        status="waiting_approval"
        serviceAvailable
        approval={{ action: '生成报告', target: '项目结果目录', unchanged: '不会修改原资料', undo: '可以删除新报告' }}
      />,
    )

    expect(screen.getByRole('heading', { name: '需要你确认一次' })).toBeInTheDocument()
    expect(screen.getByText('不会修改原资料')).toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: '处理没有完成' })).not.toBeInTheDocument()
  })

  it('explains that task options affect only the current task', async () => {
    const user = userEvent.setup()
    render(<TasksPage projectId="project-1" serviceAvailable />)

    await user.click(screen.getByRole('button', { name: /任务选项/ }))

    expect(screen.getByRole('dialog', { name: '任务选项' })).toHaveTextContent('只影响当前任务')
  })

  it('requires a plain-language confirmation before stopping', async () => {
    const user = userEvent.setup()
    const onStop = vi.fn()
    render(<TasksPage projectId="project-1" status="running" serviceAvailable onStop={onStop} onPause={vi.fn()} />)

    await user.click(screen.getByRole('button', { name: '停止未完成步骤' }))

    expect(screen.getByRole('dialog', { name: '停止未完成步骤？' })).toHaveTextContent('已完成的内容会保留')
    expect(onStop).not.toHaveBeenCalled()
    await user.click(screen.getByRole('button', { name: '确认停止' }))
    expect(onStop).toHaveBeenCalledTimes(1)
  })

  it('requires a second confirmation before approving a write action', async () => {
    const user = userEvent.setup()
    const onApprove = vi.fn()
    render(
      <TasksPage
        projectId="project-1"
        status="waiting_approval"
        serviceAvailable
        approval={{ action: '生成报告', target: '项目结果目录', unchanged: '不会修改原资料', undo: '不能自动撤销' }}
        onApprove={onApprove}
        onReject={vi.fn()}
      />,
    )

    await user.click(screen.getByRole('button', { name: '查看并确认' }))
    expect(onApprove).not.toHaveBeenCalled()
    expect(screen.getByRole('dialog', { name: '最后确认：执行这项操作？' })).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: '确认执行' }))
    expect(onApprove).toHaveBeenCalledTimes(1)
    expect(screen.getByRole('button', { name: '拒绝并停止本次任务（更安全）' })).toBeInTheDocument()
  })

  it('keeps approval confirmation focus inside the dialog and restores it on Escape', async () => {
    const user = userEvent.setup()
    render(
      <TasksPage
        projectId="project-1"
        status="waiting_approval"
        serviceAvailable
        approval={{ action: '生成报告', target: '项目结果目录', unchanged: '不会修改原资料', undo: '不能自动撤销' }}
        onApprove={vi.fn()}
        onReject={vi.fn()}
      />,
    )

    const trigger = screen.getByRole('button', { name: '查看并确认' })
    await user.click(trigger)
    await waitFor(() => expect(screen.getByRole('button', { name: '返回检查（推荐）' })).toHaveFocus())
    await user.keyboard('{Escape}')
    expect(screen.queryByRole('dialog', { name: '最后确认：执行这项操作？' })).not.toBeInTheDocument()
    await waitFor(() => expect(trigger).toHaveFocus())
  })

  it('shows a sync error instead of stacking it with the current run state', () => {
    render(<TasksPage projectId="project-1" status="running" serviceAvailable error="Failed to fetch" />)

    expect(screen.getByRole('heading', { name: '任务暂时没有同步成功' })).toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: '正在处理当前步骤' })).not.toBeInTheDocument()
    expect(screen.queryByRole('list', { name: '任务进度' })).not.toBeInTheDocument()
    expect(screen.getByText('查看技术信息')).toBeInTheDocument()
    expect(screen.getByText('同步异常')).toBeInTheDocument()
  })

  it('keeps a failed command as a notice without replacing the current state', () => {
    render(
      <TasksPage
        projectId="project-1"
        status="running"
        serviceAvailable
        actionNotice="刚才的暂停操作没有完成。已有内容会保留，请手动重试。"
      />,
    )

    expect(screen.getByRole('heading', { name: '正在处理当前步骤' })).toBeInTheDocument()
    expect(screen.getByText(/暂停操作没有完成/)).toBeInTheDocument()
  })

  it('opens the first ready result and renders JSON as readable content', async () => {
    const user = userEvent.setup()
    render(
      <TasksPage
        projectId="project-1"
        status="completed"
        serviceAvailable
        results={[
          { id: 'failed', title: '失败结果', description: '不可查看' },
          { id: 'ready', title: '项目结构检查', description: '结果已准备好' },
        ]}
        artifacts={[
          { id: 'failed', name: '失败结果', status: 'failed', content: '失败' },
          { id: 'ready', name: '项目结构检查', status: 'ready', content: '{"total_files":2}' },
        ]}
        artifactCount={2}
        onViewResult={() => useUiStore.getState().openDrawer('details')}
      />,
    )

    expect(screen.queryByText('不可查看')).not.toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: '查看结果' }))
    const readyResult = screen.getByText('项目结构检查 · 可以查看').closest('details')
    expect(readyResult).toHaveAttribute('open')
    expect(readyResult).toHaveTextContent('文件总数')
    expect(readyResult).toHaveTextContent('2')
    expect(readyResult).toHaveTextContent('查看原始数据')
    expect(screen.getByText(/推荐下一步：先检查结果/)).toBeInTheDocument()
  })

  it('replaces the empty task surface with one clear project action', () => {
    render(<TasksPage />)

    expect(screen.getByRole('heading', { name: '先选择一个项目' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: '添加或选择项目' })).toHaveAttribute('href', '#/projects')
    expect(screen.queryByLabelText('告诉 Agent 你想完成什么')).not.toBeInTheDocument()
  })

  it('uses failure details supplied by the caller and does not invent retry counts', () => {
    render(
      <TasksPage
        projectId="project-1"
        status="failed"
        failure={{
          whatHappened: '项目目录暂时无法读取。',
          dataSafety: '没有修改项目文件。',
          nextStep: '确认目录可用后再试一次。',
        }}
        onRetry={vi.fn()}
      />,
    )

    expect(screen.getByText(/项目目录暂时无法读取/)).toBeInTheDocument()
    expect(screen.getByText(/没有修改项目文件/)).toBeInTheDocument()
    expect(screen.queryByText(/第 1\/2 次/)).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: '重新尝试' })).toBeEnabled()
  })

  it('offers only the safe stop exit when a run needs recovery confirmation', () => {
    const onStop = vi.fn()
    render(<TasksPage projectId="project-1" status="recovery_required" onStop={onStop} />)

    expect(screen.getByRole('heading', { name: '先检查，再继续' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '停止并保留现场' })).toBeEnabled()
    expect(screen.queryByRole('button', { name: '重新尝试' })).not.toBeInTheDocument()
  })

  it('uses a controlled current-task depth before creation', async () => {
    const user = userEvent.setup()
    const onDepthChange = vi.fn()
    render(<TasksPage projectId="project-1" serviceAvailable depth="deep" onDepthChange={onDepthChange} />)

    await user.click(screen.getByRole('button', { name: /任务选项/ }))
    expect(screen.getByLabelText('处理方式')).toHaveValue('deep')
    await user.selectOptions(screen.getByLabelText('处理方式'), 'quick')
    expect(onDepthChange).toHaveBeenCalledWith('quick')
  })
})

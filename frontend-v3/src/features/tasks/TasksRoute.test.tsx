import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'

import { v3Api } from '../../api'
import { useDraftStore } from '../../store/draftStore'
import { useProjectSelectionStore } from '../projects/projectSelectionStore'
import { TasksRoute } from './TasksRoute'

describe('TasksRoute real command wiring', () => {
  beforeEach(() => {
    localStorage.clear()
    sessionStorage.clear()
    useDraftStore.setState({ drafts: {} })
    useProjectSelectionStore.setState({ selectedProjectId: 'project-1' })
    vi.spyOn(v3Api, 'health').mockResolvedValue({
      status: 'ok', data_generation: 'v3', schema_revision: '0001', executor_running: true,
    })
    vi.spyOn(v3Api, 'listProjects').mockResolvedValue({ items: [project()] })
    vi.spyOn(v3Api, 'listTaskMessages').mockResolvedValue({ items: [] })
    vi.spyOn(v3Api, 'listTaskRuns').mockResolvedValue({ items: [] })
  })

  afterEach(() => {
    cleanup()
    vi.restoreAllMocks()
  })

  it('creates task and run from the atomic initial message', async () => {
    const user = userEvent.setup()
    const createTask = vi.spyOn(v3Api, 'createTask').mockResolvedValue({
      task: task(),
      initial_message: message('initial-message', '检查项目'),
      replayed: false,
    })
    const createRun = vi.spyOn(v3Api, 'createRun').mockResolvedValue(runMutation())
    vi.spyOn(v3Api, 'getTask').mockResolvedValue({ task: task() })
    renderRoute('/tasks/new')

    await user.type(screen.getByLabelText('告诉 Agent 你想完成什么'), '检查项目')
    await user.click(screen.getByRole('button', { name: '开始处理' }))

    await waitFor(() => expect(createTask).toHaveBeenCalledTimes(1))
    await waitFor(() => expect(createRun).toHaveBeenCalledTimes(1))
    expect(createRun).toHaveBeenCalledWith(
      'task-1',
      expect.objectContaining({ input_message_id: 'initial-message' }),
      expect.objectContaining({ idempotencyKey: expect.any(String) }),
    )
  })

  it('adds a user message before starting another run for an existing task', async () => {
    const user = userEvent.setup()
    vi.spyOn(v3Api, 'getTask').mockResolvedValue({ task: { ...task(), status: 'completed' } })
    const addMessage = vi.spyOn(v3Api, 'addTaskMessage').mockResolvedValue({
      message: message('follow-up-message', '再检查一次'),
      replayed: false,
    })
    const createRun = vi.spyOn(v3Api, 'createRun').mockResolvedValue(runMutation())
    renderRoute('/tasks/task-1')

    await screen.findByRole('heading', { name: '检查项目' })
    await user.type(screen.getByLabelText('告诉 Agent 你想完成什么'), '再检查一次')
    await user.click(screen.getByRole('button', { name: '开始处理' }))

    await waitFor(() => expect(addMessage).toHaveBeenCalledTimes(1))
    await waitFor(() => expect(createRun).toHaveBeenCalledTimes(1))
    expect(createRun).toHaveBeenCalledWith(
      'task-1',
      expect.objectContaining({ input_message_id: 'follow-up-message' }),
      expect.any(Object),
    )
  })

  it('refreshes canonical messages when the latest run already completed', async () => {
    vi.spyOn(v3Api, 'getTask').mockResolvedValue({ task: { ...task(), status: 'completed' } })
    vi.mocked(v3Api.listTaskRuns).mockResolvedValue({
      items: [{ ...runMutation().run, status: 'completed', finished_at: '2026-08-02T00:00:01Z' }],
    })
    vi.mocked(v3Api.listTaskMessages)
      .mockResolvedValueOnce({ items: [message('initial-message', '检查项目')] })
      .mockResolvedValue({ items: [
        message('initial-message', '检查项目'),
        {
          ...message('agent-message', '检查完成'),
          run_id: 'run-1',
          role: 'agent',
          message_type: 'answer',
        },
      ] })
    vi.spyOn(v3Api, 'listRunSteps').mockResolvedValue({ items: [] })
    vi.spyOn(v3Api, 'listApprovals').mockResolvedValue({ items: [] })
    vi.spyOn(v3Api, 'listArtifacts').mockResolvedValue({ items: [] })

    renderRoute('/tasks/task-1')

    expect(await screen.findByText('检查完成')).toBeInTheDocument()
    expect(vi.mocked(v3Api.listTaskMessages).mock.calls.length).toBeGreaterThanOrEqual(2)
  })

  it('keeps message and run intent keys across refresh after a partial existing-task submission', async () => {
    const content = '再检查一次，不要重复保存'
    let messageSaved = false
    let runStarted = false
    vi.spyOn(v3Api, 'getTask').mockResolvedValue({ task: { ...task(), status: 'completed' } })
    const addMessage = vi.spyOn(v3Api, 'addTaskMessage').mockImplementation(async () => {
      messageSaved = true
      return { message: message('follow-up-message', content), replayed: false }
    })
    const createRun = vi.spyOn(v3Api, 'createRun')
      .mockRejectedValueOnce(new Error('connection lost'))
      .mockImplementationOnce(async () => {
        runStarted = true
        return runMutation()
      })
    vi.mocked(v3Api.listTaskMessages).mockImplementation(async () => ({
      items: messageSaved ? [message('follow-up-message', content)] : [],
    }))
    vi.mocked(v3Api.listTaskRuns).mockImplementation(async () => ({
      items: runStarted ? [runMutation().run] : [],
    }))
    vi.spyOn(v3Api, 'listRunSteps').mockResolvedValue({ items: [] })
    vi.spyOn(v3Api, 'listApprovals').mockResolvedValue({ items: [] })
    vi.spyOn(v3Api, 'listArtifacts').mockResolvedValue({ items: [] })

    const firstView = renderRoute('/tasks/task-1')
    await screen.findByRole('heading', { name: '检查项目' })
    const firstUser = userEvent.setup()
    await firstUser.type(screen.getByLabelText('告诉 Agent 你想完成什么'), content)
    await firstUser.click(screen.getByRole('button', { name: '开始处理' }))

    expect((await screen.findAllByText(/内容已保存，处理尚未启动/)).length).toBeGreaterThan(0)
    await waitFor(() => expect(vi.mocked(v3Api.listTaskMessages).mock.calls.length).toBeGreaterThan(1))
    const firstMessageKey = addMessage.mock.calls[0][2]?.idempotencyKey
    const firstRunKey = createRun.mock.calls[0][2]?.idempotencyKey
    const partialLedger = sessionStorage.getItem('knowledge-island:v3:intent-ledger') ?? ''
    expect(partialLedger).toContain('follow-up-message')
    expect(partialLedger).not.toContain(content)

    firstView.unmount()
    const secondView = renderRoute('/tasks/task-1')
    await screen.findByRole('heading', { name: '检查项目' })
    const secondUser = userEvent.setup()
    await secondUser.click(screen.getByRole('button', { name: '开始处理' }))

    await waitFor(() => expect(createRun).toHaveBeenCalledTimes(2))
    expect(addMessage.mock.calls[1][2]?.idempotencyKey).toBe(firstMessageKey)
    expect(createRun.mock.calls[1][2]?.idempotencyKey).toBe(firstRunKey)
    await waitFor(() => {
      expect(sessionStorage.getItem('knowledge-island:v3:intent-ledger')).toBeNull()
    })
    secondView.unmount()
  })

  it('replays atomic task creation after refresh when the content was saved but the run failed', async () => {
    const content = '检查新项目的风险'
    let taskSaved = false
    let runStarted = false
    const createTask = vi.spyOn(v3Api, 'createTask').mockImplementation(async () => {
      taskSaved = true
      return {
        task: task(),
        initial_message: message('initial-message', content),
        replayed: createTask.mock.calls.length > 1,
      }
    })
    const createRun = vi.spyOn(v3Api, 'createRun')
      .mockRejectedValueOnce(new Error('connection lost'))
      .mockImplementationOnce(async () => {
        runStarted = true
        return runMutation()
      })
    vi.spyOn(v3Api, 'getTask').mockResolvedValue({ task: task() })
    vi.mocked(v3Api.listTaskMessages).mockImplementation(async () => ({
      items: taskSaved ? [message('initial-message', content)] : [],
    }))
    vi.mocked(v3Api.listTaskRuns).mockImplementation(async () => ({
      items: runStarted ? [runMutation().run] : [],
    }))
    vi.spyOn(v3Api, 'listRunSteps').mockResolvedValue({ items: [] })
    vi.spyOn(v3Api, 'listApprovals').mockResolvedValue({ items: [] })
    vi.spyOn(v3Api, 'listArtifacts').mockResolvedValue({ items: [] })

    const firstView = renderRoute('/tasks/new')
    const firstUser = userEvent.setup()
    await firstUser.type(screen.getByLabelText('告诉 Agent 你想完成什么'), content)
    await firstUser.click(screen.getByRole('button', { name: '开始处理' }))

    expect((await screen.findAllByText(/内容已保存，处理尚未启动/)).length).toBeGreaterThan(0)
    const firstCreateKey = createTask.mock.calls[0][1]?.idempotencyKey
    const firstRunKey = createRun.mock.calls[0][2]?.idempotencyKey
    expect(sessionStorage.getItem('knowledge-island:v3:intent-ledger')).not.toContain(content)

    firstView.unmount()
    renderRoute('/tasks/new')
    const secondUser = userEvent.setup()
    await secondUser.click(screen.getByRole('button', { name: '开始处理' }))

    await waitFor(() => expect(createTask).toHaveBeenCalledTimes(2))
    await waitFor(() => expect(createRun).toHaveBeenCalledTimes(2))
    expect(createTask.mock.calls[1][1]?.idempotencyKey).toBe(firstCreateKey)
    expect(createRun.mock.calls[1][2]?.idempotencyKey).toBe(firstRunKey)
  })
})

function renderRoute(initialEntry: string) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[initialEntry]}>
        <Routes>
          <Route path="tasks/new" element={<TasksRoute />} />
          <Route path="tasks/:taskId" element={<TasksRoute />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

function project() {
  return {
    id: 'project-1', name: 'Knowledge Island', root_path: 'E:\\Project', status: 'active' as const,
    version: 1, created_at: '2026-08-02T00:00:00Z', updated_at: '2026-08-02T00:00:00Z',
  }
}

function task() {
  return {
    id: 'task-1', project_id: 'project-1', title: '检查项目', prompt: '检查项目', depth: 'standard' as const,
    status: 'queued' as const, version: 1, created_at: '2026-08-02T00:00:00Z', updated_at: '2026-08-02T00:00:00Z',
  }
}

function message(id: string, content: string) {
  return {
    id, task_id: 'task-1', run_id: null, role: 'user' as const, message_type: 'prompt', content,
    metadata: {}, created_at: '2026-08-02T00:00:00Z',
  }
}

function runMutation() {
  return {
    run: {
      id: 'run-1', task_id: 'task-1', project_id: 'project-1', workflow_version_id: null,
      workflow_key: 'project.inspect.v1', workflow_version: 2, workflow_checksum: 'a'.repeat(64),
      depth: 'standard' as const, status: 'queued' as const, priority: 0, attempt_no: 1,
      retry_of_run_id: null, version: 1, queued_at: '2026-08-02T00:00:00Z', started_at: null,
      finished_at: null, paused_at: null, cancel_requested_at: null, lease_owner: '', lease_expires_at: null,
      error_code: '', error_message: '', result: {}, created_at: '2026-08-02T00:00:00Z', updated_at: '2026-08-02T00:00:00Z',
    },
    steps: [],
    event: { id: 'event-1', run_id: 'run-1', step_id: null, sequence: 1, event_type: 'run.queued', event_schema_version: 1, payload: {}, created_at: '2026-08-02T00:00:00Z' },
    project_id: 'project-1', replayed: false,
  }
}

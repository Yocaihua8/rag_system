import { useEffect, useMemo, useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient, type QueryClient } from '@tanstack/react-query'
import { useNavigate, useParams } from 'react-router-dom'

import {
  ApiError,
  DEFAULT_V3_API_BASE_URL,
  assistantMessageReducer,
  initialAssistantMessageState,
  normalizeV3ApiBaseUrl,
  subscribeRunEvents,
  v3Api,
  v3QueryKeys,
  type AgentEvent,
} from '../../api'
import type { components } from '../../api/generated/schema'
import type { ApprovalSummary, TaskMessage, TaskStatus } from '../../components/taskTypes'
import { TasksPage } from '../../pages/TasksPage'
import { usePreferencesStore } from '../../store/preferencesStore'
import { useUiStore } from '../../store/uiStore'
import { useProjects } from '../projects/queries'
import { useProjectSelectionStore } from '../projects/projectSelectionStore'
import { digestIntentFingerprint, useIntentKeys } from '../shared/useIntentKeys'
import { useOnlineStatus } from '../shared/useOnlineStatus'

type Schemas = components['schemas']
type RunResource = Schemas['RunResource']

export function TasksRoute() {
  const { taskId } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const online = useOnlineStatus()
  const projects = useProjects()
  const selectProject = useProjectSelectionStore((state) => state.selectProject)
  const defaultDepth = usePreferencesStore((state) => state.processing)
  const [taskDepth, setTaskDepth] = useState(defaultDepth)
  const intentKeys = useIntentKeys()
  const openDrawer = useUiStore((state) => state.openDrawer)

  const health = useQuery({
    queryKey: v3QueryKeys.health(),
    queryFn: () => v3Api.health(),
    retry: false,
  })
  const task = useQuery({
    queryKey: v3QueryKeys.task(taskId ?? ''),
    queryFn: () => v3Api.getTask(taskId!),
    enabled: Boolean(taskId),
  })
  const messages = useQuery({
    queryKey: v3QueryKeys.taskMessages(taskId ?? ''),
    queryFn: () => v3Api.listTaskMessages(taskId!),
    enabled: Boolean(taskId),
  })
  const taskRuns = useQuery({
    queryKey: v3QueryKeys.taskRuns(taskId ?? '', { limit: 20, offset: 0 }),
    queryFn: () => v3Api.listTaskRuns(taskId!, { limit: 20, offset: 0 }),
    enabled: Boolean(taskId),
  })
  const latestRun = taskRuns.data?.items[0]
  const depth = latestRun?.depth ?? taskDepth
  const steps = useQuery({
    queryKey: v3QueryKeys.runSteps(latestRun?.id ?? ''),
    queryFn: () => v3Api.listRunSteps(latestRun!.id),
    enabled: Boolean(latestRun?.id),
  })
  const approvals = useQuery({
    queryKey: v3QueryKeys.approvals({ run_id: latestRun?.id ?? '', status: 'pending' }),
    queryFn: () => v3Api.listApprovals({ run_id: latestRun!.id, status: 'pending' }),
    enabled: Boolean(latestRun?.id),
  })
  const artifacts = useQuery({
    queryKey: v3QueryKeys.artifacts({ task_id: taskId ?? '' }),
    queryFn: () => v3Api.listArtifacts({ task_id: taskId! }),
    enabled: Boolean(taskId),
  })

  useEffect(() => {
    const projectId = task.data?.task.project_id
    if (projectId && projectId !== projects.selectedProjectId) selectProject(projectId)
  }, [task.data, projects.selectedProjectId, selectProject])

  const stream = useRunStream(latestRun, taskId ?? '', queryClient)
  const terminalRefreshes = useRef(new Set<string>())

  useEffect(() => {
    if (
      !taskId ||
      !latestRun ||
      !['completed', 'failed', 'cancelled'].includes(latestRun.status) ||
      terminalRefreshes.current.has(latestRun.id)
    ) return
    terminalRefreshes.current.add(latestRun.id)
    void invalidateTask(queryClient, taskId, latestRun.id)
  }, [latestRun?.id, latestRun?.status, queryClient, taskId])

  const submit = useMutation({
    mutationFn: async (content: string) => {
      const existingTask = task.data?.task
      const projectId = existingTask?.project_id ?? projects.selectedProjectId
      if (!projectId) throw new Error('请先选择项目。')
      const fingerprint = await digestIntentFingerprint([
        projectId,
        taskId ?? 'new',
        depth,
        content,
      ])
      if (existingTask) {
        const messageKey = intentKeys.get('task-message', fingerprint)
        const runKey = intentKeys.get('task-run', fingerprint)
        const message = await v3Api.addTaskMessage(
          existingTask.id,
          { content },
          { idempotencyKey: messageKey },
        )
        intentKeys.mark('task-message', fingerprint, {
          phase: 'message_saved',
          messageId: message.message.id,
        })
        intentKeys.mark('task-run', fingerprint, {
          phase: 'message_saved',
          messageId: message.message.id,
        })
        let run
        try {
          run = await v3Api.createRun(
            existingTask.id,
            {
              workflow_key: 'project.inspect.v1',
              depth,
              input_message_id: message.message.id,
            },
            { idempotencyKey: runKey },
          )
        } catch {
          await refreshSubmissionFacts(queryClient, existingTask.id)
          throw new Error(PARTIAL_SUBMISSION_MESSAGE)
        }
        intentKeys.mark('task-run', fingerprint, {
          phase: 'run_started',
          messageId: message.message.id,
        })
        intentKeys.release('task-message', fingerprint)
        intentKeys.release('task-run', fingerprint)
        return { taskId: existingTask.id, runId: run.run.id }
      }

      const createKey = intentKeys.get('task-create', fingerprint)
      const runKey = intentKeys.get('task-run', fingerprint)
      const created = await v3Api.createTask(
        {
          project_id: projectId,
          title: taskTitle(content),
          message: content,
        },
        { idempotencyKey: createKey },
      )
      intentKeys.mark('task-create', fingerprint, {
        phase: 'message_saved',
        messageId: created.initial_message.id,
      })
      intentKeys.mark('task-run', fingerprint, {
        phase: 'message_saved',
        messageId: created.initial_message.id,
      })
      let run
      try {
        run = await v3Api.createRun(
          created.task.id,
          {
            workflow_key: 'project.inspect.v1',
            depth,
            input_message_id: created.initial_message.id,
          },
          { idempotencyKey: runKey },
        )
      } catch {
        await refreshSubmissionFacts(queryClient, created.task.id)
        throw new Error(PARTIAL_SUBMISSION_MESSAGE)
      }
      intentKeys.mark('task-run', fingerprint, {
        phase: 'run_started',
        messageId: created.initial_message.id,
      })
      intentKeys.release('task-create', fingerprint)
      intentKeys.release('task-run', fingerprint)
      return { taskId: created.task.id, runId: run.run.id }
    },
    onSuccess: async ({ taskId: completedTaskId }) => {
      await invalidateTask(queryClient, completedTaskId)
      navigate(`/tasks/${completedTaskId}`, { replace: true })
    },
  })

  const command = useMutation({
    mutationFn: async (action: 'pause' | 'resume' | 'cancel' | 'retry') => {
      if (!latestRun) throw new Error('当前没有可操作的运行。')
      const scope = `run-${action}`
      const fingerprint = await digestIntentFingerprint([
        latestRun.id,
        String(latestRun.version),
        action,
      ])
      const request = {
        idempotencyKey: intentKeys.get(scope, fingerprint),
      }
      const result = action === 'pause'
        ? await v3Api.pauseRun(latestRun.id, latestRun.version, request)
        : action === 'resume'
          ? await v3Api.resumeRun(latestRun.id, latestRun.version, request)
          : action === 'cancel'
            ? await v3Api.cancelRun(latestRun.id, latestRun.version, request)
            : await v3Api.retryRun(latestRun.id, latestRun.version, request)
      intentKeys.release(scope, fingerprint)
      return result
    },
    onSettled: () => invalidateTask(queryClient, taskId ?? '', latestRun?.id),
  })

  const pendingApproval = approvals.data?.items[0]
  const resolveApproval = useMutation({
    mutationFn: async (decision: 'approved' | 'rejected') => {
      if (!pendingApproval) throw new Error('待确认操作已经失效。')
      const scope = `approval-${decision}`
      const fingerprint = await digestIntentFingerprint([
        pendingApproval.id,
        String(pendingApproval.version),
        decision,
        pendingApproval.request_hash,
      ])
      return v3Api.resolveApproval(
        pendingApproval.id,
        {
          decision,
          expected_version: pendingApproval.version,
          expected_request_hash: pendingApproval.request_hash,
          note: '',
        },
        {
          idempotencyKey: intentKeys.get(scope, fingerprint),
        },
      ).then((result) => {
        intentKeys.release(scope, fingerprint)
        return result
      })
    },
    onSettled: () => invalidateTask(queryClient, taskId ?? '', latestRun?.id),
  })

  const exportArtifact = useMutation({
    mutationFn: async ({ artifactId, expectedVersion, expectedChecksum }: {
      artifactId: string
      expectedVersion: number
      expectedChecksum: string
    }) => {
      const scope = 'artifact-export'
      const fingerprint = await digestIntentFingerprint([
        artifactId,
        String(expectedVersion),
        expectedChecksum,
      ])
      return v3Api.confirmArtifactExport(
        artifactId,
        {
          expected_version: expectedVersion,
          expected_checksum: expectedChecksum,
        },
        { idempotencyKey: intentKeys.get(scope, fingerprint) },
      ).then((result) => {
        intentKeys.release(scope, fingerprint)
        return result
      })
    },
    onSettled: async () => {
      await queryClient.invalidateQueries({ queryKey: [...v3QueryKeys.all, 'artifacts'] })
    },
  })

  const canonicalMessages = useMemo(
    () => mapMessages(messages.data?.items ?? []),
    [messages.data],
  )
  const timelineMessages = mergeStreamingMessages(canonicalMessages, stream.messages)
  const taskError = firstError(
    health.error,
    taskId ? undefined : projects.error,
    task.error,
    taskRuns.error,
    stream.error,
  )
  const actionError = firstError(command.error, resolveApproval.error, exportArtifact.error)
  const detailError = firstError(
    taskId ? projects.error : undefined,
    messages.error,
    steps.error,
    approvals.error,
    artifacts.error,
  )
  const actionNotice = actionError
    ? '刚才的操作没有完成。已有内容会保留，请检查连接后手动重试。'
    : detailError
      ? '部分消息或结果暂时没有加载成功。当前任务状态和安全操作仍可使用，请稍后重试。'
      : undefined
  const serviceAvailable = Boolean(
    online &&
      health.data?.status === 'ok' &&
      health.data.executor_running &&
      !taskError &&
      (!taskId || task.data?.task),
  )
  const currentStep = steps.data?.items.find((step) => step.status === 'running')?.ordinal
  const status = steps.data?.items.some((step) => step.status === 'recovery_required')
    ? 'recovery_required'
    : toTaskStatus(latestRun?.status ?? task.data?.task.status, taskId, task.isLoading)
  const runLabelById = new Map(
    (taskRuns.data?.items ?? []).map((item) => [
      item.id,
      `第 ${item.attempt_no} 次运行 · ${runStatusLabel(item.status)}`,
    ]),
  )
  const canPause = latestRun?.status === 'queued' || latestRun?.status === 'running'
  const canResume = latestRun?.status === 'paused'
  const canStop = Boolean(latestRun && !['completed', 'failed', 'cancelled'].includes(latestRun.status))

  return (
    <TasksPage
      projectId={(task.data?.task.project_id ?? projects.selectedProjectId) || undefined}
      projectName={
        projects.data?.items.find(
          (project) => project.id === (task.data?.task.project_id ?? projects.selectedProjectId),
        )?.name
      }
      taskId={taskId}
      taskTitle={task.data?.task.title}
      status={status}
      messages={timelineMessages}
      serviceAvailable={serviceAvailable}
      online={online}
      commandPending={submit.isPending || command.isPending || resolveApproval.isPending || exportArtifact.isPending}
      currentStep={currentStep === undefined ? undefined : currentStep + 1}
      totalSteps={steps.data?.items.length}
      approval={pendingApproval ? mapApproval(pendingApproval) : undefined}
      results={(artifacts.data?.items ?? []).map((artifact) => ({
        id: artifact.id,
        title: artifact.name,
        description: artifact.status === 'ready' ? '结果已准备好' : `当前状态：${artifact.status}`,
      }))}
      plan={(steps.data?.items ?? []).map((step) => `${step.ordinal + 1}. ${step.node_type}`)}
      artifactCount={artifacts.data?.items.length}
      artifacts={(artifacts.data?.items ?? []).map((artifact) => ({
        id: artifact.id,
        name: artifact.name,
        status: artifact.status,
        content: artifact.content,
        runLabel: runLabelById.get(artifact.run_id),
      }))}
      onPreviewArtifactExport={(artifactId) => v3Api.previewArtifactExport(artifactId).then((result) => result.preview)}
      onConfirmArtifactExport={(preview) => exportArtifact.mutateAsync({
        artifactId: preview.artifact_id,
        expectedVersion: preview.version,
        expectedChecksum: preview.checksum,
      }).then(() => undefined)}
      exportingArtifactId={exportArtifact.isPending ? exportArtifact.variables?.artifactId : undefined}
      runLabel={latestRun ? `${runStatusLabel(latestRun.status)} · 第 ${latestRun.attempt_no} 次运行` : undefined}
      error={taskError}
      actionNotice={actionNotice}
      failure={latestRun?.status === 'failed' ? {
        whatHappened: '任务没有完成，服务端已停止当前运行。',
        dataSafety: '已经保存的消息和结果会保留；系统不会自动重复提交当前操作。',
        nextStep: '先查看详细过程，确认原因后再手动重试。',
        technicalDetails: latestRun.error_code || latestRun.error_message
          ? `${latestRun.error_code || 'run_failed'}: ${latestRun.error_message || '未提供错误说明'}`
          : undefined,
      } : undefined}
      depth={depth}
      onDepthChange={taskId ? undefined : setTaskDepth}
      onSubmit={(content) => submit.mutateAsync(content).then(() => undefined)}
      onPause={canPause ? () => command.mutate('pause') : undefined}
      onResume={canResume ? () => command.mutate('resume') : undefined}
      onStop={canStop ? () => command.mutate('cancel') : undefined}
      onRetry={latestRun?.status === 'failed' ? () => command.mutate('retry') : undefined}
      onApprove={pendingApproval ? () => resolveApproval.mutate('approved') : undefined}
      onReject={pendingApproval ? () => resolveApproval.mutate('rejected') : undefined}
      onViewResult={artifacts.data?.items.some((artifact) => artifact.status === 'ready')
        ? () => openDrawer('details')
        : undefined}
    />
  )
}

const PARTIAL_SUBMISSION_MESSAGE = '内容已保存，处理尚未启动。请检查连接后手动重试'

async function refreshSubmissionFacts(queryClient: QueryClient, taskId: string) {
  try {
    const filters = { limit: 20, offset: 0 }
    const [task, messages, runs] = await Promise.all([
      v3Api.getTask(taskId),
      v3Api.listTaskMessages(taskId),
      v3Api.listTaskRuns(taskId, filters),
    ])
    queryClient.setQueryData(v3QueryKeys.task(taskId), task)
    queryClient.setQueryData(v3QueryKeys.taskMessages(taskId), messages)
    queryClient.setQueryData(v3QueryKeys.taskRuns(taskId, filters), runs)
    await queryClient.invalidateQueries({ queryKey: [...v3QueryKeys.all, 'tasks'] })
    return { task, messages, runs }
  } catch {
    await invalidateTask(queryClient, taskId)
    return undefined
  }
}

function useRunStream(run: RunResource | undefined, taskId: string, queryClient: QueryClient) {
  const [messages, setMessages] = useState(initialAssistantMessageState)
  const [messageRunId, setMessageRunId] = useState('')
  const [error, setError] = useState<unknown>(null)
  const cursor = useRef(0)
  const generation = useRef(0)
  const runId = run?.id

  useEffect(() => {
    generation.current += 1
    cursor.current = 0
    setMessages(initialAssistantMessageState)
    setMessageRunId(runId ?? '')
    setError(null)
  }, [runId])

  useEffect(() => {
    if (!run || ['completed', 'failed', 'cancelled'].includes(run.status)) return
    const controller = new AbortController()
    const currentGeneration = ++generation.current
    setError(null)
    const consume = async () => {
      try {
        for await (const event of subscribeRunEvents({
          baseUrl: normalizeV3ApiBaseUrl(
            import.meta.env.VITE_API_BASE_URL || DEFAULT_V3_API_BASE_URL,
          ),
          runId: run.id,
          afterSequence: cursor.current,
          signal: controller.signal,
        })) {
          if (
            controller.signal.aborted ||
            generation.current !== currentGeneration ||
            event.run_id !== run.id
          ) continue
          cursor.current = event.sequence
          setMessageRunId(run.id)
          setMessages((current) => assistantMessageReducer(current, event))
          invalidateForEvent(queryClient, taskId, run.id, event)
        }
      } catch (streamError) {
        if (!controller.signal.aborted && generation.current === currentGeneration) {
          setError(streamError)
        }
      }
    }
    void consume()
    return () => {
      controller.abort()
      if (generation.current === currentGeneration) generation.current += 1
    }
  }, [run?.id, run?.status, queryClient, taskId])

  return {
    messages: messageRunId === (runId ?? '') ? messages : initialAssistantMessageState,
    error,
  }
}

function invalidateForEvent(
  queryClient: QueryClient,
  taskId: string,
  runId: string,
  event: AgentEvent,
) {
  if (event.event_type.startsWith('run.')) {
    void queryClient.invalidateQueries({ queryKey: v3QueryKeys.taskRuns(taskId) })
    void queryClient.invalidateQueries({ queryKey: v3QueryKeys.task(taskId) })
  }
  if (event.event_type.startsWith('step.')) {
    void queryClient.invalidateQueries({ queryKey: v3QueryKeys.runSteps(runId) })
  }
  if (event.event_type.startsWith('approval.')) {
    void queryClient.invalidateQueries({ queryKey: [...v3QueryKeys.all, 'approvals'] })
  }
  if (event.event_type.startsWith('artifact.')) {
    void queryClient.invalidateQueries({ queryKey: [...v3QueryKeys.all, 'artifacts'] })
  }
  if (
    event.event_type === 'run.completed' ||
    event.event_type === 'run.failed' ||
    event.event_type === 'run.cancelled'
  ) {
    void invalidateTask(queryClient, taskId, runId)
  }
}

async function invalidateTask(queryClient: QueryClient, taskId: string, runId?: string) {
  if (!taskId) return
  await Promise.all([
    queryClient.invalidateQueries({ queryKey: v3QueryKeys.task(taskId) }),
    queryClient.invalidateQueries({ queryKey: v3QueryKeys.taskMessages(taskId) }),
    queryClient.invalidateQueries({ queryKey: v3QueryKeys.taskRuns(taskId) }),
    runId
      ? queryClient.invalidateQueries({ queryKey: v3QueryKeys.runSteps(runId) })
      : Promise.resolve(),
    queryClient.invalidateQueries({ queryKey: [...v3QueryKeys.all, 'approvals'] }),
    queryClient.invalidateQueries({ queryKey: [...v3QueryKeys.all, 'artifacts'] }),
    queryClient.invalidateQueries({ queryKey: [...v3QueryKeys.all, 'tasks'] }),
  ])
}

function mapMessages(items: Schemas['TaskMessageResource'][]): TaskMessage[] {
  return items.flatMap((message) => {
    if (message.role !== 'user' && message.role !== 'agent') return []
    return [{
      id: message.id,
      role: message.role === 'agent' ? 'assistant' as const : 'user' as const,
      content: message.content,
    }]
  })
}

function mergeStreamingMessages(
  canonical: TaskMessage[],
  streaming: typeof initialAssistantMessageState,
): TaskMessage[] {
  const canonicalIds = new Set(canonical.map((message) => message.id))
  return [
    ...canonical,
    ...streaming.order.flatMap((messageId) => {
      const message = streaming.byId[messageId]
      if (!message || canonicalIds.has(messageId) || !message.content) return []
      return [{
        id: messageId,
        role: 'assistant' as const,
        content: message.status === 'interrupted'
          ? `${message.content}\n\n（回答已中断：${message.interruptionReason || '处理没有完成'}${message.recoverable ? '，可以手动重试' : ''}）`
          : message.content,
        streaming: message.status === 'streaming',
      }]
    }),
  ]
}

function mapApproval(approval: Schemas['ApprovalResource']): ApprovalSummary {
  return {
    action: approval.action_type,
    target: approval.target,
    unchanged: payloadText(approval.payload, 'unchanged', '服务端未声明不受影响范围'),
    undo: payloadText(approval.payload, 'undo', '服务端未提供撤销能力'),
  }
}

function payloadText(payload: Record<string, unknown>, key: string, fallback: string): string {
  const value = payload[key]
  return typeof value === 'string' && value.trim() ? value : fallback
}

function taskTitle(content: string): string {
  return content.split(/\r?\n/, 1)[0].trim().slice(0, 80) || '新任务'
}

function toTaskStatus(status: string | undefined, taskId: string | undefined, loading: boolean): TaskStatus {
  if (loading && taskId) return 'loading'
  if (!status) return 'empty'
  if (status === 'recovering') return 'recovery_required'
  return status as TaskStatus
}

function runStatusLabel(status: string): string {
  return {
    queued: '正在准备', running: '正在处理', waiting_approval: '等你确认', paused: '已暂停',
    recovering: '正在恢复', completed: '已完成', failed: '失败', cancelled: '已停止',
  }[status] ?? status
}

function firstError(...errors: unknown[]): string | undefined {
  const error = errors.find(Boolean)
  if (!error) return undefined
  return error instanceof ApiError ? error.message : error instanceof Error ? error.message : '请求失败'
}

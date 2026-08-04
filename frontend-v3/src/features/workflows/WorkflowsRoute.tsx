import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate, useParams } from 'react-router-dom'

import { ApiError, v3Api, v3QueryKeys } from '../../api'
import { WorkflowsPage } from '../../pages/WorkflowsPage'
import { useProjectSelectionStore } from '../projects/projectSelectionStore'
import { digestIntentFingerprint, useIntentKeys } from '../shared/useIntentKeys'

export function WorkflowsRoute() {
  const { workflowId } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const projectId = useProjectSelectionStore((state) => state.selectedProjectId)
  const intentKeys = useIntentKeys()
  const workflows = useQuery({
    queryKey: v3QueryKeys.workflows({ status: 'active' }),
    queryFn: () => v3Api.listWorkflows({
      status: 'active',
    }),
  })
  const detail = useQuery({
    queryKey: v3QueryKeys.workflow(workflowId ?? ''),
    queryFn: () => v3Api.getWorkflow(workflowId!),
    enabled: Boolean(workflowId),
  })

  const selectedVersion = detail.data?.versions.find(
    (version) => version.id === detail.data?.workflow.current_published_version_id,
  ) ?? detail.data?.versions[0]
  const selectedSteps = readNodeTypes(selectedVersion?.dag)
  const bindings = useQuery({ queryKey: v3QueryKeys.workflowBindings({ project_id: projectId, enabled: true }), queryFn: () => v3Api.listWorkflowBindings({ project_id: projectId, enabled: true }), enabled: Boolean(projectId && detail.data?.workflow.id) })
  const binding = bindings.data?.items.find((item) => item.workflow_id === detail.data?.workflow.id && item.workflow_version_id === selectedVersion?.id)
  const start = useMutation({ mutationFn: async (message: string) => { if (!binding || !selectedVersion || !projectId) throw new Error('当前项目没有可执行的已绑定工作流。'); const fingerprint = await digestIntentFingerprint([projectId, binding.workflow_version_id, message]); const task = await v3Api.createTask({ project_id: projectId, title: message.slice(0, 80), message }, { idempotencyKey: intentKeys.get('workflow-task', fingerprint) }); const run = await v3Api.createRun(task.task.id, { workflow_key: detail.data!.workflow.workflow_key, workflow_version_id: binding.workflow_version_id, depth: 'standard', input_message_id: task.initial_message.id }, { idempotencyKey: intentKeys.get('workflow-run', fingerprint) }); intentKeys.release('workflow-task', fingerprint); intentKeys.release('workflow-run', fingerprint); return { taskId: task.task.id, runId: run.run.id } }, onSuccess: ({ taskId }) => { void queryClient.invalidateQueries({ queryKey: [...v3QueryKeys.all, 'tasks'] }); navigate(`/tasks/${taskId}`) } })

  return (
    <WorkflowsPage
      workflows={(workflows.data?.items ?? []).map((workflow) => ({
        id: workflow.id,
        name: workflow.name,
        statusLabel: workflow.current_published_version_id ? '已发布' : '草稿',
        steps: [],
      }))}
      selectedWorkflow={detail.data ? {
        id: detail.data.workflow.id,
        name: detail.data.workflow.name,
        statusLabel: detail.data.workflow.current_published_version_id ? '已发布' : '草稿',
        steps: selectedSteps,
      } : undefined}
      loading={workflows.isLoading || detail.isLoading}
      error={errorMessage(workflows.error ?? detail.error)}
      onSelect={(id) => navigate(`/workflows/${id}`)}
      onStart={binding ? (message) => start.mutateAsync(message).then(() => undefined) : undefined}
      startPending={start.isPending}
    />
  )
}

function readNodeTypes(dag: Record<string, unknown> | undefined): string[] {
  if (!dag || !Array.isArray(dag.nodes)) return []
  return dag.nodes.flatMap((node) => {
    if (!node || typeof node !== 'object') return []
    const type = (node as Record<string, unknown>).type
    return typeof type === 'string' ? [type] : []
  })
}

function errorMessage(error: unknown): string | undefined {
  if (!error) return undefined
  return error instanceof ApiError ? error.message : error instanceof Error ? error.message : '工作流请求失败'
}

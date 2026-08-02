import { useQuery } from '@tanstack/react-query'
import { useNavigate, useParams } from 'react-router-dom'

import { ApiError, v3Api, v3QueryKeys } from '../../api'
import { WorkflowsPage } from '../../pages/WorkflowsPage'

export function WorkflowsRoute() {
  const { workflowId } = useParams()
  const navigate = useNavigate()
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

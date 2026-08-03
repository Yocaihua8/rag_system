import createClient from 'openapi-fetch'

import { ApiError } from './errors'
import type { components, paths } from './generated/schema'

type Schemas = components['schemas']
type Envelope<T> = { data: T; meta: Schemas['ResponseMeta'] }
type ApiResult<T> = {
  data?: Envelope<T>
  error?: unknown
  response: Response
}

export interface V3ApiClientOptions {
  baseUrl: string
  fetch?: (request: Request) => Promise<Response>
  headers?: Record<string, string>
}

export interface RequestOptions {
  signal?: AbortSignal
}

export interface WriteRequestOptions extends RequestOptions {
  idempotencyKey: string
}

export const DEFAULT_V3_API_BASE_URL = 'http://127.0.0.1:8765/api/v3'

export function normalizeV3ApiBaseUrl(value: string): string {
  const normalized = value.trim().replace(/\/+$/, '')
  if (!normalized || !/(?:^|\/)api\/v3$/.test(normalized)) {
    throw new Error('v3 API base URL must include the /api/v3 mount path')
  }
  return normalized
}

export function createV3ApiClient(options: V3ApiClientOptions) {
  const baseUrl = normalizeV3ApiBaseUrl(options.baseUrl)
  const client = createClient<paths>({
    baseUrl,
    fetch: options.fetch,
    headers: options.headers,
  })

  return {
    health: (request: RequestOptions = {}) =>
      unwrap<Schemas['HealthData']>(client.GET('/health', { signal: request.signal })),

    listProjects: (request: RequestOptions = {}) =>
      unwrap<Schemas['ProjectListData']>(
        client.GET('/projects', { signal: request.signal }),
      ),
    createProject: (
      body: Schemas['ProjectCreateRequest'],
      request: WriteRequestOptions,
    ) =>
      unwrap<Schemas['ProjectMutationData']>(
        client.POST('/projects', {
          body,
          params: { header: writeHeaderParams(request.idempotencyKey) },
          signal: request.signal,
        }),
      ),

    scanProjectSources: (projectId: string, request: WriteRequestOptions) =>
      unwrap<Schemas['SourceScanData']>(
        client.POST('/projects/{project_id}/sources/scan', {
          params: {
            path: { project_id: projectId },
            header: writeHeaderParams(request.idempotencyKey),
          },
          signal: request.signal,
        }),
      ),
    listProjectSources: (
      projectId: string,
      query: {
        status?: 'active' | 'indexing' | 'ready' | 'failed' | 'archived'
        limit?: number
        offset?: number
      } = {},
      request: RequestOptions = {},
    ) =>
      unwrap<Schemas['SourceListData']>(
        client.GET('/projects/{project_id}/sources', {
          params: { path: { project_id: projectId }, query },
          signal: request.signal,
        }),
      ),
    listProjectDocuments: (
      projectId: string,
      query: { source_id?: string; limit?: number; offset?: number } = {},
      request: RequestOptions = {},
    ) =>
      unwrap<Schemas['DocumentListData']>(
        client.GET('/projects/{project_id}/documents', {
          params: { path: { project_id: projectId }, query },
          signal: request.signal,
        }),
      ),

    listTasks: (
      query: {
        project_id?: string
        status?: string
        limit?: number
        offset?: number
      } = {},
      request: RequestOptions = {},
    ) =>
      unwrap<Schemas['TaskListData']>(
        client.GET('/tasks', { params: { query }, signal: request.signal }),
      ),
    getTask: (taskId: string, request: RequestOptions = {}) =>
      unwrap<Schemas['TaskData']>(
        client.GET('/tasks/{task_id}', {
          params: { path: { task_id: taskId } },
          signal: request.signal,
        }),
      ),
    createTask: (body: Schemas['TaskCreateRequest'], request: WriteRequestOptions) =>
      unwrap<Schemas['TaskMutationData']>(
        client.POST('/tasks', {
          body,
          params: { header: writeHeaderParams(request.idempotencyKey) },
          signal: request.signal,
        }),
      ),
    listTaskMessages: (taskId: string, request: RequestOptions = {}) =>
      unwrap<Schemas['TaskMessageListData']>(
        client.GET('/tasks/{task_id}/messages', {
          params: { path: { task_id: taskId } },
          signal: request.signal,
        }),
      ),
    addTaskMessage: (
      taskId: string,
      body: Schemas['TaskMessageRequest'],
      request: WriteRequestOptions,
    ) =>
      unwrap<Schemas['TaskMessageMutationData']>(
        client.POST('/tasks/{task_id}/messages', {
          params: {
            path: { task_id: taskId },
            header: writeHeaderParams(request.idempotencyKey),
          },
          body,
          signal: request.signal,
        }),
      ),
    createRun: (
      taskId: string,
      body: Schemas['RunCreateRequest'],
      request: WriteRequestOptions,
    ) =>
      unwrap<Schemas['RunMutationData']>(
        client.POST('/tasks/{task_id}/runs', {
          params: {
            path: { task_id: taskId },
            header: writeHeaderParams(request.idempotencyKey),
          },
          body,
          signal: request.signal,
        }),
      ),
    listTaskRuns: (
      taskId: string,
      query: { limit?: number; offset?: number } = {},
      request: RequestOptions = {},
    ) =>
      unwrap<Schemas['RunListData']>(
        client.GET('/tasks/{task_id}/runs', {
          params: { path: { task_id: taskId }, query },
          signal: request.signal,
        }),
      ),
    getRun: (runId: string, request: RequestOptions = {}) =>
      unwrap<Schemas['RunData']>(
        client.GET('/runs/{run_id}', {
          params: { path: { run_id: runId } },
          signal: request.signal,
        }),
      ),
    listRunSteps: (runId: string, request: RequestOptions = {}) =>
      unwrap<Schemas['RunStepsData']>(
        client.GET('/runs/{run_id}/steps', {
          params: { path: { run_id: runId } },
          signal: request.signal,
        }),
      ),
    pauseRun: (runId: string, expectedVersion: number, request: WriteRequestOptions) =>
      controlRun(client, 'pause', runId, expectedVersion, request),
    resumeRun: (runId: string, expectedVersion: number, request: WriteRequestOptions) =>
      controlRun(client, 'resume', runId, expectedVersion, request),
    cancelRun: (runId: string, expectedVersion: number, request: WriteRequestOptions) =>
      controlRun(client, 'cancel', runId, expectedVersion, request),
    retryRun: (runId: string, expectedVersion: number, request: WriteRequestOptions) =>
      unwrap<Schemas['RunMutationData']>(
        client.POST('/runs/{run_id}/retry', {
          params: {
            path: { run_id: runId },
            header: writeHeaderParams(request.idempotencyKey),
          },
          body: { expected_version: expectedVersion },
          signal: request.signal,
        }),
      ),

    listApprovals: (
      query: {
        project_id?: string
        task_id?: string
        run_id?: string
        status?: string
      } = {},
      request: RequestOptions = {},
    ) =>
      unwrap<Schemas['ApprovalListData']>(
        client.GET('/approvals', { params: { query }, signal: request.signal }),
      ),
    getApproval: (approvalId: string, request: RequestOptions = {}) =>
      unwrap<Schemas['ApprovalData']>(
        client.GET('/approvals/{approval_id}', {
          params: { path: { approval_id: approvalId } },
          signal: request.signal,
        }),
      ),
    resolveApproval: (
      approvalId: string,
      body: Schemas['ApprovalResolveRequest'],
      request: WriteRequestOptions,
    ) =>
      unwrap<Schemas['ApprovalMutationData']>(
        client.POST('/approvals/{approval_id}/resolve', {
          params: {
            path: { approval_id: approvalId },
            header: writeHeaderParams(request.idempotencyKey),
          },
          body,
          signal: request.signal,
        }),
      ),

    listArtifacts: (
      query: { project_id?: string; task_id?: string; run_id?: string } = {},
      request: RequestOptions = {},
    ) =>
      unwrap<Schemas['ArtifactListData']>(
        client.GET('/artifacts', { params: { query }, signal: request.signal }),
      ),
    getArtifact: (artifactId: string, request: RequestOptions = {}) =>
      unwrap<Schemas['ArtifactData']>(
        client.GET('/artifacts/{artifact_id}', {
          params: { path: { artifact_id: artifactId } },
          signal: request.signal,
        }),
      ),
    previewArtifact: (artifactId: string, request: RequestOptions = {}) =>
      unwrap<Schemas['ArtifactData']>(
        client.GET('/artifacts/{artifact_id}/preview', {
          params: { path: { artifact_id: artifactId } },
          signal: request.signal,
        }),
      ),

    validateWorkflow: (body: Schemas['WorkflowGraphInput'], request: RequestOptions = {}) =>
      unwrap<Schemas['WorkflowValidationData']>(
        client.POST('/workflows/validate', { body, signal: request.signal }),
      ),
    listWorkflows: (
      query: { project_id?: string; scope_type?: string; status?: string } = {},
      request: RequestOptions = {},
    ) =>
      unwrap<Schemas['WorkflowListData']>(
        client.GET('/workflows', { params: { query }, signal: request.signal }),
      ),
    getWorkflow: (workflowId: string, request: RequestOptions = {}) =>
      unwrap<Schemas['WorkflowData']>(
        client.GET('/workflows/{workflow_id}', {
          params: { path: { workflow_id: workflowId } },
          signal: request.signal,
        }),
      ),
    createWorkflow: (
      body: Schemas['WorkflowCreateRequest'],
      request: WriteRequestOptions,
    ) =>
      unwrap<Schemas['WorkflowMutationData']>(
        client.POST('/workflows', {
          body,
          params: { header: writeHeaderParams(request.idempotencyKey) },
          signal: request.signal,
        }),
      ),
    createWorkflowDraft: (
      workflowId: string,
      body: Schemas['WorkflowDraftRequest'],
      request: WriteRequestOptions,
    ) =>
      unwrap<Schemas['WorkflowMutationData']>(
        client.POST('/workflows/{workflow_id}/drafts', {
          params: {
            path: { workflow_id: workflowId },
            header: writeHeaderParams(request.idempotencyKey),
          },
          body,
          signal: request.signal,
        }),
      ),
    publishWorkflow: (
      workflowId: string,
      body: Schemas['WorkflowPublishRequest'],
      request: WriteRequestOptions,
    ) =>
      unwrap<Schemas['WorkflowMutationData']>(
        client.POST('/workflows/{workflow_id}/publish', {
          params: {
            path: { workflow_id: workflowId },
            header: writeHeaderParams(request.idempotencyKey),
          },
          body,
          signal: request.signal,
        }),
      ),
    archiveWorkflow: (
      workflowId: string,
      expectedVersion: number,
      request: WriteRequestOptions,
    ) =>
      unwrap<Schemas['WorkflowArchiveData']>(
        client.POST('/workflows/{workflow_id}/archive', {
          params: {
            path: { workflow_id: workflowId },
            header: writeHeaderParams(request.idempotencyKey),
          },
          body: { expected_version: expectedVersion },
          signal: request.signal,
        }),
      ),
    bindWorkflow: (
      workflowId: string,
      body: Schemas['WorkflowBindRequest'],
      request: WriteRequestOptions,
    ) =>
      unwrap<Schemas['WorkflowBindingMutationData']>(
        client.POST('/workflows/{workflow_id}/bindings', {
          params: {
            path: { workflow_id: workflowId },
            header: writeHeaderParams(request.idempotencyKey),
          },
          body,
          signal: request.signal,
        }),
      ),
    listWorkflowBindings: (
      query: { project_id?: string; workflow_id?: string; enabled?: boolean } = {},
      request: RequestOptions = {},
    ) =>
      unwrap<Schemas['WorkflowBindingListData']>(
        client.GET('/workflow-bindings', {
          params: { query },
          signal: request.signal,
        }),
      ),
  }
}

type OpenApiClient = ReturnType<typeof createClient<paths>>

function controlRun(
  client: OpenApiClient,
  action: 'pause' | 'resume' | 'cancel',
  runId: string,
  expectedVersion: number,
  request: WriteRequestOptions,
) {
  const path = `/runs/{run_id}/${action}` as const
  return unwrap<Schemas['RunControlData']>(
    client.POST(path, {
      params: {
        path: { run_id: runId },
        header: writeHeaderParams(request.idempotencyKey),
      },
      body: { expected_version: expectedVersion },
      signal: request.signal,
    }),
  )
}

async function unwrap<T>(request: Promise<ApiResult<T>>): Promise<T> {
  let result: ApiResult<T>
  try {
    result = await request
  } catch (error) {
    throw error instanceof ApiError ? error : ApiError.network(error)
  }

  if (result.error !== undefined || !result.response.ok) {
    throw ApiError.fromResponse(result.response, result.error)
  }
  if (!result.data || !('data' in result.data)) {
    throw new ApiError({
      status: result.response.status,
      code: 'invalid_response',
      message: 'API response did not contain a success envelope',
      requestId: result.response.headers.get('X-Request-ID') ?? '',
    })
  }
  return result.data.data
}

function writeHeaderParams(idempotencyKey: string): { 'Idempotency-Key': string } {
  const normalized = idempotencyKey.trim()
  if (!normalized) {
    throw new Error('Idempotency-Key is required for v3 write requests')
  }
  return { 'Idempotency-Key': normalized }
}

const configuredBaseUrl = import.meta.env.VITE_API_BASE_URL || DEFAULT_V3_API_BASE_URL
export const v3Api = createV3ApiClient({ baseUrl: configuredBaseUrl })

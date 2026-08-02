import { describe, expect, it, vi } from 'vitest'

import { createV3ApiClient, normalizeV3ApiBaseUrl } from './client'
import { ApiError } from './errors'

describe('v3 API client', () => {
  it('unwraps the success envelope and uses the mounted base URL', async () => {
    const fetchMock = vi.fn(async (request: Request) => {
      expect(request.url).toBe('http://api.test/api/v3/health')
      return jsonResponse({
        data: {
          status: 'ok',
          data_generation: 'v3',
          schema_revision: '0001',
          executor_running: true,
        },
        meta: { request_id: 'health-1' },
      })
    })
    const api = createV3ApiClient({
      baseUrl: 'http://api.test/api/v3/',
      fetch: fetchMock,
    })

    await expect(api.health()).resolves.toEqual({
      status: 'ok',
      data_generation: 'v3',
      schema_revision: '0001',
      executor_running: true,
    })
  })

  it('requires and sends an idempotency key for writes', async () => {
    const fetchMock = vi.fn(async (request: Request) => {
      expect(request.headers.get('Idempotency-Key')).toBe('project-1')
      return jsonResponse({
        data: {
          project: {
            id: 'project-id',
            name: 'Demo',
            root_path: 'C:\\Demo',
            status: 'active',
            version: 1,
            created_at: '2026-08-02T00:00:00Z',
            updated_at: '2026-08-02T00:00:00Z',
          },
          replayed: false,
        },
        meta: { request_id: 'project-request' },
      }, 201)
    })
    const api = createV3ApiClient({ baseUrl: 'http://api.test/api/v3', fetch: fetchMock })

    expect(() =>
      api.createProject({ name: 'Demo', root_path: 'C:\\Demo' }, { idempotencyKey: ' ' }),
    ).toThrow('Idempotency-Key is required')

    await api.createProject(
      { name: 'Demo', root_path: 'C:\\Demo' },
      { idempotencyKey: 'project-1' },
    )
  })

  it('converts v3 failure envelopes to ApiError', async () => {
    const api = createV3ApiClient({
      baseUrl: 'http://api.test/api/v3',
      fetch: async () =>
        jsonResponse(
          {
            error: {
              code: 'state_conflict',
              message: 'version changed',
              details: { expected: 1 },
            },
            request_id: 'conflict-1',
          },
          409,
        ),
    })

    const error = await api.getTask('missing').catch((value: unknown) => value)
    expect(error).toBeInstanceOf(ApiError)
    expect(error).toMatchObject({
      status: 409,
      code: 'state_conflict',
      message: 'version changed',
      details: { expected: 1 },
      requestId: 'conflict-1',
    })
  })

  it('lists persisted task runs for refresh recovery', async () => {
    const fetchMock = vi.fn(async (request: Request) => {
      expect(request.url).toBe(
        'http://api.test/api/v3/tasks/task-1/runs?limit=20&offset=0',
      )
      return jsonResponse({
        data: { items: [] },
        meta: { request_id: 'runs-1' },
      })
    })
    const api = createV3ApiClient({
      baseUrl: 'http://api.test/api/v3',
      fetch: fetchMock,
    })

    await expect(api.listTaskRuns('task-1', { limit: 20, offset: 0 })).resolves.toEqual({
      items: [],
    })
  })

  it('rejects a base URL without the v3 mount path', () => {
    expect(() => normalizeV3ApiBaseUrl('http://api.test')).toThrow('/api/v3')
  })
})

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

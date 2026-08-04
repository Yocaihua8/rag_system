import type { components } from './generated/schema'

type ErrorEnvelope = components['schemas']['ErrorEnvelope']

export class ApiError extends Error {
  readonly status: number
  readonly code: string
  readonly details: Record<string, unknown>
  readonly requestId: string

  constructor(options: {
    status: number
    code: string
    message: string
    details?: Record<string, unknown>
    requestId?: string
    cause?: unknown
  }) {
    super(options.message, { cause: options.cause })
    this.name = 'ApiError'
    this.status = options.status
    this.code = options.code
    this.details = options.details ?? {}
    this.requestId = options.requestId ?? ''
  }

  static network(cause: unknown): ApiError {
    return new ApiError({
      status: 0,
      code: 'network_error',
      message: cause instanceof Error ? cause.message : 'Network request failed',
      cause,
    })
  }

  static fromResponse(response: Response, body: unknown): ApiError {
    const requestId =
      readString(readRecord(body)?.request_id) || response.headers.get('X-Request-ID') || ''
    const envelope = readErrorEnvelope(body)
    if (envelope) {
      return new ApiError({
        status: response.status,
        code: envelope.error.code,
        message: envelope.error.message,
        details: envelope.error.details,
        requestId: envelope.request_id || requestId,
      })
    }

    const record = readRecord(body)
    const legacyMessage = readString(record?.error)
    return new ApiError({
      status: response.status,
      code: response.status === 401 ? 'authentication_required' : 'api_error',
      message: legacyMessage || response.statusText || `HTTP ${response.status}`,
      requestId,
    })
  }
}

function readErrorEnvelope(value: unknown): ErrorEnvelope | null {
  const root = readRecord(value)
  const error = readRecord(root?.error)
  const code = readString(error?.code)
  const message = readString(error?.message)
  if (!root || !error || !code || !message) {
    return null
  }
  return {
    error: {
      code,
      message,
      details: readRecord(error.details) ?? {},
    },
    request_id: readString(root.request_id),
  }
}

function readRecord(value: unknown): Record<string, unknown> | null {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null
}

function readString(value: unknown): string {
  return typeof value === 'string' ? value : ''
}

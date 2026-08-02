import { ApiError } from './errors'
import type { components } from './generated/schema'
import { normalizeV3ApiBaseUrl } from './client'

export type AgentEvent = components['schemas']['AgentEvent']

export interface RunEventSubscriptionOptions {
  baseUrl: string
  runId: string
  afterSequence?: number
  signal?: AbortSignal
  headers?: Record<string, string>
  fetch?: typeof globalThis.fetch
  reconnectDelayMs?: number
  maxReconnectAttempts?: number
}

export interface ParseSseOptions {
  afterSequence?: number
}

export async function* subscribeRunEvents(
  options: RunEventSubscriptionOptions,
): AsyncGenerator<AgentEvent> {
  const baseUrl = normalizeV3ApiBaseUrl(options.baseUrl)
  const fetchImpl = options.fetch ?? globalThis.fetch
  const reconnectDelayMs = options.reconnectDelayMs ?? 500
  const maxReconnectAttempts = boundedReconnectAttempts(options.maxReconnectAttempts)
  let cursor = Math.max(0, options.afterSequence ?? 0)
  let reconnectAttempts = 0

  while (!options.signal?.aborted) {
    const headers = new Headers(options.headers)
    headers.set('Accept', 'text/event-stream')
    if (cursor > 0) {
      headers.set('Last-Event-ID', String(cursor))
    }

    let response: Response
    try {
      response = await fetchImpl(
        `${baseUrl}/runs/${encodeURIComponent(options.runId)}/events?after_sequence=${cursor}`,
        { headers, signal: options.signal },
      )
    } catch (error) {
      if (isAbort(error) || options.signal?.aborted) {
        return
      }
      if (reconnectAttempts >= maxReconnectAttempts) {
        throw ApiError.network(error)
      }
      reconnectAttempts += 1
      await abortableDelay(reconnectDelayMs, options.signal)
      continue
    }

    if (!response.ok) {
      const responseError = ApiError.fromResponse(
        response,
        await safelyReadResponseBody(response),
      )
      if (response.status < 500 || reconnectAttempts >= maxReconnectAttempts) {
        throw responseError
      }
      reconnectAttempts += 1
      await abortableDelay(reconnectDelayMs, options.signal)
      continue
    }
    if (!response.body) {
      throw new ApiError({
        status: response.status,
        code: 'empty_event_stream',
        message: 'Run event response did not include a readable stream',
        requestId: response.headers.get('X-Request-ID') ?? '',
      })
    }

    let terminal = false
    try {
      for await (const event of parseSseStream(response.body, { afterSequence: cursor })) {
        if (event.sequence <= cursor) {
          continue
        }
        cursor = event.sequence
        reconnectAttempts = 0
        terminal = terminal || isTerminalRunEvent(event)
        yield event
      }
    } catch (error) {
      if (isAbort(error) || options.signal?.aborted) {
        return
      }
      if (terminal) {
        return
      }
      if (error instanceof ApiError) {
        throw error
      }
      if (reconnectAttempts >= maxReconnectAttempts) {
        throw ApiError.network(error)
      }
      reconnectAttempts += 1
      await abortableDelay(reconnectDelayMs, options.signal)
      continue
    }
    if (terminal || options.signal?.aborted) {
      return
    }
    if (reconnectAttempts >= maxReconnectAttempts) {
      throw new ApiError({
        status: 0,
        code: 'event_stream_ended',
        message: 'Run event stream ended before a terminal event',
      })
    }
    reconnectAttempts += 1
    await abortableDelay(reconnectDelayMs, options.signal)
  }
}

export async function* parseSseStream(
  stream: ReadableStream<Uint8Array>,
  options: ParseSseOptions = {},
): AsyncGenerator<AgentEvent> {
  const reader = stream.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let currentId = ''
  let currentEvent = ''
  let dataLines: string[] = []
  let lastSequence = Math.max(0, options.afterSequence ?? 0)

  const dispatch = (): AgentEvent | null => {
    if (dataLines.length === 0) {
      currentId = ''
      currentEvent = ''
      return null
    }
    const rawData = dataLines.join('\n')
    dataLines = []
    const parsed = parseAgentEvent(rawData)
    currentId = ''
    currentEvent = ''
    if (parsed.sequence <= lastSequence) {
      return null
    }
    lastSequence = parsed.sequence
    return parsed
  }

  const consumeLine = (line: string): AgentEvent | null => {
    if (line === '') {
      return dispatch()
    }
    if (line.startsWith(':')) {
      return null
    }
    const separator = line.indexOf(':')
    const field = separator < 0 ? line : line.slice(0, separator)
    let value = separator < 0 ? '' : line.slice(separator + 1)
    if (value.startsWith(' ')) {
      value = value.slice(1)
    }
    if (field === 'id') {
      currentId = value
    } else if (field === 'event') {
      currentEvent = value
    } else if (field === 'data') {
      dataLines.push(value)
    }
    return null
  }

  try {
    while (true) {
      const { value, done } = await reader.read()
      if (done) {
        buffer += decoder.decode()
        break
      }
      buffer += decoder.decode(value, { stream: true })
      let newline = buffer.indexOf('\n')
      while (newline >= 0) {
        const line = buffer.slice(0, newline).replace(/\r$/, '')
        buffer = buffer.slice(newline + 1)
        const event = consumeLine(line)
        if (event) {
          yield event
        }
        newline = buffer.indexOf('\n')
      }
    }

    if (buffer) {
      const event = consumeLine(buffer.replace(/\r$/, ''))
      if (event) {
        yield event
      }
    }
    const finalEvent = dispatch()
    if (finalEvent) {
      yield finalEvent
    }
  } finally {
    reader.releaseLock()
  }
}

function parseAgentEvent(rawData: string): AgentEvent {
  let value: unknown
  try {
    value = JSON.parse(rawData)
  } catch (cause) {
    throw new ApiError({
      status: 0,
      code: 'invalid_event_data',
      message: 'Run event contained invalid JSON',
      cause,
    })
  }
  if (!isAgentEvent(value)) {
    throw new ApiError({
      status: 0,
      code: 'invalid_event_data',
      message: 'Run event did not match the v3 AgentEvent envelope',
    })
  }
  return value
}

function isAgentEvent(value: unknown): value is AgentEvent {
  if (!value || typeof value !== 'object') {
    return false
  }
  const event = value as Record<string, unknown>
  return (
    Number.isInteger(event.sequence) &&
    Number(event.sequence) >= 1 &&
    typeof event.event_type === 'string' &&
    typeof event.run_id === 'string' &&
    typeof event.created_at === 'string' &&
    !!event.payload &&
    typeof event.payload === 'object' &&
    !Array.isArray(event.payload)
  )
}

function isTerminalRunEvent(event: AgentEvent): boolean {
  return (
    event.event_type === 'run.completed' ||
    event.event_type === 'run.failed' ||
    event.event_type === 'run.cancelled'
  )
}

async function readResponseBody(response: Response): Promise<unknown> {
  const contentType = response.headers.get('content-type') ?? ''
  if (contentType.includes('application/json')) {
    try {
      return await response.json()
    } catch {
      return null
    }
  }
  return { error: await response.text() }
}

async function safelyReadResponseBody(response: Response): Promise<unknown> {
  try {
    return await readResponseBody(response)
  } catch {
    return null
  }
}

function boundedReconnectAttempts(value: number | undefined): number {
  const candidate = value ?? 5
  if (!Number.isFinite(candidate)) {
    return 5
  }
  return Math.max(0, Math.floor(candidate))
}

async function abortableDelay(milliseconds: number, signal?: AbortSignal): Promise<void> {
  if (milliseconds <= 0) {
    return
  }
  await new Promise<void>((resolve, reject) => {
    const finish = () => {
      signal?.removeEventListener('abort', abort)
      resolve()
    }
    const timeout = globalThis.setTimeout(finish, milliseconds)
    const abort = () => {
      globalThis.clearTimeout(timeout)
      signal?.removeEventListener('abort', abort)
      reject(new DOMException('The operation was aborted', 'AbortError'))
    }
    if (signal?.aborted) {
      abort()
      return
    }
    signal?.addEventListener('abort', abort, { once: true })
  })
}

function isAbort(error: unknown): boolean {
  return error instanceof DOMException && error.name === 'AbortError'
}

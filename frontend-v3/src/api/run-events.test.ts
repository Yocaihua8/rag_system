import { describe, expect, it, vi } from 'vitest'

import type { AgentEvent } from './run-events'
import { parseSseStream, subscribeRunEvents } from './run-events'

describe('v3 run event stream', () => {
  it('parses split frames, ignores heartbeats, and filters repeated sequence numbers', async () => {
    const first = event(1, 'assistant.message.started', {
      message_id: 'message-1',
      message_type: 'answer',
      format: 'markdown',
    })
    const duplicate = event(1, 'assistant.message.started', {
      message_id: 'message-1',
      message_type: 'answer',
      format: 'markdown',
    })
    const delta = event(2, 'assistant.message.delta', {
      message_id: 'message-1',
      chunk_index: 0,
      text: '第一段',
    })
    const wire = [
      ': keep-alive 0\n\n',
      frame(first),
      frame(duplicate),
      frame(delta),
    ].join('')
    const split = Math.floor(wire.length / 2)
    const stream = byteStream([wire.slice(0, split), wire.slice(split)])

    const received: AgentEvent[] = []
    for await (const item of parseSseStream(stream)) {
      received.push(item)
    }

    expect(received.map((item) => item.sequence)).toEqual([1, 2])
    expect(received[1]).toMatchObject({
      event_type: 'assistant.message.delta',
      payload: { text: '第一段' },
    })
  })

  it('reconnects from the last sequence and filters replayed events', async () => {
    const requests: (RequestInfo | URL)[] = []
    const fetchMock = vi
      .fn<typeof fetch>()
      .mockImplementationOnce(async (input) => {
        requests.push(input)
        return new Response(byteStream([frame(event(1, 'run.started', {}))]), {
          headers: { 'Content-Type': 'text/event-stream' },
        })
      })
      .mockImplementationOnce(async (input, init) => {
        requests.push(input)
        expect(new Headers(init?.headers).get('Last-Event-ID')).toBe('1')
        return new Response(
          byteStream([
            frame(event(1, 'run.started', {})),
            frame(event(2, 'run.completed', {})),
          ]),
          { headers: { 'Content-Type': 'text/event-stream' } },
        )
      })

    const received: AgentEvent[] = []
    for await (const item of subscribeRunEvents({
      baseUrl: 'http://api.test/api/v3',
      runId: 'run/id',
      fetch: fetchMock,
      reconnectDelayMs: 0,
      maxReconnectAttempts: 2,
    })) {
      received.push(item)
    }

    expect(received.map((item) => item.sequence)).toEqual([1, 2])
    expect(String(requests[0])).toContain('/runs/run%2Fid/events?after_sequence=0')
    expect(String(requests[1])).toContain('after_sequence=1')
  })

  it('reconnects from the last sequence after the response body disconnects', async () => {
    const fetchMock = vi
      .fn<typeof fetch>()
      .mockResolvedValueOnce(
        new Response(failingByteStream(frame(event(1, 'run.started', {}))), {
          headers: { 'Content-Type': 'text/event-stream' },
        }),
      )
      .mockImplementationOnce(async (_input, init) => {
        expect(new Headers(init?.headers).get('Last-Event-ID')).toBe('1')
        return new Response(
          byteStream([
            frame(event(1, 'run.started', {})),
            frame(event(2, 'run.completed', {})),
          ]),
          { headers: { 'Content-Type': 'text/event-stream' } },
        )
      })

    const received: AgentEvent[] = []
    for await (const item of subscribeRunEvents({
      baseUrl: 'http://api.test/api/v3',
      runId: 'run-1',
      fetch: fetchMock,
      reconnectDelayMs: 0,
      maxReconnectAttempts: 2,
    })) {
      received.push(item)
    }

    expect(received.map((item) => item.sequence)).toEqual([1, 2])
    expect(fetchMock).toHaveBeenCalledTimes(2)
  })

  it('stops after a terminal event even when the response body disconnects', async () => {
    const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(
      new Response(failingByteStream(frame(event(1, 'run.completed', {}))), {
        headers: { 'Content-Type': 'text/event-stream' },
      }),
    )

    const received: AgentEvent[] = []
    for await (const item of subscribeRunEvents({
      baseUrl: 'http://api.test/api/v3',
      runId: 'run-1',
      fetch: fetchMock,
      reconnectDelayMs: 0,
      maxReconnectAttempts: 2,
    })) {
      received.push(item)
    }

    expect(received.map((item) => item.sequence)).toEqual([1])
    expect(fetchMock).toHaveBeenCalledTimes(1)
  })

  it('does not retry 4xx responses or invalid event data', async () => {
    const rejectedFetch = vi.fn<typeof fetch>().mockResolvedValue(
      new Response(
        JSON.stringify({
          error: { code: 'state_conflict', message: 'run is unavailable', details: {} },
          request_id: 'request-1',
        }),
        { status: 409, headers: { 'Content-Type': 'application/json' } },
      ),
    )
    const rejected = subscribeRunEvents({
      baseUrl: 'http://api.test/api/v3',
      runId: 'run-1',
      fetch: rejectedFetch,
      reconnectDelayMs: 0,
      maxReconnectAttempts: 2,
    })

    await expect(rejected.next()).rejects.toMatchObject({
      status: 409,
      code: 'state_conflict',
    })
    expect(rejectedFetch).toHaveBeenCalledTimes(1)

    const invalidFetch = vi.fn<typeof fetch>().mockResolvedValue(
      new Response(byteStream(['id: 1\nevent: run.started\ndata: not-json\n\n']), {
        headers: { 'Content-Type': 'text/event-stream' },
      }),
    )
    const invalid = subscribeRunEvents({
      baseUrl: 'http://api.test/api/v3',
      runId: 'run-1',
      fetch: invalidFetch,
      reconnectDelayMs: 0,
      maxReconnectAttempts: 2,
    })

    await expect(invalid.next()).rejects.toMatchObject({ code: 'invalid_event_data' })
    expect(invalidFetch).toHaveBeenCalledTimes(1)
  })

  it('bounds consecutive body-disconnect reconnect attempts', async () => {
    const fetchMock = vi.fn<typeof fetch>().mockImplementation(async () =>
      new Response(failingByteStream(''), {
        headers: { 'Content-Type': 'text/event-stream' },
      }),
    )
    const subscription = subscribeRunEvents({
      baseUrl: 'http://api.test/api/v3',
      runId: 'run-1',
      fetch: fetchMock,
      reconnectDelayMs: 0,
      maxReconnectAttempts: 1,
    })

    await expect(subscription.next()).rejects.toMatchObject({ code: 'network_error' })
    expect(fetchMock).toHaveBeenCalledTimes(2)
  })
})

function event(sequence: number, eventType: string, payload: Record<string, unknown>): AgentEvent {
  return {
    sequence,
    event_type: eventType,
    run_id: 'run-1',
    step_id: null,
    event_schema_version: 1,
    payload,
    created_at: '2026-08-02T00:00:00Z',
  } as AgentEvent
}

function frame(value: AgentEvent): string {
  return `id: ${value.sequence}\nevent: ${value.event_type}\ndata: ${JSON.stringify(value)}\n\n`
}

function byteStream(chunks: string[]): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder()
  return new ReadableStream({
    start(controller) {
      for (const chunk of chunks) {
        controller.enqueue(encoder.encode(chunk))
      }
      controller.close()
    },
  })
}

function failingByteStream(chunk: string): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder()
  let sent = false
  return new ReadableStream({
    pull(controller) {
      if (!sent && chunk) {
        sent = true
        controller.enqueue(encoder.encode(chunk))
        return
      }
      controller.error(new TypeError('response body disconnected'))
    },
  })
}

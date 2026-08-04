import { describe, expect, it } from 'vitest'

import {
  assistantMessageReducer,
  initialAssistantMessageState,
} from './assistant-message-reducer'
import type { AgentEvent } from './run-events'

describe('assistant message reducer', () => {
  it('builds one message from ordered deltas and ignores duplicate sequence/chunks', async () => {
    const completedContent = '第一段。\n\n第二段。'
    const completedHash = await sha256(completedContent)
    let state = initialAssistantMessageState
    state = assistantMessageReducer(state, assistantEvent(1, 'assistant.message.started', {
      message_id: 'message-1',
      message_type: 'answer',
      format: 'markdown',
    }))
    state = assistantMessageReducer(state, assistantEvent(2, 'assistant.message.delta', {
      message_id: 'message-1',
      chunk_index: 0,
      text: '第一段。',
    }))
    const beforeDuplicate = state
    const sameState = assistantMessageReducer(state, assistantEvent(2, 'assistant.message.delta', {
      message_id: 'message-1',
      chunk_index: 0,
      text: '重复内容',
    }))
    state = assistantMessageReducer(sameState, assistantEvent(3, 'assistant.message.delta', {
      message_id: 'message-1',
      chunk_index: 0,
      text: '仍然重复',
    }))
    state = assistantMessageReducer(state, assistantEvent(4, 'assistant.message.delta', {
      message_id: 'message-1',
      chunk_index: 1,
      text: '第二段。',
    }))
    state = assistantMessageReducer(state, assistantEvent(5, 'assistant.message.completed', {
      message_id: 'message-1',
      chunk_count: 2,
      char_count: completedContent.length,
      content_hash: completedHash,
    }))

    expect(sameState).toBe(beforeDuplicate)
    expect(state.lastSequence).toBe(5)
    expect(state.order).toEqual(['message-1'])
    expect(state.byId['message-1']).toMatchObject({
      content: completedContent,
      status: 'completed',
      chunkCount: 2,
      charCount: completedContent.length,
      contentHash: completedHash,
    })
    await expect(sha256(state.byId['message-1'].content)).resolves.toBe(
      state.byId['message-1'].contentHash,
    )
  })
})

function assistantEvent(
  sequence: number,
  eventType: AgentEvent['event_type'],
  payload: Record<string, unknown>,
): AgentEvent {
  return {
    sequence,
    event_type: eventType,
    run_id: 'run-1',
    step_id: 'step-1',
    event_schema_version: 1,
    payload,
    created_at: '2026-08-02T00:00:00Z',
  } as AgentEvent
}

async function sha256(value: string): Promise<string> {
  const digest = await globalThis.crypto.subtle.digest(
    'SHA-256',
    new TextEncoder().encode(value),
  )
  return Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, '0')).join('')
}

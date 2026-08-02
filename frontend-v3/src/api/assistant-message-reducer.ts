import type { AgentEvent } from './run-events'

type AssistantMessageEvent = Extract<
  AgentEvent,
  {
    event_type:
      | 'assistant.message.started'
      | 'assistant.message.delta'
      | 'assistant.message.completed'
      | 'assistant.message.interrupted'
  }
>

export type AssistantMessageStatus = 'streaming' | 'completed' | 'interrupted'

export interface AssistantMessageProjection {
  messageId: string
  messageType: string
  format: 'markdown' | 'text'
  content: string
  chunks: Record<number, string>
  status: AssistantMessageStatus
  chunkCount: number | null
  charCount: number | null
  contentHash: string
  interruptionReason: string
  recoverable: boolean
}

export interface AssistantMessageState {
  lastSequence: number
  order: string[]
  byId: Record<string, AssistantMessageProjection>
}

export const initialAssistantMessageState: AssistantMessageState = {
  lastSequence: 0,
  order: [],
  byId: {},
}

export function assistantMessageReducer(
  state: AssistantMessageState,
  event: AgentEvent,
): AssistantMessageState {
  if (event.sequence <= state.lastSequence) {
    return state
  }
  const advancedState = { ...state, lastSequence: event.sequence }
  if (!isAssistantMessageEvent(event)) {
    return advancedState
  }

  const messageId = event.payload.message_id
  const existing = state.byId[messageId] ?? createProjection(messageId)
  let next = existing

  if (event.event_type === 'assistant.message.started') {
    next = {
      ...existing,
      messageType: event.payload.message_type,
      format: event.payload.format,
      status: 'streaming',
    }
  } else if (event.event_type === 'assistant.message.delta') {
    if (existing.chunks[event.payload.chunk_index] !== undefined) {
      return advancedState
    }
    const chunks = { ...existing.chunks, [event.payload.chunk_index]: event.payload.text }
    next = {
      ...existing,
      chunks,
      content: Object.entries(chunks)
        .sort(([left], [right]) => Number(left) - Number(right))
        .map(([, text]) => text)
        .join('\n\n'),
      status: 'streaming',
    }
  } else if (event.event_type === 'assistant.message.completed') {
    next = {
      ...existing,
      status: 'completed',
      chunkCount: event.payload.chunk_count,
      charCount: event.payload.char_count,
      contentHash: event.payload.content_hash,
      interruptionReason: '',
      recoverable: false,
    }
  } else if (event.event_type === 'assistant.message.interrupted') {
    next = {
      ...existing,
      status: 'interrupted',
      interruptionReason: event.payload.reason,
      recoverable: event.payload.recoverable,
    }
  }

  const known = Object.hasOwn(state.byId, messageId)
  return {
    ...advancedState,
    order: known ? state.order : [...state.order, messageId],
    byId: { ...state.byId, [messageId]: next },
  }
}

function isAssistantMessageEvent(event: AgentEvent): event is AssistantMessageEvent {
  return (
    event.event_type === 'assistant.message.started' ||
    event.event_type === 'assistant.message.delta' ||
    event.event_type === 'assistant.message.completed' ||
    event.event_type === 'assistant.message.interrupted'
  )
}

function createProjection(messageId: string): AssistantMessageProjection {
  return {
    messageId,
    messageType: 'answer',
    format: 'markdown',
    content: '',
    chunks: {},
    status: 'streaming',
    chunkCount: null,
    charCount: null,
    contentHash: '',
    interruptionReason: '',
    recoverable: false,
  }
}

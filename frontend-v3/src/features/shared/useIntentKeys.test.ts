import { act, renderHook } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { digestIntentFingerprint, useIntentKeys } from './useIntentKeys'

describe('useIntentKeys persistent ledger', () => {
  beforeEach(() => {
    sessionStorage.clear()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('reuses a key after remount without storing the original prompt', async () => {
    const prompt = '请检查 E:\\Private\\Project 中的敏感内容'
    const digest = await digestIntentFingerprint(['project-1', 'new', 'standard', prompt])
    const first = renderHook(() => useIntentKeys())
    let firstKey = ''

    act(() => {
      firstKey = first.result.current.get('task-run', digest)
      first.result.current.mark('task-run', digest, {
        phase: 'message_saved',
        messageId: 'message-1',
      })
    })
    first.unmount()

    const stored = sessionStorage.getItem('knowledge-island:v3:intent-ledger') ?? ''
    expect(stored).not.toContain(prompt)
    expect(stored).not.toContain('E:\\Private\\Project')
    expect(stored).toContain(digest)
    expect(stored).toContain('message-1')

    const second = renderHook(() => useIntentKeys())
    expect(second.result.current.get('task-run', digest)).toBe(firstKey)
  })

  it('bounds retained intents and expires unresolved entries after the recovery window', async () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-08-02T00:00:00Z'))
    const { result } = renderHook(() => useIntentKeys())
    const firstDigest = await digestIntentFingerprint(['intent-0'])

    for (let index = 0; index < 70; index += 1) {
      const digest = index === 0
        ? firstDigest
        : await digestIntentFingerprint([`intent-${index}`])
      act(() => {
        result.current.get('task-run', digest)
      })
      vi.setSystemTime(new Date(Date.now() + 1_000))
    }

    const bounded = JSON.parse(
      sessionStorage.getItem('knowledge-island:v3:intent-ledger') ?? '[]',
    ) as Array<{ digest: string }>
    expect(bounded).toHaveLength(64)
    expect(bounded.some((entry) => entry.digest === firstDigest)).toBe(false)

    vi.setSystemTime(new Date(Date.now() + 24 * 60 * 60 * 1_000 + 1))
    const freshDigest = await digestIntentFingerprint(['fresh-intent'])
    act(() => {
      result.current.get('task-run', freshDigest)
    })
    const refreshed = JSON.parse(
      sessionStorage.getItem('knowledge-island:v3:intent-ledger') ?? '[]',
    ) as Array<{ digest: string }>
    expect(refreshed).toEqual([expect.objectContaining({ digest: freshDigest })])
  })

  it('rotates the key after a confirmed operation is released', async () => {
    const digest = await digestIntentFingerprint(['same visible content'])
    const first = renderHook(() => useIntentKeys())
    let firstKey = ''
    act(() => {
      firstKey = first.result.current.get('task-run', digest)
      first.result.current.release('task-run', digest)
    })
    first.unmount()

    const second = renderHook(() => useIntentKeys())
    expect(second.result.current.get('task-run', digest)).not.toBe(firstKey)
  })
})

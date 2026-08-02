import { useCallback, useMemo, useRef } from 'react'

const STORAGE_KEY = 'knowledge-island:v3:intent-ledger'
const ENTRY_TTL_MS = 24 * 60 * 60 * 1000
const MAX_ENTRIES = 64
const DIGEST_PATTERN = /^sha256:[0-9a-f]{64}$/

export type IntentPhase = 'pending' | 'message_saved' | 'run_started'

interface IntentEntry {
  scope: string
  digest: string
  key: string
  phase: IntentPhase
  messageId?: string
  expiresAt: number
}

interface IntentUpdate {
  phase: IntentPhase
  messageId?: string
}

export function useIntentKeys() {
  const volatileKeys = useRef(new Map<string, string>())

  const get = useCallback((scope: string, fingerprint: string) => {
    const identity = `${scope}:${fingerprint}`
    const volatile = volatileKeys.current.get(identity)
    if (volatile) return volatile
    if (!isSafeDigest(fingerprint)) {
      const key = createKey(scope)
      volatileKeys.current.set(identity, key)
      return key
    }

    const entries = readLedger()
    const existing = entries.find(
      (entry) => entry.scope === scope && entry.digest === fingerprint,
    )
    if (existing) {
      volatileKeys.current.set(identity, existing.key)
      return existing.key
    }

    const key = createKey(scope)
    volatileKeys.current.set(identity, key)
    writeLedger([
      ...entries,
      {
        scope,
        digest: fingerprint,
        key,
        phase: 'pending',
        expiresAt: Date.now() + ENTRY_TTL_MS,
      },
    ])
    return key
  }, [])

  const mark = useCallback((scope: string, fingerprint: string, update: IntentUpdate) => {
    if (!isSafeDigest(fingerprint)) return
    const entries = readLedger()
    const entry = entries.find(
      (candidate) => candidate.scope === scope && candidate.digest === fingerprint,
    )
    if (!entry) return
    entry.phase = update.phase
    entry.messageId = update.messageId
    entry.expiresAt = Date.now() + ENTRY_TTL_MS
    writeLedger(entries)
  }, [])

  const release = useCallback((scope: string, fingerprint: string) => {
    volatileKeys.current.delete(`${scope}:${fingerprint}`)
    if (!isSafeDigest(fingerprint)) return
    writeLedger(
      readLedger().filter(
        (entry) => entry.scope !== scope || entry.digest !== fingerprint,
      ),
    )
  }, [])

  return useMemo(() => ({ get, mark, release }), [get, mark, release])
}

export async function digestIntentFingerprint(parts: readonly string[]): Promise<string> {
  if (!globalThis.crypto?.subtle) {
    throw new Error('Secure hashing is unavailable')
  }
  const serialized = JSON.stringify(parts)
  const digest = await globalThis.crypto.subtle.digest(
    'SHA-256',
    new TextEncoder().encode(serialized),
  )
  const hex = Array.from(new Uint8Array(digest), (value) =>
    value.toString(16).padStart(2, '0'),
  ).join('')
  return `sha256:${hex}`
}

function readLedger(): IntentEntry[] {
  const storage = sessionStorageOrNull()
  if (!storage) return []
  let parsed: unknown
  try {
    parsed = JSON.parse(storage.getItem(STORAGE_KEY) ?? '[]')
  } catch {
    parsed = []
  }
  const now = Date.now()
  const entries = Array.isArray(parsed)
    ? parsed.filter((entry): entry is IntentEntry => isIntentEntry(entry, now))
    : []
  const bounded = entries
    .sort((left, right) => right.expiresAt - left.expiresAt)
    .slice(0, MAX_ENTRIES)
  writeLedgerValue(storage, bounded)
  return bounded
}

function writeLedger(entries: IntentEntry[]) {
  const storage = sessionStorageOrNull()
  if (!storage) return
  const now = Date.now()
  const bounded = entries
    .filter((entry) => isIntentEntry(entry, now))
    .sort((left, right) => right.expiresAt - left.expiresAt)
    .slice(0, MAX_ENTRIES)
  writeLedgerValue(storage, bounded)
}

function writeLedgerValue(storage: Storage, entries: IntentEntry[]) {
  try {
    if (entries.length) storage.setItem(STORAGE_KEY, JSON.stringify(entries))
    else storage.removeItem(STORAGE_KEY)
  } catch {
    // Storage can be unavailable in privacy-restricted browser contexts.
  }
}

function isIntentEntry(value: unknown, now: number): value is IntentEntry {
  if (!value || typeof value !== 'object') return false
  const entry = value as Partial<IntentEntry>
  return typeof entry.scope === 'string' &&
    typeof entry.digest === 'string' && isSafeDigest(entry.digest) &&
    typeof entry.key === 'string' && entry.key.startsWith('web:') &&
    (entry.phase === 'pending' || entry.phase === 'message_saved' || entry.phase === 'run_started') &&
    (entry.messageId === undefined || typeof entry.messageId === 'string') &&
    typeof entry.expiresAt === 'number' && entry.expiresAt > now
}

function sessionStorageOrNull(): Storage | null {
  try {
    return globalThis.sessionStorage ?? null
  } catch {
    return null
  }
}

function isSafeDigest(value: string): boolean {
  return DIGEST_PATTERN.test(value)
}

function createKey(scope: string): string {
  return `web:${scope}:${randomId()}`
}

function randomId(): string {
  if (!globalThis.crypto) throw new Error('Secure random number generation is unavailable')
  if (globalThis.crypto.randomUUID) return globalThis.crypto.randomUUID()
  const values = new Uint32Array(4)
  globalThis.crypto.getRandomValues(values)
  return Array.from(values, (value) => value.toString(16).padStart(8, '0')).join('')
}

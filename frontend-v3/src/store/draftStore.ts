import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface DraftState {
  drafts: Record<string, string>
  setDraft: (key: string, value: string) => void
  clearDraft: (key: string) => void
}

export const useDraftStore = create<DraftState>()(
  persist(
    (set) => ({
      drafts: {},
      setDraft: (key, value) =>
        set((state) => ({ drafts: { ...state.drafts, [key]: value } })),
      clearDraft: (key) =>
        set((state) => {
          const drafts = { ...state.drafts }
          delete drafts[key]
          return { drafts }
        }),
    }),
    { name: 'knowledge-island-v3-task-drafts' },
  ),
)

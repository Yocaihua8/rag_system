import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export type ThemePreference = 'system' | 'light' | 'dark'
export type ProcessingPreference = 'quick' | 'standard' | 'deep'

interface PreferencesState {
  theme: ThemePreference
  processing: ProcessingPreference
  setTheme: (theme: ThemePreference) => void
  setProcessing: (processing: ProcessingPreference) => void
}

export const usePreferencesStore = create<PreferencesState>()(
  persist(
    (set) => ({
      theme: 'system',
      processing: 'standard',
      setTheme: (theme) => set({ theme }),
      setProcessing: (processing) => set({ processing }),
    }),
    { name: 'knowledge-island-v3-preferences' },
  ),
)

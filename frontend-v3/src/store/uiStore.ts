import { create } from 'zustand'

type DrawerName = 'history' | 'details' | null

interface UiState {
  drawer: DrawerName
  openDrawer: (drawer: Exclude<DrawerName, null>) => void
  closeDrawer: () => void
}

export const useUiStore = create<UiState>((set) => ({
  drawer: null,
  openDrawer: (drawer) => set({ drawer }),
  closeDrawer: () => set({ drawer: null }),
}))

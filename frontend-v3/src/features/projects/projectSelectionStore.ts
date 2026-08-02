import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface ProjectSelectionState {
  selectedProjectId: string
  selectProject: (projectId: string) => void
}

export const useProjectSelectionStore = create<ProjectSelectionState>()(
  persist(
    (set) => ({
      selectedProjectId: '',
      selectProject: (selectedProjectId) => set({ selectedProjectId }),
    }),
    { name: 'knowledge-island-v3-selected-project' },
  ),
)

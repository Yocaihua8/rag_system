import { useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'

import { v3Api, v3QueryKeys } from '../../api'
import { useProjectSelectionStore } from './projectSelectionStore'

export function useProjects() {
  const query = useQuery({
    queryKey: v3QueryKeys.projects(),
    queryFn: () => v3Api.listProjects(),
  })
  const selectedProjectId = useProjectSelectionStore((state) => state.selectedProjectId)
  const selectProject = useProjectSelectionStore((state) => state.selectProject)

  useEffect(() => {
    if (!query.isSuccess) return
    const projects = query.data?.items ?? []
    if (!projects.length) {
      if (selectedProjectId) selectProject('')
      return
    }
    if (!projects.some((project) => project.id === selectedProjectId)) {
      selectProject(projects[0].id)
    }
  }, [query.data, query.isSuccess, selectedProjectId, selectProject])

  const selectedProject = query.data?.items.find(
    (project) => project.id === selectedProjectId,
  )
  return { ...query, selectedProjectId, selectedProject, selectProject }
}

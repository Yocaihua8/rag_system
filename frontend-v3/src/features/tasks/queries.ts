import { useQuery } from '@tanstack/react-query'

import { v3Api, v3QueryKeys } from '../../api'

export function useProjectTasks(projectId: string) {
  return useQuery({
    queryKey: v3QueryKeys.tasks({ project_id: projectId }),
    queryFn: () => v3Api.listTasks({ project_id: projectId, limit: 100, offset: 0 }),
    enabled: Boolean(projectId),
  })
}

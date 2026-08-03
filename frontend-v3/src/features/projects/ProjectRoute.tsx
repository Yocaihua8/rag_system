import { useEffect } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate, useParams } from 'react-router-dom'

import { ApiError, v3Api, v3QueryKeys } from '../../api'
import { ProjectPage } from '../../pages/ProjectPage'
import { digestIntentFingerprint, useIntentKeys } from '../shared/useIntentKeys'
import { useProjects } from './queries'

export function ProjectRoute() {
  const { projectId } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const projects = useProjects()
  const intentKeys = useIntentKeys()
  const activeProjectId = projects.selectedProject?.id
  const sources = useQuery({
    queryKey: v3QueryKeys.projectSources(activeProjectId ?? ''),
    queryFn: () => v3Api.listProjectSources(activeProjectId!),
    enabled: Boolean(activeProjectId),
  })
  const documents = useQuery({
    queryKey: v3QueryKeys.projectDocuments(activeProjectId ?? ''),
    queryFn: () => v3Api.listProjectDocuments(activeProjectId!),
    enabled: Boolean(activeProjectId),
  })

  useEffect(() => {
    if (projectId && projects.data?.items.some((project) => project.id === projectId)) {
      projects.selectProject(projectId)
    }
  }, [projectId, projects.data, projects.selectProject])

  const createProject = useMutation({
    mutationFn: async ({ name, rootPath }: { name: string; rootPath: string }) => {
      const fingerprint = await digestIntentFingerprint([name, rootPath])
      const result = await v3Api.createProject(
        { name, root_path: rootPath },
        { idempotencyKey: intentKeys.get('project-create', fingerprint) },
      )
      intentKeys.release('project-create', fingerprint)
      return result
    },
    onSuccess: async ({ project }) => {
      projects.selectProject(project.id)
      await queryClient.invalidateQueries({ queryKey: v3QueryKeys.projects() })
      navigate(`/projects/${project.id}/overview`, { replace: true })
    },
  })

  const scanSources = useMutation({
    mutationFn: async (id: string) => {
      const fingerprint = await digestIntentFingerprint([id, 'project-root-source-scan-v1'])
      const result = await v3Api.scanProjectSources(
        id,
        { idempotencyKey: intentKeys.get('project-source-scan', fingerprint) },
      )
      intentKeys.release('project-source-scan', fingerprint)
      return result
    },
    onSuccess: async (_result, id) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: v3QueryKeys.projectSources(id) }),
        queryClient.invalidateQueries({ queryKey: v3QueryKeys.projectDocuments(id) }),
      ])
    },
  })

  return (
    <ProjectPage
      project={projects.selectedProject ? {
        id: projects.selectedProject.id,
        name: projects.selectedProject.name,
        rootLabel: projects.selectedProject.root_path,
      } : undefined}
      projects={(projects.data?.items ?? []).map((project) => ({
        id: project.id,
        name: project.name,
        rootLabel: project.root_path,
      }))}
      loading={projects.isLoading}
      error={errorMessage(projects.error ?? createProject.error)}
      creating={createProject.isPending}
      sources={(sources.data?.items ?? []).map((source) => ({
        id: source.id,
        name: source.name,
        sourceType: source.source_type,
        status: source.status,
        documentCount: source.document_count,
      }))}
      documents={(documents.data?.items ?? []).map((document) => ({
        id: document.id,
        relativePath: document.relative_path,
        mimeType: document.mime_type,
        sizeBytes: document.size_bytes,
      }))}
      sourcesLoading={sources.isLoading || documents.isLoading}
      scanningSources={scanSources.isPending}
      sourcesError={errorMessage(sources.error ?? documents.error ?? scanSources.error)}
      onSelectProject={(id) => {
        projects.selectProject(id)
        navigate(`/projects/${id}/overview`)
      }}
      onCreateProject={(name, rootPath) =>
        createProject.mutateAsync({ name, rootPath }).then(() => undefined)
      }
      onScanSources={() => activeProjectId ? scanSources.mutateAsync(activeProjectId).then(() => undefined) : Promise.resolve()}
    />
  )
}

function errorMessage(error: unknown): string | undefined {
  if (!error) return undefined
  return error instanceof ApiError ? error.message : error instanceof Error ? error.message : '项目请求失败'
}

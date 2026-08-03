export const v3QueryKeys = {
  all: ['v3'] as const,
  health: () => [...v3QueryKeys.all, 'health'] as const,
  projects: () => [...v3QueryKeys.all, 'projects'] as const,
  projectSources: (projectId: string) =>
    [...v3QueryKeys.all, 'project', projectId, 'sources'] as const,
  projectDocuments: (projectId: string) =>
    [...v3QueryKeys.all, 'project', projectId, 'documents'] as const,
  projectInsight: (projectId: string) =>
    [...v3QueryKeys.all, 'project', projectId, 'insight'] as const,
  tasks: (filters: Record<string, unknown> = {}) =>
    [...v3QueryKeys.all, 'tasks', filters] as const,
  task: (taskId: string) => [...v3QueryKeys.all, 'task', taskId] as const,
  taskMessages: (taskId: string) =>
    [...v3QueryKeys.all, 'task', taskId, 'messages'] as const,
  taskRuns: (taskId: string, filters?: Record<string, unknown>) =>
    filters
      ? [...v3QueryKeys.all, 'task', taskId, 'runs', filters] as const
      : [...v3QueryKeys.all, 'task', taskId, 'runs'] as const,
  run: (runId: string) => [...v3QueryKeys.all, 'run', runId] as const,
  runSteps: (runId: string) => [...v3QueryKeys.all, 'run', runId, 'steps'] as const,
  approvals: (filters: Record<string, unknown> = {}) =>
    [...v3QueryKeys.all, 'approvals', filters] as const,
  approval: (approvalId: string) =>
    [...v3QueryKeys.all, 'approval', approvalId] as const,
  artifacts: (filters: Record<string, unknown> = {}) =>
    [...v3QueryKeys.all, 'artifacts', filters] as const,
  artifact: (artifactId: string) =>
    [...v3QueryKeys.all, 'artifact', artifactId] as const,
  workflows: (filters: Record<string, unknown> = {}) =>
    [...v3QueryKeys.all, 'workflows', filters] as const,
  workflow: (workflowId: string) =>
    [...v3QueryKeys.all, 'workflow', workflowId] as const,
  workflowBindings: (filters: Record<string, unknown> = {}) =>
    [...v3QueryKeys.all, 'workflow-bindings', filters] as const,
}

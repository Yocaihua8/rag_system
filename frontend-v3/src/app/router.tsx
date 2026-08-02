import { createHashRouter, Navigate } from 'react-router-dom'
import { AppShell } from '../components/AppShell'
import { ProjectRoute } from '../features/projects/ProjectRoute'
import { TasksRoute } from '../features/tasks/TasksRoute'
import { WorkflowsRoute } from '../features/workflows/WorkflowsRoute'
import { SettingsPage } from '../pages/SettingsPage'

export const router = createHashRouter([
  {
    path: '/',
    element: <AppShell />,
    errorElement: <RouteError />,
    children: [
      { index: true, element: <Navigate to="/tasks" replace /> },
      { path: 'tasks', element: <TasksRoute /> },
      { path: 'tasks/new', element: <TasksRoute /> },
      { path: 'tasks/:taskId', element: <TasksRoute /> },
      { path: 'projects', element: <ProjectRoute /> },
      { path: 'projects/:projectId/overview', element: <ProjectRoute /> },
      { path: 'workflows', element: <WorkflowsRoute /> },
      { path: 'workflows/:workflowId', element: <WorkflowsRoute /> },
      { path: 'workflows/:workflowId/graph', element: <WorkflowsRoute /> },
      { path: 'settings', element: <Navigate to="/settings/general" replace /> },
      { path: 'settings/:section', element: <SettingsPage /> },
    ],
  },
])

function RouteError() {
  return (
    <main className="route-error" role="alert">
      <h1>页面没有打开</h1>
      <p>当前地址无效，请返回任务首页。</p>
      <a className="button button--primary" href="#/tasks">返回任务</a>
    </main>
  )
}

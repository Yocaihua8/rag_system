import { useEffect } from 'react'
import {
  FolderKanban,
  ListChecks,
  Menu,
  MessageSquare,
  Settings,
  X,
} from 'lucide-react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { useNavigate, useParams } from 'react-router-dom'
import { ApiError } from '../api'
import { useProjects } from '../features/projects/queries'
import { useProjectTasks } from '../features/tasks/queries'
import { usePreferencesStore } from '../store/preferencesStore'
import { useUiStore } from '../store/uiStore'
import { TaskHistory } from './TaskHistory'

const primaryNavigation = [
  { to: '/tasks', label: '任务', icon: MessageSquare },
  { to: '/projects', label: '项目', icon: FolderKanban },
  { to: '/workflows', label: '工作流', icon: ListChecks },
  { to: '/settings/general', label: '设置', icon: Settings },
]

export function AppShell() {
  const location = useLocation()
  const navigate = useNavigate()
  const params = useParams()
  const drawer = useUiStore((state) => state.drawer)
  const openDrawer = useUiStore((state) => state.openDrawer)
  const closeDrawer = useUiStore((state) => state.closeDrawer)
  const theme = usePreferencesStore((state) => state.theme)
  const projects = useProjects()
  const tasks = useProjectTasks(projects.selectedProjectId)

  useEffect(() => {
    document.documentElement.dataset.theme = theme
  }, [theme])

  useEffect(() => {
    closeDrawer()
  }, [location.pathname, closeDrawer])

  return (
    <div className="app-shell">
      <nav className="primary-nav" aria-label="主导航">
        <div className="brand-mark" aria-label="Knowledge Island">
          KI
        </div>
        {primaryNavigation.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) => `primary-nav__link${isActive ? ' is-active' : ''}`}
          >
            <Icon aria-hidden="true" />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>

      <div className={`history-region${drawer === 'history' ? ' is-open' : ''}`}>
        <div className="drawer-mobile-header">
          <strong>任务历史</strong>
          <button className="icon-button" type="button" aria-label="关闭任务历史" onClick={closeDrawer}>
            <X aria-hidden="true" />
          </button>
        </div>
        <TaskHistory
          projectName={projects.selectedProject?.name}
          tasks={(tasks.data?.items ?? []).map((task) => ({
            id: task.id,
            title: task.title,
            statusLabel: taskStatusLabel(task.status),
            statusTone: taskStatusTone(task.status),
          }))}
          currentTaskId={params.taskId}
          canCreateTask={Boolean(projects.selectedProjectId)}
          loading={projects.isLoading || tasks.isLoading}
          error={errorMessage(projects.error ?? tasks.error)}
          onCreateTask={() => navigate('/tasks/new')}
          onSelectTask={(taskId) => navigate(`/tasks/${taskId}`)}
        />
      </div>

      {drawer === 'history' ? (
        <button className="drawer-scrim" type="button" aria-label="关闭任务历史" onClick={closeDrawer} />
      ) : null}

      <main className="main-region">
        <button
          className="icon-button history-toggle"
          type="button"
          aria-label="打开任务历史"
          onClick={() => openDrawer('history')}
        >
          <Menu aria-hidden="true" />
        </button>
        <Outlet />
      </main>
    </div>
  )
}

function errorMessage(error: unknown): string | undefined {
  if (!error) return undefined
  return error instanceof ApiError ? error.message : '请检查后端连接后重试。'
}

function taskStatusLabel(status: string): string {
  return {
    queued: '正在准备', running: '正在处理', waiting_approval: '等你确认', paused: '已暂停',
    completed: '已完成', failed: '需要处理', cancelled: '已停止',
  }[status] ?? status
}

function taskStatusTone(status: string): 'neutral' | 'running' | 'warning' | 'danger' | 'success' {
  if (status === 'running' || status === 'queued') return 'running'
  if (status === 'waiting_approval' || status === 'paused') return 'warning'
  if (status === 'failed' || status === 'cancelled') return 'danger'
  if (status === 'completed') return 'success'
  return 'neutral'
}

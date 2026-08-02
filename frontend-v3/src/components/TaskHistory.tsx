import { Plus } from 'lucide-react'

export interface TaskHistoryItem {
  id: string
  title: string
  statusLabel: string
  statusTone: 'neutral' | 'running' | 'warning' | 'danger' | 'success'
}

interface TaskHistoryProps {
  projectName?: string
  tasks?: TaskHistoryItem[]
  currentTaskId?: string
  canCreateTask?: boolean
  onCreateTask?: () => void
  onSelectTask?: (taskId: string) => void
  loading?: boolean
  error?: string
}

export function TaskHistory({
  projectName,
  tasks = [],
  currentTaskId,
  canCreateTask = false,
  onCreateTask,
  onSelectTask,
  loading = false,
  error,
}: TaskHistoryProps) {
  return (
    <aside className="task-history" aria-label="项目和任务历史">
      <div className="task-history__header">
        <p className="context-label">正在处理</p>
        <strong>{projectName ?? '尚未选择项目'}</strong>
        <button
          className="button button--primary button--block"
          type="button"
          disabled={!canCreateTask}
          onClick={onCreateTask}
        >
          <Plus aria-hidden="true" />
          新建任务
        </button>
      </div>
      <div className="task-history__list">
        {loading ? <div className="history-empty" role="status">正在加载任务…</div> : null}
        {error ? <div className="history-empty" role="alert"><p>任务没有加载成功。</p><span>{error}</span></div> : null}
        {!loading && !error && tasks.length === 0 ? (
          <div className="history-empty" role="status">
            <p>还没有可显示的任务。</p>
            <span>{projectName ? '创建任务后会显示在这里。' : '选择项目后才能创建任务。'}</span>
          </div>
        ) : !loading && !error ? (
          tasks.map((task) => (
            <button
              className="history-item"
              type="button"
              key={task.id}
              aria-current={task.id === currentTaskId ? 'true' : undefined}
              onClick={() => onSelectTask?.(task.id)}
            >
              <span>
                <strong>{task.title}</strong>
                <small>{task.statusLabel}</small>
              </span>
              <span className={`status-dot status-dot--${task.statusTone}`} aria-hidden="true" />
            </button>
          ))
        ) : null}
      </div>
    </aside>
  )
}

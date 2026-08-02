import type { TaskStatus } from './taskTypes'

interface TaskProgressProps {
  status: TaskStatus
  currentStep?: number
  totalSteps?: number
}

function phaseForStatus(status: TaskStatus) {
  if (['empty', 'loading', 'queued', 'offline'].includes(status)) return 0
  if (['running', 'paused', 'failed', 'recovery_required', 'cancelled'].includes(status)) return 1
  if (status === 'waiting_approval') return 2
  return 3
}

export function TaskProgress({ status, currentStep, totalSteps }: TaskProgressProps) {
  const phase = phaseForStatus(status)
  const labels = ['理解需求', '正在处理', status === 'completed' ? '已完成' : '等你确认']
  return (
    <ol className="task-progress" aria-label="任务进度">
      {labels.map((label, index) => (
        <li key={label} className={index < phase ? 'is-done' : index === phase ? 'is-current' : ''} aria-current={index === phase ? 'step' : undefined}>
          <span className="progress-mark" aria-hidden="true" />
          <span>{label}</span>
          {index === 1 && totalSteps ? <small>{currentStep ?? 0}/{totalSteps} 步</small> : null}
        </li>
      ))}
    </ol>
  )
}

import { useEffect, useMemo, useRef, useState } from 'react'
import {
  Circle,
  CircleAlert,
  CircleCheck,
  Clock3,
  FolderKanban,
  LoaderCircle,
  PanelRight,
  PauseCircle,
  ShieldAlert,
  ShieldCheck,
  Square,
  WifiOff,
  type LucideIcon,
  X,
} from 'lucide-react'
import { TaskComposer } from '../components/TaskComposer'
import { TaskDetailsDrawer } from '../components/TaskDetailsDrawer'
import { TaskProgress } from '../components/TaskProgress'
import { TaskStatePanel } from '../components/TaskStatePanel'
import { TaskTimeline } from '../components/TaskTimeline'
import type { ApprovalSummary, TaskFailureSummary, TaskMessage, TaskResultSummary, TaskStatus } from '../components/taskTypes'
import type { ProcessingPreference } from '../store/preferencesStore'
import { useUiStore } from '../store/uiStore'

export interface TasksPageProps {
  projectId?: string
  projectName?: string
  taskId?: string
  taskTitle?: string
  status?: TaskStatus
  messages?: TaskMessage[]
  serviceAvailable?: boolean
  online?: boolean
  commandPending?: boolean
  currentStep?: number
  totalSteps?: number
  approval?: ApprovalSummary
  failure?: TaskFailureSummary
  results?: TaskResultSummary[]
  onSubmit?: (content: string) => void | Promise<void>
  onPause?: () => void
  onResume?: () => void
  onStop?: () => void
  onRetry?: () => void
  onApprove?: () => void
  onReject?: () => void
  onViewResult?: () => void
  plan?: string[]
  artifactCount?: number
  runLabel?: string
  artifacts?: Array<{ id: string; name: string; status: string; content: string; runLabel?: string }>
  error?: string
  actionNotice?: string
  depth?: ProcessingPreference
  onDepthChange?: (depth: ProcessingPreference) => void
}

export function TasksPage({
  projectId,
  projectName,
  taskId,
  taskTitle,
  status = 'empty',
  messages = [],
  serviceAvailable = false,
  online = true,
  commandPending = false,
  currentStep,
  totalSteps,
  approval,
  failure,
  results,
  onSubmit,
  onPause,
  onResume,
  onStop,
  onRetry,
  onApprove,
  onReject,
  onViewResult,
  plan,
  artifactCount,
  runLabel,
  artifacts,
  error,
  actionNotice,
  depth = 'standard',
  onDepthChange,
}: TasksPageProps) {
  const timelineRef = useRef<HTMLDivElement>(null)
  const [followLatest, setFollowLatest] = useState(true)
  const [optionsOpen, setOptionsOpen] = useState(false)
  const [stopConfirmOpen, setStopConfirmOpen] = useState(false)
  const [resultRequested, setResultRequested] = useState(false)
  const drawer = useUiStore((state) => state.drawer)
  const openDrawer = useUiStore((state) => state.openDrawer)
  const closeDrawer = useUiStore((state) => state.closeDrawer)
  const draftKey = `${projectId ?? 'no-project'}:${taskId ?? 'new'}`
  const effectiveStatus = online ? status : 'offline'
  const submitting = commandPending || effectiveStatus === 'queued'
  const inputLocked = ['loading', 'queued', 'running', 'paused', 'waiting_approval', 'recovery_required'].includes(effectiveStatus)
  const statusPresentation = error
    ? { label: '同步异常', Icon: CircleAlert }
    : taskStatusPresentation(effectiveStatus)
  const readyArtifactIds = useMemo(
    () => new Set((artifacts ?? []).filter((artifact) => artifact.status === 'ready').map((artifact) => artifact.id)),
    [artifacts],
  )
  const readyResults = results?.filter((result) => readyArtifactIds.has(result.id))
  const hasReadyResult = Boolean(readyResults?.length)

  useEffect(() => {
    if (!followLatest || !timelineRef.current) return
    timelineRef.current.scrollTop = timelineRef.current.scrollHeight
  }, [messages, effectiveStatus, followLatest])

  const handleTimelineScroll = () => {
    const node = timelineRef.current
    if (!node) return
    setFollowLatest(node.scrollHeight - node.scrollTop - node.clientHeight < 48)
  }

  return (
    <div className={`tasks-page${projectId ? '' : ' tasks-page--project-required'}`}>
      <header className="page-toolbar">
        <div>
          <p className="context-label">{projectName ? `${projectName} · 项目固定` : '尚未选择项目'}</p>
          <h1>{taskTitle ?? '新任务'}</h1>
        </div>
        <div className="toolbar-actions">
          <span className={`status-badge status-badge--${error ? 'failed' : effectiveStatus}`}>
            {projectId ? <statusPresentation.Icon aria-hidden="true" /> : <FolderKanban aria-hidden="true" />}
            {projectId ? statusPresentation.label : '先选择项目'}
          </span>
          {projectId ? (
            <button className="icon-button" type="button" aria-label="打开详细过程" onClick={() => openDrawer('details')}>
              <PanelRight aria-hidden="true" />
            </button>
          ) : null}
        </div>
      </header>

      {!projectId ? (
        <div className="timeline-region project-required-region">
          <section className="project-required" aria-labelledby="project-required-title">
            <FolderKanban aria-hidden="true" />
            <h2 id="project-required-title">先选择一个项目</h2>
            <p>任务会保存在所选项目中，建立后不会自动切换。</p>
            <a className="button button--primary" href="#/projects">添加或选择项目</a>
            {error ? <p className="project-required__error" role="alert">项目列表暂时没有加载成功，请检查连接后重试。</p> : null}
          </section>
        </div>
      ) : (
        <>
          {!error ? <TaskProgress status={effectiveStatus} currentStep={currentStep} totalSteps={totalSteps} /> : null}

          <div className="timeline-region" ref={timelineRef} onScroll={handleTimelineScroll}>
            <TaskTimeline messages={messages} loading={effectiveStatus === 'loading'} />
            {error ? (
              <section className="state-panel state-panel--danger" role="alert">
                <h3><CircleAlert aria-hidden="true" />任务暂时没有同步成功</h3>
                <p><strong>发生了什么：</strong>应用暂时无法读取最新任务状态。</p>
                <p className="safe-copy"><strong>数据是否安全：</strong>本地草稿仍会保留，应用不会自动重复提交。</p>
                <p><strong>下一步：</strong>检查连接后，再手动尝试刚才的操作。</p>
                <details className="technical-details"><summary>查看技术信息</summary><pre>{error}</pre></details>
              </section>
            ) : (
              <>
                {actionNotice ? <p className="action-notice" role="status">{actionNotice}</p> : null}
                <TaskStatePanel
                  status={effectiveStatus}
                  commandPending={commandPending}
                  approval={approval}
                  failure={failure}
                  results={readyResults}
                  onPause={onPause}
                  onResume={onResume}
                  onStop={onStop ? () => setStopConfirmOpen(true) : undefined}
                  onRetry={onRetry}
                  onApprove={onApprove}
                  onReject={onReject}
                  onViewResult={hasReadyResult && onViewResult ? () => { setResultRequested(true); onViewResult() } : undefined}
                />
              </>
            )}
          </div>

          {!followLatest ? <button className="button button--primary new-progress" type="button" onClick={() => setFollowLatest(true)}>有新进展</button> : null}

          <TaskComposer
            draftKey={draftKey}
            serviceAvailable={serviceAvailable}
            online={online}
            submitting={submitting}
            locked={inputLocked}
            onSubmit={onSubmit}
            onOpenOptions={() => setOptionsOpen(true)}
          />
        </>
      )}

      <TaskDetailsDrawer open={drawer === 'details'} onClose={() => { setResultRequested(false); closeDrawer() }} plan={plan} artifactCount={artifactCount} runLabel={runLabel} artifacts={artifacts} revealFirstReady={resultRequested} />
      {drawer === 'details' ? <button className="drawer-scrim" type="button" aria-label="关闭详细过程" onClick={() => { setResultRequested(false); closeDrawer() }} /> : null}

      {optionsOpen ? (
        <div className="modal-layer" role="presentation">
          <section className="modal" role="dialog" aria-modal="true" aria-labelledby="task-options-title">
            <div className="modal__header"><h2 id="task-options-title">任务选项</h2><button className="icon-button" type="button" aria-label="关闭任务选项" onClick={() => setOptionsOpen(false)}><X aria-hidden="true" /></button></div>
            <p>这些选项只影响当前任务，不会修改全局设置。</p>
            <label className="field-label" htmlFor="task-depth">处理方式</label>
            <select className="field-control" id="task-depth" value={depth} disabled={Boolean(taskId)} onChange={(event) => onDepthChange?.(event.target.value as ProcessingPreference)}>
              <option value="quick">快速处理</option>
              <option value="standard">普通处理（推荐）</option>
              <option value="deep">深入处理</option>
            </select>
            {taskId ? <p className="inline-notice">任务已建立，处理选项已冻结。</p> : null}
            <div className="modal__actions"><button className="button button--primary" type="button" onClick={() => setOptionsOpen(false)}>完成</button></div>
          </section>
        </div>
      ) : null}
      {stopConfirmOpen ? (
        <div className="modal-layer" role="presentation">
          <section className="modal" role="dialog" aria-modal="true" aria-labelledby="stop-task-title">
            <div className="modal__header"><h2 id="stop-task-title">停止未完成步骤？</h2><button className="icon-button" type="button" aria-label="返回任务" onClick={() => setStopConfirmOpen(false)}><X aria-hidden="true" /></button></div>
            <p>已完成的内容会保留，尚未开始的步骤不会继续。</p>
            <p className="safe-copy">{onPause ? '更安全的选择是先暂停，之后仍可继续。' : '停止后会保留已经完成的内容。'}</p>
            <div className="modal__actions modal__actions--wrap">
              <button className="button button--secondary" type="button" onClick={() => setStopConfirmOpen(false)}>返回</button>
              {onPause ? <button className="button button--primary" type="button" onClick={() => { setStopConfirmOpen(false); onPause() }}>先暂停（推荐）</button> : null}
              <button className="button button--danger" type="button" onClick={() => { setStopConfirmOpen(false); onStop?.() }}>确认停止</button>
            </div>
          </section>
        </div>
      ) : null}
    </div>
  )
}

function taskStatusPresentation(status: TaskStatus): { label: string; Icon: LucideIcon } {
  const presentations: Record<TaskStatus, { label: string; Icon: LucideIcon }> = {
    empty: { label: '还没开始', Icon: Circle },
    loading: { label: '正在加载', Icon: LoaderCircle },
    queued: { label: '正在准备', Icon: Clock3 },
    running: { label: '正在处理', Icon: LoaderCircle },
    paused: { label: '已暂停', Icon: PauseCircle },
    waiting_approval: { label: '等你确认', Icon: ShieldCheck },
    failed: { label: '需要处理', Icon: CircleAlert },
    recovery_required: { label: '需要检查', Icon: ShieldAlert },
    offline: { label: '当前离线', Icon: WifiOff },
    completed: { label: '已完成', Icon: CircleCheck },
    cancelled: { label: '已停止', Icon: Square },
  }
  return presentations[status]
}

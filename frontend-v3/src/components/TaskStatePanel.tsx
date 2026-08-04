import { useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import {
  CircleAlert,
  CircleCheck,
  Clock3,
  LoaderCircle,
  Pause,
  Play,
  RotateCw,
  ShieldAlert,
  ShieldCheck,
  Square,
  WifiOff,
} from 'lucide-react'
import type { ApprovalSummary, TaskFailureSummary, TaskResultSummary, TaskStatus } from './taskTypes'

interface TaskStatePanelProps {
  status: TaskStatus
  commandPending?: boolean
  approval?: ApprovalSummary
  failure?: TaskFailureSummary
  results?: TaskResultSummary[]
  onPause?: () => void
  onResume?: () => void
  onStop?: () => void
  onRetry?: () => void
  onApprove?: () => void
  onReject?: () => void
  onViewResult?: () => void
}

export function TaskStatePanel(props: TaskStatePanelProps) {
  const [approvalConfirmOpen, setApprovalConfirmOpen] = useState(false)
  const approvalTriggerRef = useRef<HTMLButtonElement>(null)
  const approvalDialogRef = useRef<HTMLElement>(null)
  const approvalReturnRef = useRef<HTMLButtonElement>(null)
  const disabled = Boolean(props.commandPending)

  useEffect(() => {
    if (!approvalConfirmOpen) return
    const frame = requestAnimationFrame(() => approvalReturnRef.current?.focus())
    const handleKeyDown = (event: globalThis.KeyboardEvent) => {
      if (event.key === 'Escape') {
        event.preventDefault()
        setApprovalConfirmOpen(false)
        return
      }
      if (event.key !== 'Tab' || !approvalDialogRef.current) return
      const controls = Array.from(
        approvalDialogRef.current.querySelectorAll<HTMLElement>('button:not(:disabled), [href], [tabindex]:not([tabindex="-1"])'),
      )
      if (!controls.length) return
      const first = controls[0]
      const last = controls[controls.length - 1]
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault()
        last.focus()
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault()
        first.focus()
      }
    }
    document.addEventListener('keydown', handleKeyDown)
    return () => {
      cancelAnimationFrame(frame)
      document.removeEventListener('keydown', handleKeyDown)
      approvalTriggerRef.current?.focus()
    }
  }, [approvalConfirmOpen])
  switch (props.status) {
    case 'running':
      return (
        <section className="state-panel" aria-label="当前任务状态">
          <h3>正在处理当前步骤</h3>
          <p>新进展会继续显示在同一个回答中。</p>
          <div className="action-row">
            <button className="button button--secondary" type="button" disabled={disabled || !props.onPause} onClick={props.onPause}>
              <Pause aria-hidden="true" />{disabled ? '正在暂停…' : '先暂停'}
            </button>
            <button className="button button--secondary" type="button" disabled={disabled || !props.onStop} onClick={props.onStop}>
              <Square aria-hidden="true" />停止未完成步骤
            </button>
          </div>
        </section>
      )
    case 'paused':
      return (
        <section className="state-panel" aria-label="当前任务状态">
          <h3><Pause aria-hidden="true" />已暂停</h3>
          <p className="safe-copy">已完成的内容仍然保留。</p>
          <button className="button button--primary" type="button" disabled={disabled || !props.onResume} onClick={props.onResume}>
            <Play aria-hidden="true" />{disabled ? '正在继续…' : '继续处理'}
          </button>
        </section>
      )
    case 'waiting_approval':
      return (
        <section className="state-panel state-panel--approval" aria-label="等待确认">
          <h3><ShieldCheck aria-hidden="true" />需要你确认一次</h3>
          {props.approval ? (
            <dl className="impact-list">
              <div><dt>将做什么</dt><dd>{props.approval.action}</dd></div>
              <div><dt>影响哪里</dt><dd>{props.approval.target}</dd></div>
              <div><dt>不会修改</dt><dd>{props.approval.unchanged}</dd></div>
              <div><dt>能否撤销</dt><dd>{props.approval.undo}</dd></div>
            </dl>
          ) : <p>确认详情尚未加载，当前不能继续。</p>}
          <div className="action-row">
            <button ref={approvalTriggerRef} className="button button--primary" type="button" disabled={disabled || !props.approval || !props.onApprove} onClick={() => setApprovalConfirmOpen(true)}>查看并确认</button>
            <button className="button button--secondary" type="button" disabled={disabled || !props.approval || !props.onReject} onClick={props.onReject}>拒绝并停止本次任务（更安全）</button>
          </div>
          {approvalConfirmOpen && props.approval ? createPortal(
            <div className="modal-layer" role="presentation">
              <section ref={approvalDialogRef} className="modal" role="dialog" aria-modal="true" aria-labelledby="approval-final-title">
                <h2 id="approval-final-title">最后确认：执行这项操作？</h2>
                <p>将执行：{props.approval.action}</p>
                <p>影响范围：{props.approval.target}</p>
                <p>撤销说明：{props.approval.undo}</p>
                <div className="modal__actions modal__actions--wrap">
                  <button ref={approvalReturnRef} className="button button--secondary" type="button" onClick={() => setApprovalConfirmOpen(false)}>返回检查（推荐）</button>
                  <button className="button button--primary" type="button" disabled={disabled} onClick={() => { setApprovalConfirmOpen(false); props.onApprove?.() }}>确认执行</button>
                </div>
              </section>
            </div>,
            document.body,
          ) : null}
        </section>
      )
    case 'failed':
      return (
        <section className="state-panel state-panel--danger" aria-label="任务失败">
          <h3><CircleAlert aria-hidden="true" />处理没有完成</h3>
          {props.failure ? (
            <>
              <p><strong>发生了什么：</strong>{props.failure.whatHappened}</p>
              <p className="safe-copy"><strong>数据是否安全：</strong>{props.failure.dataSafety}</p>
              <p><strong>下一步：</strong>{props.failure.nextStep}</p>
              {props.failure.technicalDetails ? <details className="technical-details"><summary>查看技术信息</summary><pre>{props.failure.technicalDetails}</pre></details> : null}
            </>
          ) : (
            <p>失败详情尚未加载。为避免重复操作，当前不会自动重试。</p>
          )}
          <button className="button button--primary" type="button" disabled={disabled || !props.failure || !props.onRetry} onClick={props.onRetry}>
            <RotateCw aria-hidden="true" />{disabled ? '正在重试…' : '重新尝试'}
          </button>
        </section>
      )
    case 'recovery_required':
      return (
        <section className="state-panel state-panel--warning" aria-label="需要恢复确认">
          <h3><ShieldAlert aria-hidden="true" />先检查，再继续</h3>
          <p><strong>发生了什么：</strong>上次写入结果无法确定。</p>
          <p className="safe-copy"><strong>数据是否安全：</strong>系统没有自动重试。</p>
          <p><strong>下一步：</strong>查看详细过程；当前可以安全停止并保留已完成内容。</p>
          <button className="button button--secondary" type="button" disabled={disabled || !props.onStop} onClick={props.onStop}>
            <Square aria-hidden="true" />停止并保留现场
          </button>
        </section>
      )
    case 'offline':
      return (
        <section className="state-panel" aria-label="当前离线">
          <h3><WifiOff aria-hidden="true" />当前离线</h3>
          <p>已加载的内容和本地草稿会保留。恢复连接后不会自动发送。</p>
        </section>
      )
    case 'completed':
      return (
        <section className="state-panel state-panel--success" aria-label="任务已完成">
          <h3><CircleCheck aria-hidden="true" />处理完成</h3>
          {props.results?.length ? (
            <ul className="result-list">{props.results.map((result) => <li key={result.id}><strong>{result.title}</strong><span>{result.description}</span></li>)}</ul>
          ) : <p>服务端尚未返回可显示的结果。</p>}
          <button className="button button--primary" type="button" disabled={!props.results?.length || !props.onViewResult} onClick={props.onViewResult}>查看结果</button>
          <p className="recommended-next">推荐下一步：先检查结果，再决定是否创建后续任务。</p>
        </section>
      )
    case 'cancelled':
      return <section className="state-panel" aria-label="任务已停止"><h3><Square aria-hidden="true" />已停止未完成步骤</h3><p>已完成的内容仍然保留。</p></section>
    case 'queued':
      return <section className="state-panel" aria-label="任务正在准备"><h3><Clock3 aria-hidden="true" />已收到，正在准备</h3><p>任务开始后会显示当前步骤。</p></section>
    case 'loading':
      return <section className="state-panel" aria-label="正在加载"><h3><LoaderCircle aria-hidden="true" />正在加载任务</h3><p>请稍等，不需要重复操作。</p></section>
    case 'empty':
      return null
    default:
      return null
  }
}

import { FormEvent, KeyboardEvent, useRef, useState } from 'react'
import { ListTodo, SearchCheck, Send, SlidersHorizontal, Files } from 'lucide-react'
import { useDraftStore } from '../store/draftStore'

const quickActions = [
  { id: 'find', label: '找出问题', help: '先检查，再给出清单', icon: SearchCheck, prompt: '请检查项目，找出最需要先处理的问题。', available: true },
  { id: 'organize', label: '整理资料', help: '后端能力尚未开放', icon: Files, prompt: '', available: false },
  { id: 'plan', label: '做一份计划', help: '后端能力尚未开放', icon: ListTodo, prompt: '', available: false },
]

interface TaskComposerProps {
  draftKey: string
  serviceAvailable: boolean
  online: boolean
  submitting: boolean
  locked?: boolean
  onSubmit?: (content: string) => void | Promise<void>
  onOpenOptions: () => void
}

export function TaskComposer({
  draftKey,
  serviceAvailable,
  online,
  submitting,
  locked = false,
  onSubmit,
  onOpenOptions,
}: TaskComposerProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const submitInFlight = useRef(false)
  const value = useDraftStore((state) => state.drafts[draftKey] ?? '')
  const setDraft = useDraftStore((state) => state.setDraft)
  const clearDraft = useDraftStore((state) => state.clearDraft)
  const [feedback, setFeedback] = useState('')
  const [locallySubmitting, setLocallySubmitting] = useState(false)
  const busy = submitting || locallySubmitting
  const canSubmit = serviceAvailable && online && !busy && !locked && Boolean(onSubmit)
  const availabilityMessage = !online
    ? '当前离线：可以继续写草稿，恢复连接后请手动发送。'
    : !serviceAvailable || !onSubmit
      ? '任务服务尚未连接：可以先写草稿，当前不会发送。'
      : locked
        ? '当前任务正在处理，请先完成当前操作。'
        : ''

  const chooseQuickAction = (prompt: string) => {
    setDraft(draftKey, prompt)
    setFeedback('已填入建议，你可以继续修改。')
    requestAnimationFrame(() => textareaRef.current?.focus())
  }

  const submit = async () => {
    if (submitInFlight.current) return
    const content = value.trim()
    if (!content) {
      setFeedback('请先告诉我你想完成什么。')
      textareaRef.current?.focus()
      return
    }
    if (!canSubmit) {
      setFeedback(online ? '任务服务尚未连接，草稿已保留，未发送。' : '当前离线，草稿已保留，恢复连接后请手动发送。')
      return
    }
    submitInFlight.current = true
    setLocallySubmitting(true)
    setFeedback('正在发送，请不要重复点击。')
    try {
      await onSubmit?.(content)
      clearDraft(draftKey)
      setFeedback('已提交，正在读取服务端状态。')
    } catch (error) {
      setFeedback(`${error instanceof Error ? error.message : '发送失败'}。草稿已保留，不会自动重复提交。`)
    } finally {
      submitInFlight.current = false
      setLocallySubmitting(false)
    }
  }

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault()
    void submit()
  }

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      void submit()
    }
  }

  return (
    <section className="composer-region" aria-label="任务输入">
      <p className="capability-notice">当前只会安全检查项目结构；输入内容会保存为任务说明，不会修改项目文件。</p>
      <div className="quick-actions" aria-label="快捷入口">
        {quickActions.map(({ id, label, help, icon: Icon, prompt, available }) => (
          <button className="quick-action" type="button" key={id} disabled={locked || !available} aria-describedby={`${id}-quick-help`} onClick={() => chooseQuickAction(prompt)}>
            <Icon aria-hidden="true" />
            <span><strong>{label}</strong><small id={`${id}-quick-help`}>{help}</small></span>
          </button>
        ))}
      </div>
      <form className="composer" onSubmit={handleSubmit}>
        <label className="sr-only" htmlFor="task-prompt">告诉 Agent 你想完成什么</label>
        <textarea
          id="task-prompt"
          ref={textareaRef}
          value={value}
          rows={2}
          placeholder="告诉我你想完成什么，我会一步一步帮你。"
          disabled={locked}
          onChange={(event) => setDraft(draftKey, event.target.value)}
          onKeyDown={handleKeyDown}
        />
        <div className="composer__footer">
          <span className="composer__hint">Enter 发送 · Shift+Enter 换行</span>
          <div className="composer__actions">
            <button className="button button--secondary" type="button" onClick={onOpenOptions}>
              <SlidersHorizontal aria-hidden="true" />
              任务选项
            </button>
            <button className="button button--primary" type="submit" disabled={!canSubmit}>
              <Send aria-hidden="true" />
              {busy ? '正在发送…' : locked ? '任务处理中' : '开始处理'}
            </button>
          </div>
        </div>
      </form>
      <p className="composer-feedback" role="status" aria-live="polite">{feedback || availabilityMessage}</p>
    </section>
  )
}

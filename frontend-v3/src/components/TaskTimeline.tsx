import { Bot, LoaderCircle } from 'lucide-react'
import type { TaskMessage } from './taskTypes'

interface TaskTimelineProps {
  messages: TaskMessage[]
  loading?: boolean
}

export function TaskTimeline({ messages, loading = false }: TaskTimelineProps) {
  if (loading) {
    return <div className="timeline-empty" role="status"><LoaderCircle className="spin" aria-hidden="true" />正在加载任务记录…</div>
  }
  if (messages.length === 0) {
    return (
      <div className="task-welcome">
        <h2>今天想先解决什么？</h2>
        <p>选择一个快捷入口，或直接在下方告诉我。</p>
      </div>
    )
  }
  return (
    <div className="message-list" aria-live="polite">
      {messages.map((message) => (
        <article className={`message message--${message.role}`} key={message.id}>
          {message.role === 'assistant' ? <span className="message-avatar"><Bot aria-hidden="true" /></span> : null}
          <div className="message-bubble">
            <p>{message.content}</p>
            {message.streaming ? <span className="streaming-label"><LoaderCircle className="spin" aria-hidden="true" />正在补充结果…</span> : null}
          </div>
        </article>
      ))}
    </div>
  )
}

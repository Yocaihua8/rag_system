export type TaskStatus =
  | 'empty'
  | 'loading'
  | 'queued'
  | 'running'
  | 'paused'
  | 'waiting_approval'
  | 'failed'
  | 'recovery_required'
  | 'offline'
  | 'completed'
  | 'cancelled'

export interface TaskMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  streaming?: boolean
}

export interface ApprovalSummary {
  action: string
  target: string
  unchanged: string
  undo: string
}

export interface TaskResultSummary {
  id: string
  title: string
  description: string
}

export interface TaskFailureSummary {
  whatHappened: string
  dataSafety: string
  nextStep: string
  technicalDetails?: string
}

import { useState } from 'react'
import { GitBranch, Plus } from 'lucide-react'
import { workflowStepLabel } from '../components/workflowLabels'

export interface WorkflowSummary {
  id: string
  name: string
  statusLabel: string
  steps: string[]
}

interface WorkflowsPageProps {
  workflows?: WorkflowSummary[]
  selectedWorkflow?: WorkflowSummary
  loading?: boolean
  error?: string
  onSelect?: (workflowId: string) => void
  onStart?: (message: string) => Promise<void>
  startPending?: boolean
}

export function WorkflowsPage({ workflows = [], selectedWorkflow, loading = false, error, onSelect, onStart, startPending = false }: WorkflowsPageProps) {
  const [message, setMessage] = useState('')
  return (
    <div className="standard-page">
      <header className="standard-page__header">
        <div><p className="context-label">工作流</p><h1>工作流</h1><p>把重复任务保存为可复用步骤。</p></div>
        <button className="button button--primary" type="button" disabled title="此功能尚未开放"><Plus aria-hidden="true" />新建工作流</button>
      </header>
      {loading ? <section className="page-state" role="status">正在加载工作流…</section> : null}
      {error ? <section className="page-state page-state--error" role="alert"><h2>工作流没有加载成功</h2><p>{error}</p></section> : null}
      {!loading && !error && workflows.length === 0 ? (
        <section className="page-state">
          <GitBranch aria-hidden="true" />
          <h2>还没有可显示的工作流</h2>
          <p>创建工作流后，会在这里显示可以重复使用的步骤。</p>
          <button className="button button--secondary" type="button" disabled>编辑流程图（请先选择工作流）</button>
        </section>
      ) : null}
      <div className="capability-notice capability-notice--warning" role="status"><strong>目前可以查看步骤</strong><p>编辑功能尚未开放，现有工作流不会被修改。</p></div>
      {selectedWorkflow ? <section className="content-section"><h2>{selectedWorkflow.name}</h2><span className="status-badge">{selectedWorkflow.statusLabel}</span>{selectedWorkflow.steps.length ? <ol>{selectedWorkflow.steps.map((step, index) => <li key={`${index}-${step}`}>{workflowStepLabel(step)}</li>)}</ol> : <p>这个版本暂时没有可显示的步骤。</p>}{onStart ? <form onSubmit={(event) => { event.preventDefault(); if (message.trim()) void onStart(message.trim()).then(() => setMessage('')) }}><label className="field-label" htmlFor="workflow-message">本次任务</label><textarea className="field-control" id="workflow-message" value={message} onChange={(event) => setMessage(event.target.value)} placeholder="说明这次要检查什么" /><button className="button button--primary" type="submit" disabled={startPending || !message.trim()}>{startPending ? '正在启动…' : '启动此工作流'}</button></form> : <p className="inline-notice">当前项目没有可执行的已绑定版本。</p>}<button className="button button--secondary" type="button" disabled>编辑流程图（尚未开放）</button></section> : null}
      <div className="workflow-list">
        {workflows.map((workflow) => (
          <article className="workflow-row" key={workflow.id}>
            <div><h2>{workflow.name}</h2><span className="status-badge">{workflow.statusLabel}</span>{workflow.steps.length ? <ol>{workflow.steps.map((step) => <li key={step}>{step}</li>)}</ol> : <p>选择后读取真实版本步骤。</p>}</div>
            <button className="button button--secondary" type="button" disabled={!onSelect} onClick={() => onSelect?.(workflow.id)}>查看工作流</button>
          </article>
        ))}
      </div>
    </div>
  )
}

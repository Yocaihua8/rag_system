import { useEffect, useMemo, useRef, useState } from 'react'
import { X } from 'lucide-react'
import type { ArtifactExportPreview } from '../pages/TasksPage'
import { workflowStepLabel } from './workflowLabels'

interface TaskDetailsDrawerProps {
  open: boolean
  onClose: () => void
  plan?: string[]
  sourceCount?: number
  artifactCount?: number
  runLabel?: string
  artifacts?: Array<{ id: string; name: string; status: string; content: string; runLabel?: string }>
  revealFirstReady?: boolean
  onPreviewArtifactExport?: (artifactId: string) => Promise<ArtifactExportPreview>
  onConfirmArtifactExport?: (preview: ArtifactExportPreview) => Promise<void>
  exportingArtifactId?: string
}

export function TaskDetailsDrawer({
  open,
  onClose,
  plan,
  sourceCount,
  artifactCount,
  runLabel,
  artifacts = [],
  revealFirstReady = false,
  onPreviewArtifactExport,
  onConfirmArtifactExport,
  exportingArtifactId,
}: TaskDetailsDrawerProps) {
  const [exportPreview, setExportPreview] = useState<ArtifactExportPreview>()
  const [exportArtifactId, setExportArtifactId] = useState<string>()
  const [exportError, setExportError] = useState<string>()
  const firstReadyId = useMemo(
    () => artifacts.find((artifact) => artifact.status === 'ready')?.id,
    [artifacts],
  )
  const firstReadyRef = useRef<HTMLDetailsElement>(null)

  useEffect(() => {
    if (!open || !revealFirstReady || !firstReadyId) return
    const frame = requestAnimationFrame(() => {
      firstReadyRef.current?.scrollIntoView?.({ block: 'start' })
      firstReadyRef.current?.querySelector('summary')?.focus()
    })
    return () => cancelAnimationFrame(frame)
  }, [firstReadyId, open, revealFirstReady])

  const previewExport = async (artifactId: string) => {
    if (!onPreviewArtifactExport) return
    setExportArtifactId(artifactId)
    setExportError(undefined)
    try {
      setExportPreview(await onPreviewArtifactExport(artifactId))
    } catch (error) {
      setExportError(error instanceof Error ? error.message : '无法读取导出确认信息。')
    }
  }

  const confirmExport = async () => {
    if (!exportPreview || !onConfirmArtifactExport) return
    setExportError(undefined)
    try {
      await onConfirmArtifactExport(exportPreview)
      setExportPreview(undefined)
      setExportArtifactId(undefined)
    } catch (error) {
      setExportError(error instanceof Error ? error.message : '导出没有完成。')
    }
  }

  return (
    <aside className={`details-drawer${open ? ' is-open' : ''}`} aria-label="详细过程" aria-hidden={!open}>
      <div className="details-drawer__header">
        <h2>详细过程</h2>
        <button className="icon-button" type="button" aria-label="关闭详细过程" onClick={onClose}><X aria-hidden="true" /></button>
      </div>
      <div className="details-drawer__body">
        <section><h3>处理计划</h3>{plan?.length ? <ol>{plan.map((step) => <li key={step}>{workflowStepLabel(step)}</li>)}</ol> : <p>任务开始后显示计划。</p>}</section>
        <section><h3>参考资料</h3><p>{sourceCount === undefined ? '资料尚未加载。' : `${sourceCount} 项资料`}</p></section>
        <section className="artifact-section">
          <h3>生成结果</h3>
          <p>{artifactCount === undefined ? '结果尚未加载。' : `${artifactCount} 个结果`}</p>
          {artifacts.map((artifact) => {
            const isFirstReady = artifact.id === firstReadyId
            return (
              <details
                className="artifact-result"
                key={artifact.id}
                open={isFirstReady && revealFirstReady}
                ref={isFirstReady ? firstReadyRef : undefined}
              >
                <summary tabIndex={0}>
                  {artifact.name} · {artifactStatusLabel(artifact.status)}{artifact.runLabel ? ` · ${artifact.runLabel}` : ''}
                </summary>
                <ArtifactContent content={artifact.content} />
                {artifact.status === 'ready' && onPreviewArtifactExport && onConfirmArtifactExport ? (
                  <div className="artifact-export">
                    <button className="button button--secondary" type="button" onClick={() => void previewExport(artifact.id)} disabled={exportingArtifactId === artifact.id}>
                      导出结果
                    </button>
                    {exportPreview?.artifact_id === artifact.id ? (
                      <section className="artifact-export__confirmation" aria-label="导出确认">
                        <p>将导出“{exportPreview.name}”到受管 v3 目录中的 <code>{exportPreview.target_filename}</code>（{exportPreview.content_bytes} 字节）。不会修改项目文件，也不能自动撤销。</p>
                        <div className="modal__actions">
                          <button className="button button--secondary" type="button" onClick={() => { setExportPreview(undefined); setExportArtifactId(undefined); setExportError(undefined) }} disabled={exportingArtifactId === artifact.id}>取消</button>
                          <button className="button button--primary" type="button" onClick={() => void confirmExport()} disabled={exportingArtifactId === artifact.id}>
                            {exportingArtifactId === artifact.id ? '正在导出…' : '确认导出'}
                          </button>
                        </div>
                      </section>
                    ) : null}
                    {exportArtifactId === artifact.id && exportError ? <p className="project-required__error" role="alert">{exportError}</p> : null}
                  </div>
                ) : null}
              </details>
            )
          })}
        </section>
        <section><h3>执行记录</h3><p>{runLabel ?? '运行信息尚未加载。'}</p></section>
      </div>
    </aside>
  )
}

function ArtifactContent({ content }: { content: string }) {
  const parsed = parseJson(content)
  if (isRecord(parsed)) {
    const entries = Object.entries(parsed).filter(([key]) => key in artifactFieldLabels)
    return (
      <div className="artifact-content artifact-content--summary">
        {entries.length ? (
          <dl className="artifact-summary">
            {entries.map(([key, value]) => (
              <div className="artifact-summary__item" key={key}>
                <dt>{artifactFieldLabels[key]}</dt>
                <dd>{renderArtifactValue(key, value)}</dd>
              </div>
            ))}
          </dl>
        ) : <p>结果已经生成，可以在下方查看完整数据。</p>}
        <details className="technical-details artifact-raw">
          <summary>查看原始数据</summary>
          <pre>{JSON.stringify(parsed, null, 2)}</pre>
        </details>
      </div>
    )
  }
  if (parsed !== undefined) {
    return <pre className="artifact-content artifact-content--json">{JSON.stringify(parsed, null, 2)}</pre>
  }
  return <p className="artifact-content artifact-content--text">{content || '这个结果暂时没有可显示的内容。'}</p>
}

const artifactFieldLabels: Record<string, string> = {
  root_exists: '项目位置可读取',
  total_files: '文件总数',
  supported_files: '可分析文件数',
  manifest_paths: '项目配置文件',
  top_level: '顶层内容',
  suffix_counts: '文件类型统计',
  skipped_symlinks: '已跳过的链接',
  visited_entries: '已检查条目',
  truncated: '是否提前停止',
}

function renderArtifactValue(key: string, value: unknown) {
  if (typeof value === 'boolean') return value ? '是' : '否'
  if (typeof value === 'number' || typeof value === 'string') return String(value)
  if (value === null || value === undefined) return '没有数据'
  if (key === 'top_level' && Array.isArray(value)) {
    return value.length ? (
      <ul>{value.map((item, index) => {
        if (!isRecord(item)) return <li key={index}>{String(item)}</li>
        const name = typeof item.name === 'string' ? item.name : `第 ${index + 1} 项`
        const kind = item.kind === 'directory' ? '文件夹' : item.kind === 'file' ? '文件' : ''
        return <li key={`${name}-${index}`}>{name}{kind ? `（${kind}）` : ''}</li>
      })}</ul>
    ) : '没有顶层内容'
  }
  if (Array.isArray(value)) {
    return value.length ? <ul>{value.map((item, index) => <li key={index}>{String(item)}</li>)}</ul> : '没有'
  }
  if (isRecord(value)) {
    const entries = Object.entries(value)
    return entries.length
      ? <ul>{entries.map(([name, count]) => <li key={name}>{name || '无扩展名'}：{String(count)}</li>)}</ul>
      : '没有'
  }
  return String(value)
}

function parseJson(content: string): unknown | undefined {
  try {
    return JSON.parse(content) as unknown
  } catch {
    return undefined
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function artifactStatusLabel(status: string): string {
  return {
    draft: '正在生成',
    ready: '可以查看',
    exported: '已导出',
    failed: '生成失败',
  }[status] ?? '状态未知'
}

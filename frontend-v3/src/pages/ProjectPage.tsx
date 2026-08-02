import { FormEvent, useState } from 'react'
import { FolderPlus, HelpCircle, X } from 'lucide-react'
import { Link } from 'react-router-dom'

export interface ProjectSummary {
  id: string
  name: string
  rootLabel: string
}

interface ProjectPageProps {
  project?: ProjectSummary
  projects?: ProjectSummary[]
  loading?: boolean
  error?: string
  creating?: boolean
  onCreateProject?: (name: string, rootPath: string) => void | Promise<void>
  onSelectProject?: (projectId: string) => void
}

export function ProjectPage({ project, projects = [], loading = false, error, creating = false, onCreateProject, onSelectProject }: ProjectPageProps) {
  const [dialogOpen, setDialogOpen] = useState(false)
  const [name, setName] = useState('')
  const [rootPath, setRootPath] = useState('')
  const [submitError, setSubmitError] = useState('')

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    if (!name.trim() || !rootPath.trim() || !onCreateProject) return
    setSubmitError('')
    try {
      await onCreateProject(name.trim(), rootPath.trim())
      setDialogOpen(false)
      setName('')
      setRootPath('')
    } catch (submitFailure) {
      setSubmitError(submitFailure instanceof Error ? submitFailure.message : '项目没有创建成功')
    }
  }

  return (
    <div className="standard-page">
      <header className="standard-page__header">
        <div><p className="context-label">项目</p><h1>{project?.name ?? '项目空间'}</h1><p>查看项目信息，并从整个项目发起任务。</p></div>
        <button className="button button--primary" type="button" disabled={!onCreateProject} onClick={() => setDialogOpen(true)}><FolderPlus aria-hidden="true" />添加项目</button>
      </header>
      {loading ? <section className="page-state" role="status">正在加载项目…</section> : null}
      {error ? <section className="page-state page-state--error" role="alert"><h2>项目没有加载成功</h2><p>{error}</p></section> : null}
      {!loading && !error && !project ? (
        <section className="page-state">
          <HelpCircle aria-hidden="true" />
          <h2>还没有选择项目</h2>
          <p>项目资料和洞察不会使用演示内容替代。连接项目接口后，这里会显示真实信息。</p>
          <Link className="button button--secondary" to="/tasks">返回任务</Link>
        </section>
      ) : null}
      {project ? (
        <div className="content-grid">
          {projects.length > 1 ? <section className="content-section"><h2>选择项目</h2><label className="field-label" htmlFor="project-select">当前项目</label><select id="project-select" className="field-control" value={project.id} onChange={(event) => onSelectProject?.(event.target.value)}>{projects.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></section> : null}
          <section className="content-section"><h2>项目概况</h2><dl className="summary-list"><div><dt>名称</dt><dd>{project.name}</dd></div><div><dt>位置</dt><dd>{project.rootLabel}</dd></div></dl></section>
          <section className="content-section"><h2>参考资料</h2><p>资料接口尚未接入当前前端阶段，因此不会显示占位资料。</p><button className="button button--secondary" type="button" disabled>导入资料（尚未开放）</button></section>
          <section className="content-section"><h2>项目洞察</h2><p>Overview、Knowledge、Assessments 和 Learning Plan 将在真实接口接入后开放。</p></section>
        </div>
      ) : null}
      {dialogOpen ? <div className="modal-layer" role="presentation"><form className="modal" role="dialog" aria-modal="true" aria-labelledby="create-project-title" onSubmit={submit}><div className="modal__header"><h2 id="create-project-title">添加项目</h2><button className="icon-button" type="button" aria-label="关闭添加项目" onClick={() => setDialogOpen(false)}><X aria-hidden="true" /></button></div><p>路径必须是运行后端的这台机器上已经存在的文件夹。浏览器不会上传该目录。</p><label className="field-label" htmlFor="project-name">项目名称</label><input className="field-control" id="project-name" value={name} onChange={(event) => setName(event.target.value)} required /><label className="field-label" htmlFor="project-root">现有文件夹路径</label><input className="field-control" id="project-root" value={rootPath} onChange={(event) => setRootPath(event.target.value)} placeholder="例如 E:\\Dev\\Projects\\my-project" required />{submitError ? <p role="alert">{submitError}</p> : null}<div className="modal__actions"><button className="button button--primary" type="submit" disabled={creating || !name.trim() || !rootPath.trim()}>{creating ? '正在添加…' : '确认添加'}</button></div></form></div> : null}
    </div>
  )
}

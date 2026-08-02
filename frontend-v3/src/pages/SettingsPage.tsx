import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { usePreferencesStore, type ProcessingPreference, type ThemePreference } from '../store/preferencesStore'

const settingsSections = [
  { id: 'general', label: '通用' },
  { id: 'models', label: '模型' },
  { id: 'integrations', label: '集成' },
  { id: 'data-storage', label: '数据与存储' },
  { id: 'advanced', label: '高级' },
] as const

type SettingsSection = (typeof settingsSections)[number]['id']

function isSettingsSection(value: string | undefined): value is SettingsSection {
  return settingsSections.some((section) => section.id === value)
}

export function SettingsPage() {
  const params = useParams()
  const navigate = useNavigate()
  const activeSection: SettingsSection = isSettingsSection(params.section) ? params.section : 'general'
  const [feedback, setFeedback] = useState('偏好会自动保存。')
  const theme = usePreferencesStore((state) => state.theme)
  const processing = usePreferencesStore((state) => state.processing)
  const setTheme = usePreferencesStore((state) => state.setTheme)
  const setProcessing = usePreferencesStore((state) => state.setProcessing)

  const saved = (label: string) => setFeedback(`${label}已自动保存。`)

  return (
    <div className="standard-page settings-page">
      <header className="standard-page__header"><div><p className="context-label">设置</p><h1>设置</h1><p>普通偏好自动保存，高风险操作逐步确认。</p></div></header>
      <div className="settings-layout">
        <nav className="settings-nav" role="tablist" aria-label="设置分类">
          {settingsSections.map((section) => (
            <button
              className="settings-nav__item"
              type="button"
              role="tab"
              key={section.id}
              aria-selected={activeSection === section.id}
              onClick={() => navigate(`/settings/${section.id}`)}
            >
              {section.label}
            </button>
          ))}
        </nav>
        <div className="settings-content">
          {activeSection === 'general' ? (
            <section aria-labelledby="settings-general-title">
              <h2 id="settings-general-title">通用</h2><p className="section-lead">调整界面与新任务默认体验。</p>
              <div className="setting-row"><label htmlFor="theme-setting"><strong>外观主题</strong><span>默认跟随系统。</span></label><select id="theme-setting" className="field-control" value={theme} onChange={(event) => { setTheme(event.target.value as ThemePreference); saved('外观主题') }}><option value="system">跟随系统</option><option value="light">亮色</option><option value="dark">暗色</option></select></div>
              <div className="setting-row"><label htmlFor="processing-setting"><strong>默认处理方式</strong><span>任务选项可以单独覆盖当前任务。</span></label><select id="processing-setting" className="field-control" value={processing} onChange={(event) => { setProcessing(event.target.value as ProcessingPreference); saved('默认处理方式') }}><option value="quick">快速处理</option><option value="standard">普通处理（推荐）</option><option value="deep">深入处理</option></select></div>
              <div className="setting-row"><label className="check-label check-label--disabled"><input type="checkbox" checked={false} disabled /><span><strong>任务完成提醒（尚未开放）</strong><small>当前不会发送系统通知。</small></span></label></div>
              <p className="save-feedback" role="status" aria-live="polite">{feedback}</p>
            </section>
          ) : null}
          {activeSection === 'models' ? <UnavailableSettingsSection title="模型" description="模型配置接口尚未接入当前前端。不会显示或保存明文密钥。" action="添加模型配置" /> : null}
          {activeSection === 'integrations' ? <UnavailableSettingsSection title="集成" description="集成接口尚未接入。外部写入能力不会伪装为可用。" action="管理集成" /> : null}
          {activeSection === 'data-storage' ? <UnavailableSettingsSection title="数据与存储" description="存储预检、备份和迁移接口尚未接入。为避免数据风险，迁移入口保持禁用。" action="迁移存储位置" danger /> : null}
          {activeSection === 'advanced' ? (
            <section><h2>高级</h2><p className="section-lead">技术日志和实验能力将在真实能力接入后开放。</p><button className="button button--secondary" type="button" disabled>查看详细日志（尚未开放）</button></section>
          ) : null}
        </div>
      </div>
    </div>
  )
}

function UnavailableSettingsSection({ title, description, action, danger = false }: { title: string; description: string; action: string; danger?: boolean }) {
  return (
    <section>
      <h2>{title}</h2>
      <p className="section-lead">{description}</p>
      <div className={`capability-notice${danger ? ' capability-notice--warning' : ''}`} role="status">
        <strong>当前不可用</strong>
        <p>此入口会在后端能力和安全校验接入后启用。</p>
        <button className="button button--secondary" type="button" disabled>{action}</button>
      </div>
    </section>
  )
}

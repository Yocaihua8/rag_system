import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate, useParams } from 'react-router-dom'
import { ApiError, v3Api, v3QueryKeys } from '../api'
import type { components } from '../api/generated/schema'
import { digestIntentFingerprint, useIntentKeys } from '../features/shared/useIntentKeys'
import { usePreferencesStore, type ProcessingPreference, type ThemePreference } from '../store/preferencesStore'

const settingsSections = [
  { id: 'general', label: '通用' },
  { id: 'models', label: '模型' },
  { id: 'integrations', label: '集成' },
  { id: 'data-storage', label: '数据与存储' },
  { id: 'advanced', label: '高级' },
] as const

type SettingsSection = (typeof settingsSections)[number]['id']
type ModelProfile = components['schemas']['ModelProfileResource']
type ModelProfileDraft = {
  name: string
  provider: 'api' | 'ollama'
  api_base: string
  model: string
  temperature: number
  max_tokens: number
  api_key_ref: '' | 'env:RAG_LLM_API_KEY' | 'env:DEEPSEEK_API_KEY' | 'saved:RAG_LLM_API_KEY'
  status: 'active' | 'disabled'
  is_default: boolean
}

const initialModelProfile: ModelProfileDraft = {
  name: '',
  provider: 'api',
  api_base: '',
  model: '',
  temperature: 0.7,
  max_tokens: 2048,
  api_key_ref: '',
  status: 'active',
  is_default: false,
}

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
          {activeSection === 'models' ? <ModelProfilesSettings /> : null}
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

function ModelProfilesSettings() {
  const queryClient = useQueryClient()
  const intentKeys = useIntentKeys()
  const profiles = useQuery({
    queryKey: v3QueryKeys.modelProfiles(),
    queryFn: () => v3Api.listModelProfiles(),
  })
  const [draft, setDraft] = useState<ModelProfileDraft>(initialModelProfile)
  const [editingId, setEditingId] = useState<string>()
  const [deletingId, setDeletingId] = useState<string>()
  const [feedback, setFeedback] = useState('配置只保存受控 Key 引用，不会保存或显示明文密钥。')
  const save = useMutation({
    mutationFn: async () => {
      const fingerprint = await digestIntentFingerprint([editingId ?? 'new', JSON.stringify(draft)])
      const scope = editingId ? 'model-profile-update' : 'model-profile-create'
      const request = { idempotencyKey: intentKeys.get(scope, fingerprint) }
      const result = editingId
        ? await v3Api.updateModelProfile(editingId, draft, request)
        : await v3Api.createModelProfile(draft, request)
      intentKeys.release(scope, fingerprint)
      return result
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: v3QueryKeys.modelProfiles() })
      setDraft(initialModelProfile)
      setEditingId(undefined)
      setFeedback('模型配置已保存。')
    },
  })
  const setDefault = useMutation({
    mutationFn: async (profileId: string) => {
      const fingerprint = await digestIntentFingerprint([profileId, 'set-default'])
      const result = await v3Api.setDefaultModelProfile(profileId, {
        idempotencyKey: intentKeys.get('model-profile-default', fingerprint),
      })
      intentKeys.release('model-profile-default', fingerprint)
      return result
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: v3QueryKeys.modelProfiles() })
      setFeedback('默认模型配置已更新。')
    },
  })
  const remove = useMutation({
    mutationFn: async (profileId: string) => {
      const fingerprint = await digestIntentFingerprint([profileId, 'delete'])
      const result = await v3Api.deleteModelProfile(profileId, {
        idempotencyKey: intentKeys.get('model-profile-delete', fingerprint),
      })
      intentKeys.release('model-profile-delete', fingerprint)
      return result
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: v3QueryKeys.modelProfiles() })
      setDeletingId(undefined)
      setFeedback('模型配置已删除。')
    },
  })
  const error = profiles.error ?? save.error ?? setDefault.error ?? remove.error

  const edit = (profile: ModelProfile) => {
    setEditingId(profile.id)
    setDraft({
      name: profile.name,
      provider: profile.provider,
      api_base: profile.api_base,
      model: profile.model,
      temperature: profile.temperature,
      max_tokens: profile.max_tokens,
      api_key_ref: profile.api_key_ref,
      status: profile.status,
      is_default: profile.is_default,
    })
    setFeedback('正在编辑模型配置。')
  }

  return (
    <section aria-labelledby="settings-models-title">
      <h2 id="settings-models-title">模型</h2>
      <p className="section-lead">管理 v3 的模型配置元数据。连接测试与密钥录入不在本阶段开放。</p>
      {profiles.isLoading ? <p role="status">正在读取模型配置…</p> : null}
      {error ? <p role="alert">{errorMessage(error)}</p> : null}
      {profiles.data?.items.length ? <ul className="plain-list" aria-label="模型配置列表">{profiles.data.items.map((profile) => <li key={profile.id}><div><strong>{profile.name}</strong>{profile.is_default ? <span> · 默认</span> : null}<span> · {profile.provider} / {profile.model} · {profile.status}</span><small>密钥引用：{profile.api_key_ref || '未引用'}</small></div><div className="button-row"><button className="button button--secondary" type="button" onClick={() => edit(profile)}>编辑</button><button className="button button--secondary" type="button" disabled={profile.is_default || profile.status !== 'active' || setDefault.isPending} onClick={() => void setDefault.mutateAsync(profile.id)}>设为默认</button><button className="button button--secondary" type="button" disabled={remove.isPending} onClick={() => setDeletingId(profile.id)}>删除</button></div>{deletingId === profile.id ? <div className="capability-notice capability-notice--warning"><p>删除后不可恢复，确认删除此模型配置？</p><button className="button button--secondary" type="button" disabled={remove.isPending} onClick={() => void remove.mutateAsync(profile.id)}>确认删除</button><button className="button button--secondary" type="button" disabled={remove.isPending} onClick={() => setDeletingId(undefined)}>取消</button></div> : null}</li>)}</ul> : !profiles.isLoading ? <p>尚无模型配置。不会使用演示配置替代。</p> : null}
      <form className="settings-form" onSubmit={(event) => { event.preventDefault(); void save.mutateAsync() }}>
        <h3>{editingId ? '编辑模型配置' : '添加模型配置'}</h3>
        <label className="field-label" htmlFor="model-profile-name">名称</label><input className="field-control" id="model-profile-name" value={draft.name} onChange={(event) => setDraft({ ...draft, name: event.target.value })} required />
        <label className="field-label" htmlFor="model-profile-provider">Provider</label><select className="field-control" id="model-profile-provider" value={draft.provider} onChange={(event) => setDraft({ ...draft, provider: event.target.value as ModelProfileDraft['provider'] })}><option value="api">OpenAI-compatible API</option><option value="ollama">Ollama</option></select>
        <label className="field-label" htmlFor="model-profile-base">API Base（可选）</label><input className="field-control" id="model-profile-base" value={draft.api_base} onChange={(event) => setDraft({ ...draft, api_base: event.target.value })} />
        <label className="field-label" htmlFor="model-profile-model">模型</label><input className="field-control" id="model-profile-model" value={draft.model} onChange={(event) => setDraft({ ...draft, model: event.target.value })} required />
        <label className="field-label" htmlFor="model-profile-key-ref">密钥引用</label><select className="field-control" id="model-profile-key-ref" value={draft.api_key_ref} onChange={(event) => setDraft({ ...draft, api_key_ref: event.target.value as ModelProfileDraft['api_key_ref'] })}><option value="">不引用密钥</option><option value="env:RAG_LLM_API_KEY">环境变量 RAG_LLM_API_KEY</option><option value="env:DEEPSEEK_API_KEY">环境变量 DEEPSEEK_API_KEY</option><option value="saved:RAG_LLM_API_KEY">本机兼容设置引用</option></select>
        <label className="field-label" htmlFor="model-profile-temperature">Temperature</label><input className="field-control" id="model-profile-temperature" type="number" min="0" max="2" step="0.1" value={draft.temperature} onChange={(event) => setDraft({ ...draft, temperature: Number(event.target.value) })} required />
        <label className="field-label" htmlFor="model-profile-max-tokens">最大 Token</label><input className="field-control" id="model-profile-max-tokens" type="number" min="1" max="128000" value={draft.max_tokens} onChange={(event) => setDraft({ ...draft, max_tokens: Number(event.target.value) })} required />
        <label className="check-label"><input type="checkbox" checked={draft.status === 'active'} onChange={(event) => setDraft({ ...draft, status: event.target.checked ? 'active' : 'disabled', is_default: event.target.checked ? draft.is_default : false })} /><span><strong>启用此配置</strong></span></label>
        <label className="check-label"><input type="checkbox" checked={draft.is_default} disabled={draft.status === 'disabled'} onChange={(event) => setDraft({ ...draft, is_default: event.target.checked })} /><span><strong>设为默认配置</strong></span></label>
        <div className="button-row"><button className="button button--primary" type="submit" disabled={save.isPending || !draft.name.trim() || !draft.model.trim()}>{save.isPending ? '正在保存…' : editingId ? '保存修改' : '添加模型配置'}</button>{editingId ? <button className="button button--secondary" type="button" onClick={() => { setEditingId(undefined); setDraft(initialModelProfile) }}>取消编辑</button> : null}</div>
      </form>
      <p className="save-feedback" role="status" aria-live="polite">{feedback}</p>
    </section>
  )
}

function errorMessage(error: unknown): string {
  if (error instanceof ApiError || error instanceof Error) return error.message
  return '模型配置请求失败'
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

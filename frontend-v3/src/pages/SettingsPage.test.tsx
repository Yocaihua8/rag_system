import { cleanup, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { v3Api } from '../api'
import { usePreferencesStore } from '../store/preferencesStore'
import { SettingsPage } from './SettingsPage'

function renderSettings(path = '/settings/general') {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[path]}>
        <Routes><Route path="/settings/:section" element={<SettingsPage />} /></Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('SettingsPage', () => {
  afterEach(cleanup)
  beforeEach(() => {
    vi.restoreAllMocks()
    localStorage.clear()
    usePreferencesStore.setState({ theme: 'system', processing: 'standard' })
  })

  it('auto-saves low-risk preferences with visible feedback', async () => {
    const user = userEvent.setup()
    renderSettings()

    await user.selectOptions(screen.getByLabelText(/外观主题/), 'dark')

    expect(usePreferencesStore.getState().theme).toBe('dark')
    expect(screen.getByRole('status')).toHaveTextContent('外观主题已自动保存')
  })

  it('separates data migration and keeps it disabled without backend capability', async () => {
    const user = userEvent.setup()
    renderSettings()

    await user.click(screen.getByRole('tab', { name: '数据与存储' }))

    expect(screen.getByRole('heading', { name: '数据与存储' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '迁移存储位置' })).toBeDisabled()
    expect(screen.getByText(/不会伪装为可用|保持禁用/)).toBeInTheDocument()
  })

  it('does not present completion notifications as an active preference', () => {
    renderSettings()

    expect(screen.getByRole('checkbox', { name: /任务完成提醒/ })).toBeDisabled()
    expect(screen.getByText('当前不会发送系统通知。')).toBeInTheDocument()
  })

  it('manages real v3 model profile metadata without accepting a key value', async () => {
    const user = userEvent.setup()
    vi.spyOn(v3Api, 'listModelProfiles').mockResolvedValue({ items: [] })
    const create = vi.spyOn(v3Api, 'createModelProfile').mockResolvedValue({
      profile: {
        id: 'profile-1',
        name: 'Local API',
        provider: 'api',
        api_base: '',
        model: 'demo-model',
        temperature: 0.7,
        max_tokens: 2048,
        api_key_ref: '',
        status: 'active',
        is_default: false,
        created_at: '2026-08-03T00:00:00Z',
        updated_at: '2026-08-03T00:00:00Z',
      },
      replayed: false,
    })
    renderSettings('/settings/models')

    expect(await screen.findByText('尚无模型配置。不会使用演示配置替代。')).toBeInTheDocument()
    await user.type(screen.getByLabelText('名称'), 'Local API')
    await user.type(screen.getByLabelText('模型', { selector: 'input' }), 'demo-model')
    await user.click(screen.getByRole('button', { name: '添加模型配置' }))

    await waitFor(() => expect(create).toHaveBeenCalledTimes(1))
    expect(create).toHaveBeenCalledWith(
      expect.objectContaining({ name: 'Local API', model: 'demo-model', api_key_ref: '' }),
      expect.objectContaining({ idempotencyKey: expect.any(String) }),
    )
    expect(screen.getByLabelText('密钥引用')).toBeInTheDocument()
    expect(screen.queryByLabelText(/API Key/)).not.toBeInTheDocument()
  })
})

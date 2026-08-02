import { cleanup, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { usePreferencesStore } from '../store/preferencesStore'
import { SettingsPage } from './SettingsPage'

function renderSettings(path = '/settings/general') {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes><Route path="/settings/:section" element={<SettingsPage />} /></Routes>
    </MemoryRouter>,
  )
}

describe('SettingsPage', () => {
  afterEach(cleanup)
  beforeEach(() => {
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
})

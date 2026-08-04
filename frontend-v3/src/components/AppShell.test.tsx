import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import { vi } from 'vitest'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { v3Api } from '../api'
import { AppShell } from './AppShell'

describe('AppShell', () => {
  afterEach(() => {
    cleanup()
    vi.restoreAllMocks()
  })
  it('provides four consistent primary destinations', () => {
    vi.spyOn(v3Api, 'listProjects').mockResolvedValue({ items: [] })
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={['/tasks']}>
          <Routes><Route path="/" element={<AppShell />}><Route path="tasks" element={<p>任务内容</p>} /></Route></Routes>
        </MemoryRouter>
      </QueryClientProvider>,
    )

    const navigation = screen.getByRole('navigation', { name: '主导航' })
    expect(navigation).toHaveTextContent('任务')
    expect(navigation).toHaveTextContent('项目')
    expect(navigation).toHaveTextContent('工作流')
    expect(navigation).toHaveTextContent('设置')
    expect(navigation).not.toHaveTextContent('常用做法')
  })
})

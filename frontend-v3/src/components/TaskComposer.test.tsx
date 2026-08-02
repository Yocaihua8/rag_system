import { cleanup, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { useDraftStore } from '../store/draftStore'
import { TaskComposer } from './TaskComposer'

describe('TaskComposer', () => {
  afterEach(cleanup)
  beforeEach(() => {
    localStorage.clear()
    useDraftStore.setState({ drafts: {} })
  })

  it('keeps a draft and disables sending when the task service is unavailable', async () => {
    const user = userEvent.setup()
    render(<TaskComposer draftKey="project:new" serviceAvailable={false} online submitting={false} onOpenOptions={() => undefined} />)

    await user.type(screen.getByLabelText('告诉 Agent 你想完成什么'), '检查项目')

    expect(screen.getByRole('button', { name: '开始处理' })).toBeDisabled()
    expect(screen.getByRole('status')).toHaveTextContent('任务服务尚未连接')
    expect(useDraftStore.getState().drafts['project:new']).toBe('检查项目')
  })

  it('fills a plain-language quick action and submits only once while available', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn().mockResolvedValue(undefined)
    render(<TaskComposer draftKey="project:new" serviceAvailable online submitting={false} onSubmit={onSubmit} onOpenOptions={() => undefined} />)

    await user.click(screen.getByRole('button', { name: /找出问题/ }))
    expect(screen.getByLabelText('告诉 Agent 你想完成什么')).toHaveValue('请检查项目，找出最需要先处理的问题。')
    await user.click(screen.getByRole('button', { name: '开始处理' }))

    expect(onSubmit).toHaveBeenCalledTimes(1)
    expect(onSubmit).toHaveBeenCalledWith('请检查项目，找出最需要先处理的问题。')
  })

  it('does not present unavailable backend abilities as working shortcuts', () => {
    render(<TaskComposer draftKey="project:new" serviceAvailable online submitting={false} onSubmit={vi.fn()} onOpenOptions={() => undefined} />)

    expect(screen.getByRole('button', { name: /整理资料/ })).toBeDisabled()
    expect(screen.getByRole('button', { name: /做一份计划/ })).toBeDisabled()
    expect(screen.getAllByText('后端能力尚未开放')).toHaveLength(2)
  })

  it('keeps editing available but disables writes while offline', () => {
    render(<TaskComposer draftKey="project:new" serviceAvailable online={false} submitting={false} onSubmit={vi.fn()} onOpenOptions={() => undefined} />)

    expect(screen.getByLabelText('告诉 Agent 你想完成什么')).toBeEnabled()
    expect(screen.getByRole('button', { name: '开始处理' })).toBeDisabled()
    expect(screen.getByRole('status')).toHaveTextContent('恢复连接后请手动发送')
  })

  it('keeps the draft and does not claim receipt when submission fails', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn().mockRejectedValue(new Error('后端拒绝了请求'))
    render(<TaskComposer draftKey="project:new" serviceAvailable online submitting={false} onSubmit={onSubmit} onOpenOptions={() => undefined} />)

    await user.type(screen.getByLabelText('告诉 Agent 你想完成什么'), '检查失败流程')
    await user.click(screen.getByRole('button', { name: '开始处理' }))

    expect(await screen.findByRole('status')).toHaveTextContent('草稿已保留')
    expect(screen.getByRole('status')).toHaveTextContent('不会自动重复提交')
    expect(screen.getByRole('status')).not.toHaveTextContent('已收到')
    expect(useDraftStore.getState().drafts['project:new']).toBe('检查失败流程')
  })
})

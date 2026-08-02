import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import { WorkflowsPage } from './WorkflowsPage'

describe('WorkflowsPage', () => {
  afterEach(cleanup)

  it('uses plain Chinese labels for workflow steps and editor actions', () => {
    render(
      <WorkflowsPage
        selectedWorkflow={{
          id: 'workflow-1',
          name: '检查项目并给出建议',
          statusLabel: '已发布',
          steps: ['trigger.manual', 'project.analyze', 'artifact.create', 'agent.respond'],
        }}
      />,
    )

    expect(screen.getByText('手动开始')).toBeInTheDocument()
    expect(screen.getByText('检查项目内容')).toBeInTheDocument()
    expect(screen.getByText('生成结果文件')).toBeInTheDocument()
    expect(screen.getByText('生成中文建议')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '编辑流程图（尚未开放）' })).toBeDisabled()
    expect(screen.queryByText('专业编辑（尚未开放）')).not.toBeInTheDocument()
  })
})

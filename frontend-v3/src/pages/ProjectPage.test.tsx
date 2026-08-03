import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { ProjectPage } from './ProjectPage'


describe('ProjectPage Sources', () => {
  it('keeps an empty project honest and starts a real source scan on demand', () => {
    const onScanSources = vi.fn()
    render(
      <ProjectPage
        project={{ id: 'project-1', name: '资料项目', rootLabel: 'E:/project' }}
        onScanSources={onScanSources}
      />,
    )

    expect(screen.getByText('尚未扫描此项目。扫描只读取已绑定目录中的受支持文本文件，不会修改项目文件。')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: '扫描项目资料' }))
    expect(onScanSources).toHaveBeenCalledOnce()
  })

  it('renders only source metadata and relative document paths', () => {
    render(
      <ProjectPage
        project={{ id: 'project-1', name: '资料项目', rootLabel: 'E:/project' }}
        sources={[{ id: 'source-1', name: '项目根目录', sourceType: 'project_root', status: 'ready', documentCount: 1 }]}
        documents={[{ id: 'doc-1', relativePath: 'src/main.py', mimeType: 'text/x-python', sizeBytes: 19 }]}
        onScanSources={() => undefined}
      />,
    )

    expect(screen.getByText('项目根目录')).toBeInTheDocument()
    expect(screen.getByText('src/main.py')).toBeInTheDocument()
    expect(screen.queryByText('资料接口尚未接入当前前端阶段，因此不会显示占位资料。')).not.toBeInTheDocument()
  })
})

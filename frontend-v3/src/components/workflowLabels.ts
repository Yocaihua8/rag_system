const workflowStepLabels: Record<string, string> = {
  'trigger.manual': '手动开始',
  'agent.plan': '整理处理计划',
  'source.search': '查找参考资料',
  'source.read': '读取参考资料',
  'project.analyze': '检查项目内容',
  'llm.synthesize': '整理分析结果',
  'llm.compare': '比较两种结果',
  'insight.assess': '评估项目情况',
  'learning.plan': '生成学习计划',
  'artifact.create': '生成结果文件',
  'agent.respond': '生成中文建议',
  'approval.request': '等待你的确认',
  'artifact.export': '导出生成结果',
  'obsidian.publish': '发布到 Obsidian',
  'control.branch': '按条件分开处理',
  'control.join': '合并处理结果',
}

export function workflowStepLabel(step: string): string {
  const numbered = /^(\d+\.\s*)(.+)$/.exec(step)
  if (numbered) {
    return `${numbered[1]}${workflowStepLabels[numbered[2]] ?? '其他处理步骤'}`
  }
  return workflowStepLabels[step] ?? '其他处理步骤'
}

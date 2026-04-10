from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "data" / "outputs"


@dataclass
class OutputResult:
    path: str
    content: str


class OutputService:
    def save_markdown(self, file_name: str, content: str) -> OutputResult:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        target = OUTPUT_DIR / file_name
        target.write_text(content, encoding="utf-8")
        return OutputResult(path=str(target), content=content)

    def build_readme_draft(self, workspace_name: str, workspace_root: str, analysis_report: str) -> str:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return (
            f"# {workspace_name} - 项目说明草稿\n\n"
            f"- 生成时间: {now}\n"
            f"- 工作区目录: {workspace_root}\n\n"
            "## 项目概述\n\n"
            "本草稿由本地 RAG + Agent 桌面系统基于当前工作区自动生成，可在此基础上继续补充。\n\n"
            "## 分析结果\n\n"
            f"{analysis_report.strip() if analysis_report.strip() else '暂无分析结果，请先执行项目分析。'}\n\n"
            "## 运行说明（待补充）\n\n"
            "- 环境要求\n"
            "- 启动命令\n"
            "- 常见问题\n"
        )

    def build_requirement_draft(self, workspace_name: str, analysis_report: str) -> str:
        return (
            f"# {workspace_name} - 需求设计分析草稿\n\n"
            "## 目标\n"
            "- 明确项目核心能力与边界\n"
            "- 形成可执行需求清单\n\n"
            "## 需求摘要\n"
            f"{analysis_report.strip() if analysis_report.strip() else '暂无分析输入，请先执行项目分析。'}\n\n"
            "## 约束\n"
            "- 本地优先\n"
            "- 数据可控\n"
            "- 高风险操作需确认\n"
        )

    def build_system_design_draft(self, workspace_name: str, analysis_report: str) -> str:
        return (
            f"# {workspace_name} - 系统设计草稿\n\n"
            "## 分层结构\n"
            "- UI 层\n"
            "- 编排层\n"
            "- 业务层\n"
            "- 基础设施层\n\n"
            "## 当前分析输入\n"
            f"{analysis_report.strip() if analysis_report.strip() else '暂无分析输入，请先执行项目分析。'}\n"
        )

    def build_prompt_draft(self, workspace_name: str, analysis_report: str) -> str:
        return (
            f"# {workspace_name} - Codex Prompt 草稿\n\n"
            "你是我的项目协作助手，请基于以下上下文完成任务：\n\n"
            "## 项目上下文\n"
            f"{analysis_report.strip() if analysis_report.strip() else '暂无分析输入，请先执行项目分析。'}\n\n"
            "## 输出要求\n"
            "- 先给结论再给原因\n"
            "- 给出可执行步骤\n"
            "- 标注风险与验证方式\n"
        )

    def build_by_type(
        self,
        doc_type: Literal["README", "需求设计分析", "系统设计", "Codex Prompt"],
        workspace_name: str,
        workspace_root: str,
        analysis_report: str,
    ) -> str:
        if doc_type == "需求设计分析":
            return self.build_requirement_draft(workspace_name, analysis_report)
        if doc_type == "系统设计":
            return self.build_system_design_draft(workspace_name, analysis_report)
        if doc_type == "Codex Prompt":
            return self.build_prompt_draft(workspace_name, analysis_report)
        return self.build_readme_draft(workspace_name, workspace_root, analysis_report)

"""
生成类用例：简历生成 / JD 匹配 / 面试脚本。

共同模式：有针对性检索（指定 domain）→ 领域分析 → 结构化 Prompt → LLM 生成
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from legacy.desktop.ports.llm_client import ILLMClient, LLMRequest
from legacy.desktop.ports.retriever import IRetriever, RetrievalQuery


@dataclass(frozen=True)
class GenerationResult:
    markdown: str
    model_used: str
    sources_used: int


# ── 简历生成 ──────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ResumeRequest:
    workspace_id: str
    job_keywords: List[str]
    project_name: str
    domains: List[str] = field(default_factory=lambda: ["resume"])
    top_k: int = 10


class GenerateResumeUseCase:

    _SYSTEM = """你是一位专业的职业顾问，擅长撰写高质量的简历项目描述。
请用 STAR 法则（情境-任务-行动-结果）提炼项目亮点，使用强动作动词开头，量化成果。"""

    def __init__(self, retriever: IRetriever, llm_client: ILLMClient, model: str = "qwen2.5:7b") -> None:
        self._retriever = retriever
        self._llm = llm_client
        self._model = model

    def execute(self, request: ResumeRequest) -> GenerationResult:
        result = self._retriever.search(RetrievalQuery(
            question=" ".join(request.job_keywords),
            workspace_id=request.workspace_id,
            domains=request.domains,
            top_k=request.top_k,
        ))

        # P3: 空检索保护，避免用空 context 发给 LLM 导致幻觉
        if not result.chunks:
            return GenerationResult(
                markdown="⚠️ 知识库中未检索到相关内容，请先建立索引或向工作区添加更多文档。",
                model_used="—",
                sources_used=0,
            )

        context = "\n\n".join(c.content for c in result.chunks)
        keywords_str = "、".join(request.job_keywords)

        prompt = f"""项目名称：{request.project_name}
目标岗位关键词：{keywords_str}

以下是从知识库中检索到的相关经历片段：
{context}

请基于以上内容，生成 5-6 条简历项目子弹点。要求：
1. 每条以强动作动词开头（主导、搭建、优化、推动、设计等）
2. 包含具体数字或百分比（如无数据，给出合理占位符 [X%]）
3. 结合目标关键词，突出与岗位的匹配度
4. 每条不超过 60 字

输出格式（直接输出 Markdown 列表，无需其他说明）："""

        response = self._llm.generate(LLMRequest(
            prompt=prompt,
            model=self._model,
            system_prompt=self._SYSTEM,
            temperature=0.7,
        ))
        return GenerationResult(
            markdown=response.content,
            model_used=self._model,
            sources_used=len(result.chunks),
        )


# ── JD 匹配 ───────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class JDMatchRequest:
    workspace_id: str
    job_name: str
    job_keywords: List[str]
    coverage_threshold: int = 70
    domains: List[str] = field(default_factory=lambda: ["resume", "jd"])
    top_k: int = 12


class MatchJDUseCase:

    _SYSTEM = """你是一位专业的求职顾问，擅长分析 JD 与候选人经历的匹配程度。
请基于候选人知识库内容，给出详细的匹配分析和改进建议。"""

    def __init__(self, retriever: IRetriever, llm_client: ILLMClient, model: str = "qwen2.5:7b") -> None:
        self._retriever = retriever
        self._llm = llm_client
        self._model = model

    def execute(self, request: JDMatchRequest) -> GenerationResult:
        result = self._retriever.search(RetrievalQuery(
            question=" ".join(request.job_keywords),
            workspace_id=request.workspace_id,
            domains=request.domains,
            top_k=request.top_k,
        ))

        # P3: 空检索保护
        if not result.chunks:
            return GenerationResult(
                markdown="⚠️ 知识库中未检索到相关内容，请先建立索引或向工作区添加更多文档。",
                model_used="—",
                sources_used=0,
            )

        context = "\n\n".join(c.content for c in result.chunks)
        keywords_str = "\n".join(f"- {kw}" for kw in request.job_keywords)

        # 简单覆盖率计算（纯文本分析，LLM 会做更深入的判断）
        all_text = context.lower()
        matched = [kw for kw in request.job_keywords if kw.lower() in all_text]
        coverage_pct = int(len(matched) / max(len(request.job_keywords), 1) * 100)

        prompt = f"""目标岗位：{request.job_name}
初步关键词覆盖率：{coverage_pct}%（已匹配 {len(matched)}/{len(request.job_keywords)} 个关键词）

JD 关键词列表：
{keywords_str}

候选人知识库相关内容：
{context}

请生成一份完整的 JD 匹配报告，包含：
1. **匹配总结**（2-3 句话，覆盖率评级：优秀≥80% / 良好≥60% / 需加强<60%）
2. **优势匹配**（列出强匹配项及支撑证据）
3. **差距分析**（列出缺失或薄弱的关键词，说明影响）
4. **改进建议**（3-5 条具体可执行的建议）
5. **推荐补充项目弹点**（基于知识库内容，2-3 条可直接填入简历的描述）

输出为结构化 Markdown 格式："""

        response = self._llm.generate(LLMRequest(
            prompt=prompt,
            model=self._model,
            system_prompt=self._SYSTEM,
            temperature=0.5,
            max_tokens=2048,
        ))
        return GenerationResult(
            markdown=response.content,
            model_used=self._model,
            sources_used=len(result.chunks),
        )


# ── 面试脚本生成 ──────────────────────────────────────────────────────────

@dataclass(frozen=True)
class InterviewRequest:
    workspace_id: str
    job_keywords: List[str]
    project_name: str
    domains: List[str] = field(default_factory=lambda: ["resume", "notes"])
    top_k: int = 10


class GenerateInterviewScriptUseCase:

    _SYSTEM = """你是一位经验丰富的面试教练，擅长帮助候选人准备技术和行为面试。
请基于候选人的真实经历，生成具体、有说服力的面试回答脚本。"""

    def __init__(self, retriever: IRetriever, llm_client: ILLMClient, model: str = "qwen2.5:7b") -> None:
        self._retriever = retriever
        self._llm = llm_client
        self._model = model

    def execute(self, request: InterviewRequest) -> GenerationResult:
        result = self._retriever.search(RetrievalQuery(
            question=" ".join(request.job_keywords),
            workspace_id=request.workspace_id,
            domains=request.domains,
            top_k=request.top_k,
        ))

        # P3: 空检索保护
        if not result.chunks:
            return GenerationResult(
                markdown="⚠️ 知识库中未检索到相关内容，请先建立索引或向工作区添加更多文档。",
                model_used="—",
                sources_used=0,
            )

        context = "\n\n".join(c.content for c in result.chunks)
        keywords_str = "、".join(request.job_keywords)

        prompt = f"""项目名称：{request.project_name}
岗位关键词：{keywords_str}

候选人相关经历：
{context}

请为候选人生成面试准备脚本，包含：
1. **自我介绍（1分钟版）**（结合项目经历，突出与岗位相关的亮点）
2. **项目介绍话术**（用 STAR 法则描述 {request.project_name}，控制在 2 分钟内）
3. **高频面试题回答**（针对以下 3 类问题各给一个回答示例）
   - "你遇到的最大技术挑战是什么？"
   - "你如何与团队协作解决分歧？"
   - "你如何衡量项目成功？"
4. **可能被追问的技术问题**（列出 3-5 个根据经历可能被深挖的问题，附简要回答思路）

输出为结构化 Markdown 格式："""

        response = self._llm.generate(LLMRequest(
            prompt=prompt,
            model=self._model,
            system_prompt=self._SYSTEM,
            temperature=0.6,
            max_tokens=2500,
        ))
        return GenerationResult(
            markdown=response.content,
            model_used=self._model,
            sources_used=len(result.chunks),
        )

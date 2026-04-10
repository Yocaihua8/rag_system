from datetime import date
import re
from typing import Dict, List, Tuple

from backend.app.config import RAW_PATH
from backend.app.modules.preprocess.metric_extractor import extract_metrics
from backend.app.schemas.chunk import Chunk


UPDATES_PATH = RAW_PATH / "resume" / "project_updates.md"

SYNONYMS = {
    "auth": ["authentication", "authorization", "rbac"],
    "permissions": ["auth", "rbac", "authorization"],
    "export": ["导出", "导出打印", "print"],
    "导出": ["export", "print"],
    "draft": ["草稿", "drafting"],
    "草稿": ["draft"],
    "rag": ["retrieval", "检索增强生成"],
    "retrieval": ["search", "召回", "matching"],
    "embedding": ["vector", "向量", "向量化"],
    "chunking": ["split", "切片", "分块"],
    "fastapi": ["FastAPI"],
    "python": ["Python"],
    "sqlite": ["SQLite"],
    "vue": ["Vue", "Vue3"],
}

SECTION_HINTS = {
    "auth": "project_bullets.md -> API 安全与鉴权",
    "permissions": "project_bullets.md -> API 安全与鉴权",
    "rag": "project_bullets.md -> RAG 核心链路",
    "retrieval": "project_bullets.md -> 检索与召回",
    "embedding": "project_bullets.md -> 向量化与索引",
    "chunking": "project_bullets.md -> 文档切片与清洗",
    "fastapi": "project_bullets.md -> FastAPI 服务与联调",
    "python": "project_bullets.md -> Python 服务实现",
    "sqlite": "project_bullets.md -> 本地存储与历史记录",
    "export": "project_bullets.md -> 导出与结果沉淀",
    "draft": "project_bullets.md -> 草稿编辑链路",
}

METRIC_HINTS = {
    "auth": ["越权请求拦截率", "鉴权规则覆盖率", "误授权请求数"],
    "permissions": ["越权请求拦截率", "鉴权规则覆盖率", "误授权请求数"],
    "rag": ["问题命中率", "回答相关性评分", "无答案率"],
    "retrieval": ["Top-K 命中率", "召回耗时", "重试查询比例"],
    "embedding": ["向量构建耗时", "向量索引更新时长", "向量库一致性差异率"],
    "chunking": ["切片平均长度", "切片生成耗时", "重复切片比例"],
    "export": ["导出成功率", "导出耗时", "导出失败重试率"],
    "导出": ["导出成功率", "导出耗时", "导出失败重试率"],
    "draft": ["草稿保存成功率", "误提交率", "草稿转正式平均耗时"],
    "草稿": ["草稿保存成功率", "误提交率", "草稿转正式平均耗时"],
    "fastapi": ["API 平均响应耗时", "接口可用性", "超时比例"],
    "python": ["任务执行耗时", "异常率"],
    "sqlite": ["查询耗时", "锁冲突比例"],
    "vue": ["页面首屏时间", "交互错误率"],
}

METRIC_TEMPLATES = {
    "率": "(单位: %) 参考区间: 90%~99%",
    "时间": "(单位: ms/秒/分钟) 参考区间: 100ms~3s",
    "比例": "(单位: %) 参考区间: 1%~10%",
    "次数": "(单位: 次/周 或 次/月) 参考区间: 0~5",
    "耗时": "(单位: ms/秒/分钟) 参考区间: 100ms~5s",
    "可用性": "(单位: %) 参考区间: 99%~99.9%",
    "错误率": "(单位: %) 参考区间: 0.1%~1%",
}

AI_KEYWORDS = {"rag", "retrieval", "embedding", "chunking", "fastapi", "python"}


def _extract_points(chunks: List[Chunk]) -> List[str]:
    points = []
    for chunk in chunks:
        for line in chunk.content.splitlines():
            text = line.strip()
            if text.startswith("- ") or text.startswith("* "):
                points.append(text[2:].strip())
    if not points:
        for chunk in chunks:
            snippet = chunk.content.strip().replace("\n", " ")
            if snippet:
                points.append(snippet[:120])
    return points


def _normalize_keywords(job_keywords: List[str]) -> List[str]:
    normalized = []
    for keyword in job_keywords:
        cleaned = keyword.strip()
        if cleaned:
            normalized.append(cleaned)
    return normalized


def _expand_keyword(keyword: str) -> List[str]:
    variants = [keyword]
    for alt in SYNONYMS.get(keyword, []):
        variants.append(alt)
    for key, values in SYNONYMS.items():
        if keyword in values:
            variants.append(key)
            variants.extend(values)
    seen = set()
    result = []
    for v in variants:
        lower = v.lower()
        if lower in seen:
            continue
        seen.add(lower)
        result.append(v)
    return result


def _find_missing_keywords(job_keywords: List[str], points: List[str]) -> Tuple[List[str], int, int]:
    normalized = _normalize_keywords(job_keywords)
    if not normalized:
        return [], 0, 0

    text = " ".join(points).lower()
    missing = []
    matched = 0

    for keyword in normalized:
        variants = _expand_keyword(keyword)
        if any(variant.lower() in text for variant in variants):
            matched += 1
        else:
            missing.append(keyword)

    return missing, matched, len(normalized)


def _recommend_sections(missing: List[str]) -> List[str]:
    if not missing:
        return []

    recommendations = []
    for keyword in missing:
        hint = SECTION_HINTS.get(keyword.lower()) or SECTION_HINTS.get(keyword)
        if hint:
            recommendations.append("- {0}: add bullet under {1}".format(keyword, hint))
        else:
            recommendations.append("- {0}: add bullet under project_bullets.md -> RAG 核心链路".format(keyword))
    return recommendations


def _coverage_grade(coverage: int) -> str:
    if coverage >= 85:
        return "HIGH"
    if coverage >= 60:
        return "MEDIUM"
    return "LOW"


def _attach_metric_template(metric_name: str) -> str:
    for key, template in METRIC_TEMPLATES.items():
        if key in metric_name:
            return "{0} {1}".format(metric_name, template)
    return metric_name


def _metric_suggestions(missing: List[str]) -> List[str]:
    if not missing:
        return []
    lines = []
    for keyword in missing:
        hints = METRIC_HINTS.get(keyword.lower()) or METRIC_HINTS.get(keyword)
        if hints:
            with_template = [_attach_metric_template(h) for h in hints]
            lines.append("- {0}: {1}".format(keyword, " / ".join(with_template)))
    return lines


def _parse_updates() -> List[Dict[str, str]]:
    if not UPDATES_PATH.exists():
        return []
    text = UPDATES_PATH.read_text(encoding="utf-8")
    entries = []
    current: Dict[str, str] = {}

    for line in text.splitlines():
        line = line.strip()
        if line.startswith("## "):
            if current:
                entries.append(current)
            current = {"date": line[3:].strip()}
            continue
        if line.startswith("- "):
            content = line[2:].strip()
            if "：" in content:
                key, value = content.split("：", 1)
                current[key.strip()] = value.strip()
    if current:
        entries.append(current)
    return entries


def _match_keyword_to_entry(keyword: str, entry: Dict[str, str]) -> bool:
    variants = [v.lower() for v in _expand_keyword(keyword)]
    module = entry.get("模块", "").lower()
    tags = entry.get("关联标签", "").lower()
    return any(v in module or v in tags for v in variants)


def _metrics_for_keyword(keyword: str) -> List[str]:
    entries = _parse_updates()
    metrics: List[str] = []
    for entry in entries:
        if not _match_keyword_to_entry(keyword, entry):
            continue
        text = " ".join([entry.get("验证结果", ""), entry.get("具体改动", "")])
        for record in extract_metrics(text, doc_id=entry.get("date", "")):
            if record.subject:
                metrics.append("{0}{1} {2}{3}".format(record.subject, record.metric_name, record.value, record.unit))
            else:
                metrics.append("{0} {1}{2}".format(record.metric_name, record.value, record.unit))
    seen = set()
    result = []
    for m in metrics:
        if m in seen:
            continue
        seen.add(m)
        result.append(m)
    return result


def _draft_bullet_blocks(missing: List[str]) -> List[str]:
    if not missing:
        return []

    today = date.today().isoformat()
    blocks = []
    for keyword in missing:
        hint = SECTION_HINTS.get(keyword.lower()) or SECTION_HINTS.get(keyword)
        location = hint or "project_bullets.md -> RAG 核心链路"
        role = "Python后端 / AI应用开发" if keyword.lower() in AI_KEYWORDS else "Python后端"
        metric_hint = METRIC_HINTS.get(keyword.lower()) or METRIC_HINTS.get(keyword) or []
        metric_with_template = [_attach_metric_template(h) for h in metric_hint]
        metric_text = "；指标建议：{0}".format(" / ".join(metric_with_template)) if metric_with_template else ""

        scene = "场景：与{0}相关的 RAG 流程或联调问题暴露".format(keyword)
        action = "动作：梳理接口/字段并完成必要的服务改造与联调"
        real_metrics = _metrics_for_keyword(keyword)
        if real_metrics:
            result = "结果：效率或稳定性提升，指标：{0}".format(" / ".join(real_metrics))
        else:
            result = "结果：效率或稳定性提升，{0}".format("请补充可量化指标")

        content = "{0}；{1}；{2}{3}".format(scene, action, result, metric_text)

        block = [
            "- [建议补充位置] {0}".format(location),
            "  [适合岗位] {0}".format(role),
            "  [技术标签] {0}".format(keyword),
            "  [成熟度] 草稿",
            "  [最近更新时间] {0}".format(today),
            "  [内容] {0}".format(content),
        ]
        blocks.append("\n".join(block))
    return blocks


def build_draft_bullets(job_keywords: List[str], retrieved_chunks: List[Chunk]) -> List[str]:
    points = _extract_points(retrieved_chunks)
    missing, _, _ = _find_missing_keywords(job_keywords, points)
    return _draft_bullet_blocks(missing)


def generate_jd_match_summary(
    job_name: str,
    job_keywords: List[str],
    retrieved_chunks: List[Chunk],
    project_name: str = "Python RAG Desktop Assistant",
    coverage_threshold: int = 70,
) -> str:
    points = _extract_points(retrieved_chunks)
    keyword_hint = ", ".join(job_keywords) if job_keywords else "rag"

    highlights = ["- {0}".format(p) for p in points[:6]] if points else ["- TODO: add more bullets."]
    missing, matched, total = _find_missing_keywords(job_keywords, points)

    if total > 0:
        coverage = int((matched / float(total)) * 100)
        coverage_line = "- Coverage: {0}% ({1}/{2})".format(coverage, matched, total)
        grade_line = "- Grade: {0}".format(_coverage_grade(coverage))
    else:
        coverage = 0
        coverage_line = "- Coverage: N/A (no keywords provided)"
        grade_line = "- Grade: N/A"

    if total > 0 and coverage < coverage_threshold:
        warning_line = "- WARNING: coverage below {0}% threshold, prioritize filling missing keywords.".format(
            coverage_threshold
        )
    else:
        warning_line = "- Coverage is acceptable for current threshold."

    if missing:
        gap_lines = ["- Missing keywords: {0}".format(", ".join(missing))]
        gap_lines.append("- TODO: add bullets or updates to cover these keywords.")
        gap_lines.extend(_recommend_sections(missing))
    else:
        gap_lines = ["- No missing keywords detected against current bullets."]

    draft_blocks = _draft_bullet_blocks(missing)
    draft_section = "\n".join(draft_blocks) if draft_blocks else "- No draft bullets needed."

    metric_lines = _metric_suggestions(missing)
    metric_section = "\n".join(metric_lines) if metric_lines else "- No metric suggestions available."

    return """## JD Match Summary: {0}

### Target Role
- Job: {0}
- Keywords: {1}

### Coverage
{2}
{3}
{4}

### Project Mapping ({5})
{6}

### Gaps / Next Actions
{7}

### Draft Bullet Suggestions
{8}

### Metric Suggestions
{9}
""".format(
        job_name,
        keyword_hint,
        coverage_line,
        grade_line,
        warning_line,
        project_name,
        "\n".join(highlights),
        "\n".join(gap_lines),
        draft_section,
        metric_section,
    )

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import re
import uuid
from typing import Iterable, List

from legacy.desktop.domain.errors import NotFoundError, ValidationError
from legacy.desktop.domain.models.project_knowledge import (
    Evidence,
    KnowledgePoint,
    ProjectKnowledgePoint,
    MasteryRecord,
    MasteryStatus,
    SkillArea,
)
from legacy.desktop.ports.project_knowledge_store import IProjectKnowledgeStore
from legacy.desktop.ports.knowledge_mastery_store import IKnowledgeMasteryStore
from legacy.desktop.ports.workspace_store import IWorkspaceStore


@dataclass(frozen=True)
class MasteryOverview:
    workspace_id: str
    total_points: int
    total_records: int
    claimed: int
    evidence_found: int
    verified: int


@dataclass(frozen=True)
class AssessmentQuestion:
    """掌握评估问题（最小会话问题模型）。"""

    id: str
    workspace_id: str
    knowledge_point_id: str
    prompt: str
    source_path: str
    expected_points: tuple[str, ...]
    reference: str


@dataclass(frozen=True)
class AssessmentQuestionResult:
    """单题评估结果（规则化得分）。"""

    question_id: str
    workspace_id: str
    status: str
    score: float
    matched_points: tuple[str, ...]
    missing_points: tuple[str, ...]
    feedback: str
    answer: str = ""


@dataclass(frozen=True)
class AbilityGapReport:
    """评估结束后的能力差距汇总。"""

    workspace_id: str
    total_questions: int
    mastered_count: int
    basic_count: int
    needs_improvement_count: int
    mastered_knowledge_points: tuple[str, ...]
    weak_knowledge_points: tuple[str, ...]
    suggested_reading_files: tuple[str, ...]
    suggested_follow_up_questions: tuple[str, ...]
    next_learning_order: tuple[str, ...]
    overview: str
    follow_up_question_ids: tuple[str, ...] = ()


class MasteryAssessmentStatus(str, Enum):
    MASTERY = "已掌握"
    BASIC = "基本理解"
    IMPROVE = "需要补充"


@dataclass(frozen=True)
class AssessmentSession:
    """评估会话（一次评估下发的题集合）。"""

    id: str
    workspace_id: str
    questions: tuple[AssessmentQuestion, ...]
    focus_knowledge_point_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class MissedAssessmentRecord:
    """错题记录（内存态），用于优先复测。"""

    question_id: str
    knowledge_point_id: str
    workspace_id: str
    status: str
    answer: str
    updated_at: str


class KnowledgeMasteryUseCase:
    """掌握评估主干数据的最小用例编排。"""

    def __init__(
        self,
        workspace_store: IWorkspaceStore,
        mastery_store: IKnowledgeMasteryStore,
        project_knowledge_store: IProjectKnowledgeStore,
    ) -> None:
        self._workspace_store = workspace_store
        self._mastery_store = mastery_store
        self._project_knowledge_store = project_knowledge_store
        self._missed_records: dict[str, list[MissedAssessmentRecord]] = {}

    def create_skill_area(
        self,
        workspace_id: str,
        name: str,
        description: str = "",
    ) -> SkillArea:
        self._require_workspace(workspace_id)
        normalized = (name or "").strip()
        if not normalized:
            raise ValidationError("技能域名称不能为空")
        existing = self._mastery_store.list_skill_areas_by_workspace(workspace_id)
        for area in existing:
            if area.name.lower() == normalized.lower():
                return area
        area = SkillArea.create(
            workspace_id=workspace_id,
            name=normalized,
            description=description,
        )
        self._mastery_store.save_skill_area(area)
        return area

    def create_knowledge_point(
        self,
        workspace_id: str,
        skill_area_id: str,
        name: str,
        summary: str,
        confidence: float = 0.6,
    ) -> KnowledgePoint:
        self._require_workspace(workspace_id)
        area = self._get_skill_area(workspace_id, skill_area_id)
        if area is None:
            raise NotFoundError("SkillArea", skill_area_id)
        normalized = (name or "").strip()
        if not normalized:
            raise ValidationError("知识点名称不能为空")
        point = KnowledgePoint.create(
            workspace_id=workspace_id,
            skill_area_id=area.id,
            name=normalized,
            summary=(summary or "").strip(),
            confidence=confidence,
        )
        self._mastery_store.save_knowledge_point(point)
        return point

    def create_evidence(
        self,
        workspace_id: str,
        knowledge_point_id: str,
        source_path: str,
        snippet: str,
        confidence: float = 0.6,
    ) -> Evidence:
        self._require_workspace(workspace_id)
        point = self._get_knowledge_point(workspace_id, knowledge_point_id)
        if point is None or point.workspace_id != workspace_id:
            raise NotFoundError("KnowledgePoint", knowledge_point_id)
        if not source_path.strip():
            raise ValidationError("来源路径不能为空")
        evidence = Evidence.create(
            workspace_id=workspace_id,
            knowledge_point_id=knowledge_point_id,
            source_path=source_path.strip(),
            snippet=snippet.strip(),
            confidence=confidence,
        )
        self._mastery_store.save_evidence(evidence)
        return evidence

    def claim_mastery(
        self,
        workspace_id: str,
        knowledge_point_id: str,
        note: str = "",
        confidence: float = 0.6,
    ) -> MasteryRecord:
        self._require_workspace(workspace_id)
        point = self._get_knowledge_point(workspace_id, knowledge_point_id)
        if point is None or point.workspace_id != workspace_id:
            raise NotFoundError("KnowledgePoint", knowledge_point_id)

        existing_records = self._mastery_store.list_mastery_records_by_knowledge_point(knowledge_point_id)
        if existing_records:
            # 同一知识点保持最新记录，避免重复插入
            return existing_records[0]

        record = MasteryRecord.create(
            workspace_id=workspace_id,
            knowledge_point_id=knowledge_point_id,
            status=MasteryStatus.CLAIMED,
            confidence=confidence,
            note=note or "已声明掌握",
        )
        self._mastery_store.save_mastery_record(record)
        return record

    def mark_evidence_found(
        self,
        workspace_id: str,
        record_id: str,
        evidence_id: str,
        note: str = "",
    ) -> MasteryRecord:
        record = self._get_record(record_id, workspace_id)
        point = self._get_knowledge_point(workspace_id, record.knowledge_point_id)
        if point is None:
            raise NotFoundError("KnowledgePoint", record.knowledge_point_id)
        evidence = self._mastery_store.get_evidence(evidence_id)
        if (
            evidence is None
            or evidence.knowledge_point_id != record.knowledge_point_id
            or evidence.workspace_id != workspace_id
        ):
            raise NotFoundError("Evidence", evidence_id)
        updated = record.mark_evidence_found(evidence_id=evidence.id, note=note or "已关联证据")
        self._mastery_store.save_mastery_record(updated)
        return updated

    def mark_verified(
        self,
        workspace_id: str,
        record_id: str,
        note: str = "",
        confidence: float | None = None,
    ) -> MasteryRecord:
        record = self._get_record(record_id, workspace_id)
        if record.status == MasteryStatus.CLAIMED and not record.evidence_id:
            raise ValidationError("未绑定证据前不能确认验证通过")
        updated = record.mark_verified(note=note or "已验证通过", confidence=confidence)
        self._mastery_store.save_mastery_record(updated)
        return updated

    def get_overview(self, workspace_id: str) -> MasteryOverview:
        self._require_workspace(workspace_id)
        records = self._mastery_store.list_mastery_records_by_workspace(workspace_id)
        counts = Counter(r.status for r in records)
        return MasteryOverview(
            workspace_id=workspace_id,
            total_points=len(self._mastery_store.list_knowledge_points_by_workspace(workspace_id)),
            total_records=len(records),
            claimed=counts.get(MasteryStatus.CLAIMED, 0),
            evidence_found=counts.get(MasteryStatus.EVIDENCE_FOUND, 0),
            verified=counts.get(MasteryStatus.VERIFIED, 0),
        )

    def create_assessment_session(
        self,
        workspace_id: str,
        question_count: int = 5,
        prioritize_missed: bool = False,
        focus_knowledge_point_ids: tuple[str, ...] | None = None,
    ) -> AssessmentSession:
        """基于项目知识点生成一批评估题（无状态、可重复）。"""
        self._require_workspace(workspace_id)
        if question_count <= 0:
            raise ValidationError("题目数量必须大于 0")

        points = self._project_knowledge_store.list_by_workspace(workspace_id)
        if not points:
            raise ValidationError("当前项目暂无知识点，无法自动出题")

        selected_points = _select_assessment_points(
            points=points,
            question_count=question_count,
            focus_knowledge_point_ids=focus_knowledge_point_ids,
            prioritize_missed=prioritize_missed,
            missed_records=self._missed_records.get(workspace_id, []),
        )
        questions = [
            self._build_assessment_question(workspace_id=workspace_id, point=point)
            for point in selected_points
        ]
        return AssessmentSession(
            id=str(uuid.uuid4()),
            workspace_id=workspace_id,
            questions=tuple(questions),
            focus_knowledge_point_ids=tuple(
                point.id for point in _ordered_focus_points(
                    points=selected_points,
                    focus_knowledge_point_ids=focus_knowledge_point_ids,
                )
            ),
        )

    def evaluate_answer(
        self,
        workspace_id: str,
        question: AssessmentQuestion,
        answer: str,
    ) -> AssessmentQuestionResult:
        self._require_workspace(workspace_id)
        if question.workspace_id != workspace_id:
            raise ValidationError("题目不属于该项目空间")

        normalized_answer = (answer or "").strip().lower()
        if not normalized_answer:
            raise ValidationError("回答不能为空")

        matched = tuple(point for point in question.expected_points if point.lower() in normalized_answer)
        missing = tuple(point for point in question.expected_points if point.lower() not in normalized_answer)
        total = len(question.expected_points)
        score = round(len(matched) / max(1, total), 2)

        if score >= 0.75:
            status = MasteryAssessmentStatus.MASTERY.value
            feedback = (
                "回答基本命中了题目的核心点，建议可结合源码做一次复核，"
                "形成可追踪的理解输出。"
            )
        elif score >= 0.35:
            status = MasteryAssessmentStatus.BASIC.value
            feedback = (
                "回答有一定覆盖，但未覆盖全部关键点，建议补充引用来源中的上下文后再复述。"
            )
        else:
            status = MasteryAssessmentStatus.IMPROVE.value
            feedback = (
                "回答还不够充分，建议阅读对应来源文件后再作回答，"
                "先确认概念与流程关系。"
            )

        return AssessmentQuestionResult(
            question_id=question.id,
            workspace_id=workspace_id,
            status=status,
            score=score,
            matched_points=matched,
            missing_points=missing,
            feedback=feedback,
            answer=(answer or "").strip(),
        )

    def record_assessment_attempt(
        self,
        workspace_id: str,
        session: AssessmentSession,
        question_id: str,
        answer: str,
        result: AssessmentQuestionResult,
    ) -> None:
        """记录评估历史，用于错题优先复测。"""
        self._require_workspace(workspace_id)
        question_by_id = {question.id: question for question in session.questions}
        question = question_by_id.get(question_id)
        if question is None or session.workspace_id != workspace_id:
            raise ValidationError("该题目不属于本次评估会话")

        records = self._missed_records.setdefault(workspace_id, [])
        records = [item for item in records if item.knowledge_point_id != question.knowledge_point_id]

        if result.status != MasteryAssessmentStatus.MASTERY.value:
            records.append(
                MissedAssessmentRecord(
                    question_id=question.id,
                    knowledge_point_id=question.knowledge_point_id,
                    workspace_id=workspace_id,
                    status=result.status,
                    answer=(answer or "").strip(),
                    updated_at=_now_ts(),
                )
            )

            deduped: dict[str, MissedAssessmentRecord] = {}
            for item in records:
                deduped[item.knowledge_point_id] = item
            records = list(deduped.values())

        records.sort(key=lambda item: item.updated_at, reverse=True)
        self._missed_records[workspace_id] = records

    def generate_ability_gap_report(
        self,
        session: AssessmentSession,
        results: Iterable[AssessmentQuestionResult],
    ) -> AbilityGapReport:
        self._require_workspace(session.workspace_id)
        normalized_results = tuple(results)
        if not normalized_results:
            raise ValidationError("尚无评估结果，无法生成能力差距报告")

        question_by_id: dict[str, AssessmentQuestion] = {
            q.id: q for q in session.questions
        }
        weak_items: list[tuple[int, float, str, str]] = []
        mastered_points: list[str] = []
        weak_points: list[str] = []
        reading_files: list[str] = []
        follow_ups: list[str] = []
        follow_up_ids: list[str] = []

        for result in normalized_results:
            if result.workspace_id != session.workspace_id:
                raise ValidationError("评估结果项目空间不一致，无法生成能力差距报告")
            question = question_by_id.get(result.question_id)
            if question is None:
                raise ValidationError("评估结果与当前会话题目不匹配")

            point_name = self._knowledge_point_name(
                workspace_id=session.workspace_id,
                point_id=question.knowledge_point_id,
                fallback=question.prompt,
            )

            status_rank = {
                MasteryAssessmentStatus.MASTERY.value: 0,
                MasteryAssessmentStatus.BASIC.value: 1,
                MasteryAssessmentStatus.IMPROVE.value: 2,
            }.get(result.status, 3)

            if result.status == MasteryAssessmentStatus.MASTERY.value:
                mastered_points.append(point_name)
                continue

            weak_points.append(point_name)
            if question.source_path and question.source_path not in reading_files:
                reading_files.append(question.source_path)
            weak_items.append((status_rank, result.score, point_name, question.source_path))

            if result.missing_points:
                missing = "、".join(result.missing_points)
                follow_ups.append(f"请补充『{point_name}』在【{missing}】上的说明并补证据")
            else:
                follow_ups.append(f"请再一次完整回答：{question.prompt}")
            follow_up_ids.append(result.question_id)

        mastered = len(
            [r for r in normalized_results if r.status == MasteryAssessmentStatus.MASTERY.value]
        )
        basic = len(
            [r for r in normalized_results if r.status == MasteryAssessmentStatus.BASIC.value]
        )
        improve = len(
            [r for r in normalized_results if r.status == MasteryAssessmentStatus.IMPROVE.value]
        )

        weak_items.sort(key=lambda item: (item[0], item[1], item[2]))
        next_order = tuple(item[2] for item in weak_items[:3])
        overview = (
            f"共 {len(normalized_results)} 题，{mastered} 项已掌握，"
            f"{basic} 项基本理解，{improve} 项建议补充。"
        )

        return AbilityGapReport(
            workspace_id=session.workspace_id,
            total_questions=len(normalized_results),
            mastered_count=mastered,
            basic_count=basic,
            needs_improvement_count=improve,
            mastered_knowledge_points=tuple(mastered_points),
            weak_knowledge_points=tuple(weak_points),
            suggested_reading_files=tuple(reading_files),
            suggested_follow_up_questions=tuple(follow_ups),
            follow_up_question_ids=tuple(follow_up_ids),
            next_learning_order=next_order,
            overview=overview,
        )

    def _build_assessment_question(
        self,
        workspace_id: str,
        point: ProjectKnowledgePoint,
    ) -> AssessmentQuestion:
        prompt = _question_prompt_from_point(point)
        expected_points = _extract_key_points(point.name, point.summary)
        return AssessmentQuestion(
            id=str(uuid.uuid4()),
            workspace_id=workspace_id,
            knowledge_point_id=point.id,
            prompt=prompt,
            source_path=point.source_path,
            expected_points=tuple(expected_points),
            reference=point.summary,
        )

    def _require_workspace(self, workspace_id: str) -> None:
        workspace = self._workspace_store.get(workspace_id)
        if workspace is None:
            raise NotFoundError("Workspace", workspace_id)

    def _get_skill_area(self, workspace_id: str, skill_area_id: str) -> SkillArea | None:
        areas = self._mastery_store.list_skill_areas_by_workspace(workspace_id)
        for area in areas:
            if area.id == skill_area_id:
                return area
        return None

    def _get_knowledge_point(
        self,
        workspace_id: str,
        point_id: str,
    ) -> KnowledgePoint | None:
        points = self._mastery_store.list_knowledge_points_by_workspace(workspace_id)
        for point in points:
            if point.id == point_id:
                return point
        return None

    def _get_record(self, record_id: str, workspace_id: str) -> MasteryRecord:
        record = self._mastery_store.get_mastery_record(record_id)
        if record is None or record.workspace_id != workspace_id:
            raise NotFoundError("MasteryRecord", record_id)
        return record

    def _knowledge_point_name(
        self,
        workspace_id: str,
        point_id: str,
        fallback: str,
    ) -> str:
        for point in self._project_knowledge_store.list_by_workspace(workspace_id):
            if point.id == point_id:
                return point.name
        return fallback


def _question_prompt_from_point(point: ProjectKnowledgePoint) -> str:
    kind_prompt = {
        "tech_stack": "围绕该技术点“{name}”说明它在当前项目中的作用，以及和其他模块如何协作。",
        "config": "该配置文件“{name}”通常承载什么职责？请结合项目场景回答。",
        "test": "项目中的测试相关内容如何帮助验证该功能？请举例说明。",
        "flow": "围绕流程“{name}”，请描述项目中关键步骤和交付产物。",
    }
    template = kind_prompt.get(point.kind, "请说明“{name}”在当前项目中的定位、主要职责和常见风险。")
    return template.format(name=point.name)


def _extract_key_points(name: str, summary: str) -> tuple[str, ...]:
    raw = f"{name} {summary}"
    tokens = _tokenize_for_scoring(raw)
    unique: list[str] = []
    for token in tokens:
        normalized = token.strip()
        if len(normalized) < 2:
            continue
        if normalized not in unique:
            unique.append(normalized)
    return tuple(unique[:4])


def _tokenize_for_scoring(text: str) -> Iterable[str]:
    for match in re.findall(r"[A-Za-z0-9_+#.-]{2,}|[\u4e00-\u9fff]{2,}", text.lower()):
        yield match


def _now_ts() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ordered_focus_points(
    points: list,
    focus_knowledge_point_ids: tuple[str, ...] | None,
) -> list:
    if not focus_knowledge_point_ids:
        return points
    focus_ids = dict.fromkeys(focus_knowledge_point_ids)
    by_id = {point.id: point for point in points}
    ordered: list = [by_id.get(pid) for pid in focus_ids]
    result: list = [point for point in ordered if point is not None]
    for point in points:
        if point not in result:
            result.append(point)
    return result


def _select_assessment_points(
    points: list,
    focus_knowledge_point_ids: tuple[str, ...] | None,
    question_count: int,
    prioritize_missed: bool,
    missed_records: list[MissedAssessmentRecord],
) -> list:
    focus_ids = focus_knowledge_point_ids or ()
    if not focus_ids and prioritize_missed:
        focus_ids = tuple(item.knowledge_point_id for item in missed_records)

    focus_ids = tuple(dict.fromkeys(focus_ids))
    by_id = {point.id: point for point in points}
    focused: list = [by_id.get(pid) for pid in focus_ids]
    selected: list = [point for point in focused if point is not None]

    if not selected and focus_ids:
        raise ValidationError("无法定位到可复测的知识点，正在改为普通出题。")

    for point in points:
        if point not in selected:
            selected.append(point)
        if len(selected) >= question_count:
            break

    return selected[:question_count]

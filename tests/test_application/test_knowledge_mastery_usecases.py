"""
test_knowledge_mastery_usecases.py — Knowledge Mastery 主用例测试。

覆盖：
  - 创建技能域与知识点
  - 证据关联后的掌握状态推进
  - 工作区概览聚合
"""
from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from legacy.desktop.application.container import AppContainer
from legacy.desktop.application.knowledge_mastery_usecases import (
    AssessmentQuestion,
    AssessmentQuestionResult,
    KnowledgeMasteryUseCase,
)
from legacy.desktop.domain.models.project_knowledge import ProjectKnowledgePoint
from legacy.desktop.application.workspace_usecases import WorkspaceUseCases
from legacy.desktop.config.settings import load_settings
from legacy.desktop.domain.errors import NotFoundError, ValidationError


def _build_container(tmp_path) -> AppContainer:
    settings = load_settings(override_env={
        "RAG_KB_ROOT": str(tmp_path / "kb"),
        "RAG_RUNTIME_DIR": str(tmp_path / "runtime"),
        "RAG_RETRIEVER_KIND": "keyword",
        "RAG_EMBED_PROVIDER": "none",
    })
    settings = dataclasses.replace(settings, db_path=Path(":memory:"))
    return AppContainer.build_for_testing(settings)


def _create_sample_point(uc: KnowledgeMasteryUseCase, ws_id: str, name: str):
    area = uc.create_skill_area(ws_id, f"技能域-{name}")
    point = uc.create_knowledge_point(
        workspace_id=ws_id,
        skill_area_id=area.id,
        name=f"知识点-{name}",
        summary=f"{name} 相关知识点",
        confidence=0.82,
    )
    return area, point

def _seed_project_points(
    container: AppContainer,
    workspace_id: str,
) -> None:
    container.project_knowledge_store.save_batch(
        [
            ProjectKnowledgePoint.create(
                workspace_id=workspace_id,
                name="FastAPI 路由",
                kind="tech_stack",
                summary="FastAPI 提供路由注册、请求校验和依赖注入能力。",
                source_path="/project/app/main.py",
                evidence="router = APIRouter()",
                confidence=0.84,
            ),
            ProjectKnowledgePoint.create(
                workspace_id=workspace_id,
                name="数据库流程",
                kind="flow",
                summary="项目将数据写入数据库前需经过校验、持久化和异常处理。",
                source_path="/project/app/flow.md",
                evidence="校验 -> 持久化 -> 返回响应",
                confidence=0.78,
            ),
        ]
    )


class TestKnowledgeMasteryUseCase:

    def test_claim_evidence_found_verified_flow(self, tmp_path):
        container = _build_container(tmp_path)
        uc = KnowledgeMasteryUseCase(
            container.workspace_store,
            container.mastery_store,
            container.project_knowledge_store,
        )
        ws = WorkspaceUseCases(container.workspace_store).create("ws", str(tmp_path / "repo"))

        _, point = _create_sample_point(uc, ws.id, "flow")
        record = uc.claim_mastery(
            workspace_id=ws.id,
            knowledge_point_id=point.id,
            note="已初步声明掌握",
        )
        assert record.status.value == "claimed"
        assert record.knowledge_point_id == point.id

        evidence = uc.create_evidence(
            workspace_id=ws.id,
            knowledge_point_id=point.id,
            source_path=str(tmp_path / "repo" / "readme.md"),
            snippet="掌握该流程可在文档 X 第 3 步找到示例。",
            confidence=0.9,
        )
        record = uc.mark_evidence_found(
            workspace_id=ws.id,
            record_id=record.id,
            evidence_id=evidence.id,
            note="已定位到证据来源",
        )
        assert record.status.value == "evidence_found"
        assert record.evidence_id == evidence.id
        assert "已定位到证据来源" in record.note

        verified = uc.mark_verified(
            workspace_id=ws.id,
            record_id=record.id,
            note="已完成验证",
            confidence=0.95,
        )
        assert verified.status.value == "verified"
        assert verified.confidence == 0.95

    def test_claim_is_idempotent(self, tmp_path):
        container = _build_container(tmp_path)
        uc = KnowledgeMasteryUseCase(
            container.workspace_store,
            container.mastery_store,
            container.project_knowledge_store,
        )
        ws = WorkspaceUseCases(container.workspace_store).create("ws-idemp", str(tmp_path / "repo"))

        _, point = _create_sample_point(uc, ws.id, "idempotent")
        first = uc.claim_mastery(ws.id, point.id, note="first")
        second = uc.claim_mastery(ws.id, point.id, note="second")

        assert second.id == first.id
        assert second.note == first.note

    def test_overview_aggregates_mastery_status(self, tmp_path):
        container = _build_container(tmp_path)
        uc = KnowledgeMasteryUseCase(
            container.workspace_store,
            container.mastery_store,
            container.project_knowledge_store,
        )
        ws = WorkspaceUseCases(container.workspace_store).create("ws-overview", str(tmp_path / "repo"))

        area = uc.create_skill_area(ws.id, "Python")
        p1 = uc.create_knowledge_point(
            workspace_id=ws.id,
            skill_area_id=area.id,
            name="知识点1",
            summary="第一条",
            confidence=0.7,
        )
        p2 = uc.create_knowledge_point(
            workspace_id=ws.id,
            skill_area_id=area.id,
            name="知识点2",
            summary="第二条",
            confidence=0.8,
        )

        uc.claim_mastery(ws.id, p1.id, note="claim")
        evidence = uc.create_evidence(
            workspace_id=ws.id,
            knowledge_point_id=p2.id,
            source_path=str(tmp_path / "repo" / "q.md"),
            snippet="snippet2",
        )
        p2_record = uc.mark_evidence_found(
            workspace_id=ws.id,
            record_id=uc.claim_mastery(ws.id, p2.id, note="claim").id,
            evidence_id=evidence.id,
        )
        uc.mark_verified(
            workspace_id=ws.id,
            record_id=p2_record.id,
            note="verify",
        )

        overview = uc.get_overview(ws.id)
        assert overview.workspace_id == ws.id
        assert overview.total_points == 2
        assert overview.total_records == 2
        assert overview.claimed == 1
        assert overview.evidence_found == 0
        assert overview.verified == 1

    def test_validation_errors(self, tmp_path):
        container = _build_container(tmp_path)
        uc = KnowledgeMasteryUseCase(
            container.workspace_store,
            container.mastery_store,
            container.project_knowledge_store,
        )
        ws = WorkspaceUseCases(container.workspace_store).create("ws-valid", str(tmp_path / "repo"))
        _create_sample_point(uc, ws.id, "sample")

        with pytest.raises(NotFoundError):
            uc.create_knowledge_point(ws.id, "missing-area", "p", "summary")

        with pytest.raises(NotFoundError):
            uc.claim_mastery("unknown", "missing-point")

        with pytest.raises(ValidationError):
            uc.create_skill_area(ws.id, "   ")

    def test_verified_requires_evidence(self, tmp_path):
        container = _build_container(tmp_path)
        uc = KnowledgeMasteryUseCase(
            container.workspace_store,
            container.mastery_store,
            container.project_knowledge_store,
        )
        ws = WorkspaceUseCases(container.workspace_store).create("ws-verify", str(tmp_path / "repo2"))
        _, p = _create_sample_point(uc, ws.id, "verify")
        record = uc.claim_mastery(ws.id, p.id, note="claim")

        with pytest.raises(ValidationError):
            uc.mark_verified(ws.id, record.id)

    def test_create_assessment_session_from_project_points(self, tmp_path):
        container = _build_container(tmp_path)
        uc = KnowledgeMasteryUseCase(
            container.workspace_store,
            container.mastery_store,
            container.project_knowledge_store,
        )
        ws = WorkspaceUseCases(container.workspace_store).create("ws-assess", str(tmp_path / "repo"))

        _seed_project_points(container, ws.id)
        session = uc.create_assessment_session(workspace_id=ws.id, question_count=2)

        assert session.workspace_id == ws.id
        assert len(session.questions) == 2
        assert session.questions[0].prompt
        assert session.questions[0].expected_points

    def test_evaluate_assessment_answer(self, tmp_path):
        container = _build_container(tmp_path)
        uc = KnowledgeMasteryUseCase(
            container.workspace_store,
            container.mastery_store,
            container.project_knowledge_store,
        )
        ws = WorkspaceUseCases(container.workspace_store).create("ws-answer", str(tmp_path / "repo"))

        _seed_project_points(container, ws.id)
        session = uc.create_assessment_session(workspace_id=ws.id, question_count=1)
        question = session.questions[0]
        result = uc.evaluate_answer(
            workspace_id=ws.id,
            question=AssessmentQuestion(
                id=question.id,
                workspace_id=question.workspace_id,
                knowledge_point_id=question.knowledge_point_id,
                prompt=question.prompt,
                source_path=question.source_path,
                expected_points=question.expected_points,
                reference=question.reference,
            ),
            answer="这两个模块负责路由和请求处理，配合校验和持久化完成数据处理流程。",
        )

        assert result.workspace_id == ws.id
        assert 0 <= result.score <= 1
        assert result.status in {"已掌握", "基本理解", "需要补充"}

    def test_generate_ability_gap_report(self, tmp_path):
        container = _build_container(tmp_path)
        uc = KnowledgeMasteryUseCase(
            container.workspace_store,
            container.mastery_store,
            container.project_knowledge_store,
        )
        ws = WorkspaceUseCases(container.workspace_store).create("ws-report", str(tmp_path / "repo"))

        _seed_project_points(container, ws.id)
        session = uc.create_assessment_session(workspace_id=ws.id, question_count=2)
        q0 = session.questions[0]
        q1 = session.questions[1]

        results = (
            AssessmentQuestionResult(
                question_id=q0.id,
                workspace_id=ws.id,
                status="已掌握",
                score=0.95,
                matched_points=q0.expected_points,
                missing_points=(),
                feedback="答得完整。",
            ),
            AssessmentQuestionResult(
                question_id=q1.id,
                workspace_id=ws.id,
                status="需要补充",
                score=0.2,
                matched_points=(),
                missing_points=("校验", "持久化"),
                feedback="缺少关键步骤。",
            ),
        )
        report = uc.generate_ability_gap_report(session=session, results=results)

        assert report.workspace_id == ws.id
        assert report.total_questions == 2
        assert report.mastered_count == 1
        assert report.basic_count == 0
        assert report.needs_improvement_count == 1
        assert len(report.mastered_knowledge_points) == 1
        assert len(report.weak_knowledge_points) == 1
        assert q1.source_path in report.suggested_reading_files
        assert report.follow_up_question_ids == (q1.id,)
        assert len(report.next_learning_order) == 1
        assert report.overview.startswith("共 2 题")

    def test_prioritize_missed_questions_in_next_session(self, tmp_path):
        container = _build_container(tmp_path)
        uc = KnowledgeMasteryUseCase(
            container.workspace_store,
            container.mastery_store,
            container.project_knowledge_store,
        )
        ws = WorkspaceUseCases(container.workspace_store).create("ws-missed", str(tmp_path / "repo"))

        _seed_project_points(container, ws.id)
        first_session = uc.create_assessment_session(workspace_id=ws.id, question_count=1)
        first_q = first_session.questions[0]
        weak_result = uc.evaluate_answer(
            workspace_id=ws.id,
            question=first_q,
            answer="仅回答了部分内容。",
        )
        uc.record_assessment_attempt(
            workspace_id=ws.id,
            session=first_session,
            question_id=first_q.id,
            answer="仅回答了部分内容。",
            result=weak_result,
        )

        follow_up_session = uc.create_assessment_session(
            workspace_id=ws.id,
            question_count=2,
            prioritize_missed=True,
        )
        assert follow_up_session.focus_knowledge_point_ids[0] == first_q.knowledge_point_id
        assert follow_up_session.questions[0].knowledge_point_id == first_q.knowledge_point_id

    def test_follow_up_cleared_when_mastered(self, tmp_path):
        container = _build_container(tmp_path)
        uc = KnowledgeMasteryUseCase(
            container.workspace_store,
            container.mastery_store,
            container.project_knowledge_store,
        )
        ws = WorkspaceUseCases(container.workspace_store).create("ws-clear", str(tmp_path / "repo"))

        _seed_project_points(container, ws.id)
        first_session = uc.create_assessment_session(workspace_id=ws.id, question_count=1)
        q0 = first_session.questions[0]

        weak_result = uc.evaluate_answer(
            workspace_id=ws.id,
            question=q0,
            answer="尚缺少完整描述。",
        )
        uc.record_assessment_attempt(
            workspace_id=ws.id,
            session=first_session,
            question_id=q0.id,
            answer="尚缺少完整描述。",
            result=weak_result,
        )

        next_session = uc.create_assessment_session(
            workspace_id=ws.id,
            question_count=1,
            prioritize_missed=True,
        )
        assert next_session.questions[0].knowledge_point_id == q0.knowledge_point_id

        strong_result = uc.evaluate_answer(
            workspace_id=ws.id,
            question=next_session.questions[0],
            answer=" ".join(next_session.questions[0].expected_points) + " 进行了完整复核",
        )
        uc.record_assessment_attempt(
            workspace_id=ws.id,
            session=next_session,
            question_id=next_session.questions[0].id,
            answer="这次给出完整并复核了流程。",
            result=strong_result,
        )
        assert all(
            item.knowledge_point_id != q0.id for item in uc._missed_records.get(ws.id, [])
        )

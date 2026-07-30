import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import CoachAssessmentOverlay from "./CoachAssessmentOverlay.vue";

const knowledgePoints = {
  items: [{ id: "kp-1", title: "Web 入口" }],
};
const skills = {
  items: [
    { id: "skill-1", name: "FastAPI", project_evidence: "mapped" },
    { id: "skill-2", name: "Docker", project_evidence: "no_project_evidence" },
  ],
};

describe("CoachAssessmentOverlay", () => {
  it("lets the user choose a target and emits start without calling an API", async () => {
    const wrapper = mount(CoachAssessmentOverlay, {
      props: { open: true, knowledgePoints, skills },
    });

    await wrapper.find('[data-coach-assessment-field="target-id"]').setValue("kp-1");
    await wrapper.find("form").trigger("submit");

    expect(wrapper.emitted("start")[0]).toEqual([
      { target_type: "knowledge_point", target_id: "kp-1", restart: false },
    ]);
  });

  it("never exposes scoring basis before an answer and emits the answer contract", async () => {
    const wrapper = mount(CoachAssessmentOverlay, {
      props: {
        open: true,
        knowledgePoints,
        skills,
        session: {
          id: "session-1",
          target_type: "knowledge_point",
          target_id: "kp-1",
          target: { label: "Web 入口" },
          question_count: 1,
          current_question_id: "question-1",
          questions: [{
            id: "question-1",
            prompt: "说明当前项目的 Web 入口。",
            question_type: "code_location",
            source_ids: ["source-1"],
            expected_points: ["绝不能显示的评分要点"],
          }],
        },
      },
    });

    expect(wrapper.text()).toContain("说明当前项目的 Web 入口");
    expect(wrapper.text()).not.toContain("绝不能显示的评分要点");
    expect(wrapper.text()).not.toContain("命中证据");
    await wrapper.find('[data-coach-assessment-field="answer"]').setValue("app.py 创建 FastAPI 应用");
    await wrapper.find(".coach-assessment-answer").trigger("submit");

    expect(wrapper.emitted("submit-answer")[0]).toEqual([{
      session_id: "session-1",
      question_id: "question-1",
      answer: "app.py 创建 FastAPI 应用",
    }]);
  });

  it("shows only returned post-answer evidence, gaps, confidence and sources", () => {
    const wrapper = mount(CoachAssessmentOverlay, {
      props: {
        open: true,
        session: {
          id: "session-1",
          target_type: "knowledge_point",
          target_id: "kp-1",
          question_count: 1,
          current_question_id: "question-1",
          questions: [{ id: "question-1", prompt: "说明入口", question_type: "concept", source_ids: ["source-1"] }],
          sources: {
            "source-1": { id: "source-1", path: "app.py", excerpt: "FastAPI()" },
          },
        },
        assessmentResult: {
          status: "developing",
          confidence: 0.6,
          evaluator: "rule",
          matched_evidence: [{ point: "FastAPI", evidence: "FastAPI" }],
          missing_points: ["app.py"],
          source_ids: ["source-1"],
        },
      },
    });

    expect(wrapper.text()).toContain("发展中");
    expect(wrapper.text()).toContain("置信度：60%");
    expect(wrapper.text()).toContain("FastAPI：FastAPI");
    expect(wrapper.text()).toContain("app.py");
    expect(wrapper.text()).toContain("source-1");
  });

  it("emits real source payloads after grading and shows completion when no question remains", async () => {
    const wrapper = mount(CoachAssessmentOverlay, {
      props: {
        open: true,
        session: {
          id: "session-1",
          status: "completed",
          target_type: "knowledge_point",
          target_id: "kp-1",
          question_count: 1,
          current_question_id: null,
          questions: [{
            id: "question-1",
            prompt: "说明入口",
            answered: true,
            result: {
              id: "result-1",
              status: "mastered",
              confidence: 0.8,
              evaluator: "rule",
              matched_evidence: [],
              missing_points: [],
              source_ids: ["source-1"],
            },
          }],
          sources: {
            "source-1": { id: "source-1", path: "app.py", excerpt: "FastAPI()" },
          },
        },
        assessmentResult: {
          id: "result-1",
          status: "mastered",
          confidence: 0.8,
          evaluator: "rule",
          matched_evidence: [],
          missing_points: [],
          source_ids: ["source-1"],
        },
      },
    });

    expect(wrapper.text()).toContain("本次评估已完成");
    await wrapper.find('[data-coach-assessment-action="open-result-sources"]').trigger("click");
    expect(wrapper.emitted("open-sources")[0]).toEqual([{
      title: "评估结果来源",
      source_ids: ["source-1"],
      sources: {
        "source-1": { id: "source-1", path: "app.py", excerpt: "FastAPI()" },
      },
    }]);
  });
});

import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import LearningMapView from "./LearningMapView.vue";

function mountMap(overrides = {}) {
  return mount(LearningMapView, {
    props: {
      selectedProjectId: "project-1",
      overview: {
        summary: "FastAPI 项目的本地知识教练。",
        source_ids: ["source-1"],
        sources: {
          "source-1": { id: "source-1", path: "app.py", excerpt: "FastAPI()" },
        },
        scope_notice: "仅表示当前项目、当前来源版本下的项目知识分析。",
      },
      knowledgePoints: {
        items: [
          {
            id: "kp-1",
            title: "Web 入口",
            category: "architecture",
            summary: "从 app.py 启动。",
            source_ids: ["source-1"],
          },
        ],
        sources: {
          "source-1": { id: "source-1", path: "app.py", excerpt: "FastAPI()" },
        },
      },
      skills: {
        scope_notice: "技能映射仅辅助解释当前项目知识，不是整体职业能力评价。",
        items: [
          { id: "skill-1", name: "FastAPI", project_evidence: "mapped", mappings: [{}] },
          { id: "skill-2", name: "Docker", project_evidence: "no_project_evidence", mappings: [] },
        ],
      },
      coverage: {
        can_assess: true,
        summary: { assessed_count: 1, coverage_ratio: 1 },
        knowledge_points: [{ id: "kp-1", status: "mastered", source_ids: ["source-1"] }],
        skills: [
          {
            id: "skill-1",
            status: "developing",
            project_evidence: "mapped",
            mapped_knowledge_point_count: 1,
            assessed_knowledge_point_count: 1,
          },
          {
            id: "skill-2",
            status: null,
            project_evidence: "no_project_evidence",
            assessment_state: "no_project_evidence",
          },
        ],
        recent_assessments: [{
          id: "result-1",
          status: "mastered",
          score: 1,
          confidence: 0.8,
          valid_for_current_sources: true,
          source_ids: ["source-1"],
        }],
        sources: {
          "source-1": { id: "source-1", path: "app.py", excerpt: "FastAPI()" },
        },
      },
      ...overrides,
    },
  });
}

describe("LearningMapView", () => {
  it("labels only current-project assessment states and avoids career conclusions", () => {
    const wrapper = mountMap();

    expect(wrapper.text()).toContain("当前项目知识地图");
    expect(wrapper.text()).toContain("已掌握");
    expect(wrapper.text()).toContain("发展中");
    expect(wrapper.text()).toContain("当前项目无证据");
    expect(wrapper.text()).toContain("不能据此得出能力结论");
    expect(wrapper.text()).not.toContain("职业能力不足");
  });

  it("emits targeted assessment, learning, and real source payloads", async () => {
    const wrapper = mountMap();

    await wrapper.find('[data-learning-map-action="assess-knowledge-point"]').trigger("click");
    await wrapper.find('[data-learning-map-action="learn-knowledge-point"]').trigger("click");
    await wrapper.find('[data-learning-map-action="learn-skill"]').trigger("click");
    await wrapper.find('[data-learning-map-action="open-knowledge-sources"]').trigger("click");
    await wrapper.find('[data-learning-map-action="open-overview-sources"]').trigger("click");
    await wrapper.find('[data-learning-map-action="open-assessment-sources"]').trigger("click");

    expect(wrapper.emitted("start-assessment")[0]).toEqual([
      { target_type: "knowledge_point", target_id: "kp-1" },
    ]);
    expect(wrapper.emitted("start-learning")).toEqual([
      [{ target_type: "knowledge_point", target_id: "kp-1", origin_type: "learning_map" }],
      [{ target_type: "skill", target_id: "skill-1", origin_type: "learning_map" }],
    ]);
    expect(wrapper.emitted("open-sources")[0][0]).toMatchObject({
      title: "Web 入口",
      source_ids: ["source-1"],
      sources: {
        "source-1": { path: "app.py", excerpt: "FastAPI()" },
      },
    });
    expect(wrapper.emitted("open-sources")).toHaveLength(3);
  });

  it("makes stale analysis explicit and disables every targeted assessment", () => {
    const wrapper = mountMap({
      coverage: {
        stale: true,
        can_assess: false,
        summary: {},
        knowledge_points: [{ id: "kp-1", status: "unassessed", source_ids: ["source-1"] }],
        skills: [{ id: "skill-1", status: "unassessed", project_evidence: "mapped" }],
      },
    });

    expect(wrapper.text()).toContain("当前分析已过期");
    expect(wrapper.findAll('[data-learning-map-action^="assess-"]').every((button) => button.attributes("disabled") !== undefined)).toBe(true);
    expect(wrapper.findAll('[data-learning-map-action^="learn-"]').every((button) => button.attributes("disabled") !== undefined)).toBe(true);
  });
});

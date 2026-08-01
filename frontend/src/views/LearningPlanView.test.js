import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import LearningPlanView from "./LearningPlanView.vue";

function planItem(overrides = {}) {
  return {
    id: "item-1",
    plan_id: "plan-draft",
    stable_key: "learn:web-entry",
    item_type: "learning",
    objective: "理解 Web 入口",
    knowledge_point_id: "kp-1",
    skill_node_id: "skill-1",
    source_ids: ["source-1"],
    reading_sources: [{
      id: "source-1",
      path: "app.py",
      excerpt: "app = FastAPI()",
      locator: { line_start: 10 },
    }],
    practice_question: "入口如何启动？",
    completion_criteria: "能指出入口和真实来源。",
    estimated_minutes: 25,
    status: "todo",
    sort_order: 0,
    ...overrides,
  };
}

function currentPlan(overrides = {}) {
  return {
    stale: false,
    scope_notice: "学习计划仅针对当前项目和当前来源版本，不代表整体职业能力。",
    sources: {
      "source-1": {
        id: "source-1",
        path: "app.py",
        excerpt: "app = FastAPI()",
      },
    },
    draft: {
      id: "plan-draft",
      revision: 2,
      status: "draft",
      items_hash: "items-hash",
      progress_hash: "draft-progress",
      can_edit_structure: true,
      can_confirm: true,
      can_update_progress: false,
      items: [
        planItem(),
        planItem({
          id: "item-2",
          stable_key: "learn:routes",
          objective: "理解路由分发",
          knowledge_point_id: "kp-2",
          source_ids: ["source-2"],
          reading_sources: [{
            id: "source-2",
            path: "backend/routes/coach.py",
            excerpt: "def dispatch_coach_route",
          }],
          sort_order: 1,
        }),
      ],
    },
    confirmed: null,
    history: [],
    ...overrides,
  };
}

function mountPlan(overrides = {}) {
  return mount(LearningPlanView, {
    props: {
      selectedProjectId: "project-1",
      currentPlan: currentPlan(),
      obsidianConnection: { id: "connection-1", status: "active" },
      ...overrides,
    },
  });
}

describe("LearningPlanView", () => {
  it("edits, reorders and emits a complete draft with optimistic concurrency fields", async () => {
    const wrapper = mountPlan();
    const objectives = wrapper.findAll('[data-learning-plan-field="objective"]');
    await objectives[0].setValue("掌握 Web 入口");
    await wrapper.findAll('[data-learning-plan-action="move-down"]')[0].trigger("click");
    await wrapper.find('[data-learning-plan-action="save"]').trigger("submit");

    const payload = wrapper.emitted("update-plan")[0][0];
    expect(payload).toMatchObject({
      planId: "plan-draft",
      expectedRevision: 2,
      expectedItemsHash: "items-hash",
    });
    expect(payload.items[0]).toEqual({
      stable_key: "learn:routes",
      item_type: "learning",
      objective: "理解路由分发",
      knowledge_point_id: "kp-2",
      skill_node_id: "skill-1",
      source_ids: ["source-2"],
      practice_question: "入口如何启动？",
      completion_criteria: "能指出入口和真实来源。",
      estimated_minutes: 25,
      status: "todo",
      sort_order: 0,
    });
    expect(payload.items[1].objective).toBe("掌握 Web 入口");
    expect(payload.items[1].sort_order).toBe(1);
  });

  it("confirms with the draft hash and emits real source data", async () => {
    const wrapper = mountPlan();

    await wrapper.find('[data-learning-plan-action="confirm"]').trigger("click");
    await wrapper.findAll('[data-learning-plan-action="open-sources"]')[0].trigger("click");

    expect(wrapper.emitted("confirm")[0][0]).toEqual({
      planId: "plan-draft",
      expectedRevision: 2,
      expectedItemsHash: "items-hash",
    });
    expect(wrapper.emitted("open-sources")[0][0]).toMatchObject({
      title: "理解 Web 入口",
      source_ids: ["source-1"],
      sources: {
        "source-1": {
          path: "app.py",
          excerpt: "app = FastAPI()",
        },
      },
    });
    expect(wrapper.text()).toContain("不代表整体职业能力");
  });

  it("keeps a confirmed plan read-only and updates only item statuses", async () => {
    const confirmed = {
      ...currentPlan().draft,
      id: "plan-confirmed",
      status: "confirmed",
      progress_hash: "progress-hash",
      can_edit_structure: false,
      can_confirm: false,
      can_update_progress: true,
      items: [planItem({ id: "confirmed-item", plan_id: "plan-confirmed" })],
    };
    const wrapper = mountPlan({
      currentPlan: currentPlan({ draft: null, confirmed }),
    });

    expect(wrapper.find('[data-learning-plan-field="objective"]').exists()).toBe(false);
    await wrapper.find('[data-learning-plan-field="status"]').setValue("in_progress");
    await wrapper.find('[data-learning-plan-action="save-progress"]').trigger("click");

    expect(wrapper.emitted("update-plan")[0][0]).toEqual({
      planId: "plan-confirmed",
      itemStatuses: { "confirmed-item": "in_progress" },
      expectedProgressHash: "progress-hash",
    });
  });

  it("starts or continues only learning tasks from the confirmed plan", async () => {
    const confirmed = {
      ...currentPlan().draft,
      id: "plan-confirmed",
      status: "confirmed",
      can_edit_structure: false,
      can_confirm: false,
      can_update_progress: true,
      items: [
        planItem({
          id: "todo-item",
          plan_id: "plan-confirmed",
          status: "todo",
        }),
        planItem({
          id: "progress-item",
          plan_id: "plan-confirmed",
          stable_key: "learn:routes",
          status: "in_progress",
        }),
        planItem({
          id: "source-gap-item",
          plan_id: "plan-confirmed",
          stable_key: "source:missing",
          item_type: "source_gap",
          status: "todo",
        }),
      ],
    };
    const wrapper = mountPlan({
      currentPlan: currentPlan({ draft: null, confirmed }),
    });
    const learningButtons = wrapper.findAll('[data-learning-plan-action="start-learning"]');

    expect(learningButtons).toHaveLength(2);
    expect(learningButtons[0].text()).toBe("开始学习");
    expect(learningButtons[1].text()).toBe("继续学习");
    await learningButtons[1].trigger("click");
    expect(wrapper.emitted("start-learning")).toEqual([[
      { planId: "plan-confirmed", planItemId: "progress-item" },
    ]]);
  });

  it("blocks stale structure actions and Obsidian publication without fabricating completion", () => {
    const wrapper = mountPlan({
      currentPlan: currentPlan({ stale: true }),
    });

    expect(wrapper.text()).toContain("当前分析已过期");
    expect(wrapper.find('[data-learning-plan-action="generate"]').attributes("disabled")).toBeDefined();
    expect(wrapper.find('[data-learning-plan-action="save"]').attributes("disabled")).toBeDefined();
    expect(wrapper.find('[data-learning-plan-action="confirm"]').attributes("disabled")).toBeDefined();
    expect(wrapper.text()).not.toContain("已写入 Obsidian");
  });
});

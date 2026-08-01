import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import CoachLearningSessionOverlay from "./CoachLearningSessionOverlay.vue";

function baseSession(overrides = {}) {
  return {
    id: "learning-1",
    status: "learning",
    version: 2,
    read_only: false,
    progress: {
      current: 1,
      total: 2,
      completed: 0,
    },
    current_step: {
      id: "step-1",
      title: "理解订单查询",
      explanation: "订单列表由当前项目的 orders 表驱动。",
      source_ids: ["source-1"],
      context: {
        title: "项目代码上下文",
        content: "backend/storage/orders.py\nSELECT * FROM orders",
      },
    },
    current_exercise: null,
    attempts: [],
    sources: {
      "source-1": {
        id: "source-1",
        path: "backend/storage/orders.py",
        excerpt: "def list_orders(): ...",
      },
    },
    allowed_actions: ["begin_question", "abandon"],
    recommended_action: "begin_question",
    ...overrides,
  };
}

describe("CoachLearningSessionOverlay", () => {
  it("lets the coach entry choose one current-project target before starting", async () => {
    const wrapper = mount(CoachLearningSessionOverlay, {
      props: {
        open: true,
        knowledgePoints: {
          items: [{ id: "kp-1", title: "Web 入口" }],
        },
        skills: {
          items: [
            { id: "skill-1", name: "FastAPI", project_evidence: "mapped" },
            { id: "skill-2", name: "Docker", project_evidence: "no_project_evidence" },
          ],
        },
      },
    });

    await wrapper.find('[data-coach-learning-field="target-id"]').setValue("kp-1");
    await wrapper.find('[data-coach-learning-action="start"]').trigger("submit");

    expect(wrapper.emitted("start")).toEqual([[
      { target_type: "knowledge_point", target_id: "kp-1", origin_type: "coach" },
    ]]);
    expect(wrapper.text()).not.toContain("Docker");
  });

  it("renders one current knowledge point, progress, context and real sources", async () => {
    const wrapper = mount(CoachLearningSessionOverlay, {
      props: {
        open: true,
        session: baseSession(),
      },
    });

    expect(wrapper.text()).toContain("知识点 1 / 2");
    expect(wrapper.text()).toContain("理解订单查询");
    expect(wrapper.text()).toContain("订单列表由当前项目的 orders 表驱动");
    expect(wrapper.text()).toContain("backend/storage/orders.py");
    expect(wrapper.text()).toContain("def list_orders(): ...");
    expect(wrapper.text()).toContain("SELECT * FROM orders");
    expect(wrapper.findAll('[data-coach-learning-action="begin-question"]')).toHaveLength(1);
    expect(wrapper.find('[data-coach-learning-action="retry"]').exists()).toBe(false);

    await wrapper.find('[data-coach-learning-action="begin-question"]').trigger("click");
    expect(wrapper.emitted("transition")[0]).toEqual([{
      session_id: "learning-1",
      expected_version: 2,
      action: "begin_question",
    }]);
  });

  it("renders structured SQL fixtures and preserves raw SQL whitespace", async () => {
    const wrapper = mount(CoachLearningSessionOverlay, {
      props: {
        open: true,
        session: baseSession({
          status: "awaiting_answer",
          version: 4,
          current_exercise: {
            id: "exercise-1",
            question_type: "sql_query",
            prompt: "查询金额大于 10 的订单名称和金额。",
            reference_answer: "绝不能提前显示",
            scoring_basis: ["绝不能提前显示的评分规则"],
            sql_fixture: {
              schema: [{
                name: "orders",
                columns: [
                  { name: "id", type: "INTEGER", nullable: false },
                  { name: "name", type: "TEXT", nullable: false },
                  { name: "total", type: "REAL", nullable: true },
                ],
              }],
              seed_rows: {
                orders: [
                  { id: 1, name: "A-100", total: 25.5 },
                  { id: 2, name: "A-101", total: null },
                ],
              },
            },
          },
          allowed_actions: ["submit", "abandon"],
          recommended_action: null,
        }),
      },
    });

    expect(wrapper.text()).toContain("查询金额大于 10 的订单名称和金额");
    expect(wrapper.text()).toContain("固定练习数据");
    expect(wrapper.text()).toContain("orders");
    expect(wrapper.text()).toContain("INTEGER");
    expect(wrapper.text()).toContain("A-100");
    expect(wrapper.text()).toContain("NULL");
    expect(wrapper.text()).not.toContain("绝不能提前显示");

    const rawSql = "\nSELECT name,\n       total\nFROM orders\nWHERE total > 10;\n";
    await wrapper.find('[data-coach-learning-field="answer"]').setValue(rawSql);
    await wrapper.find('[data-coach-learning-action="submit"]').trigger("submit");

    const payload = wrapper.emitted("submit-attempt")[0][0];
    expect(payload).toMatchObject({
      session_id: "learning-1",
      exercise_id: "exercise-1",
      answer: rawSql,
      expected_version: 4,
    });
    expect(payload.idempotency_key).toEqual(expect.any(String));
    expect(payload.idempotency_key.length).toBeGreaterThan(0);

    await wrapper.setProps({ submitting: true });
    await wrapper.find('[data-coach-learning-action="submit"]').trigger("submit");
    expect(wrapper.emitted("submit-attempt")).toHaveLength(1);
    expect(wrapper.find("textarea").attributes("disabled")).toBeDefined();
  });

  it("does not expose a submit form unless the server allows submit", () => {
    const wrapper = mount(CoachLearningSessionOverlay, {
      props: {
        open: true,
        session: baseSession({
          status: "awaiting_answer",
          current_exercise: {
            id: "exercise-1",
            question_type: "concept",
            prompt: "说明项目入口。",
          },
          allowed_actions: ["abandon"],
        }),
      },
    });

    expect(wrapper.find('[data-coach-learning-field="answer"]').exists()).toBe(false);
  });

  it("shows explicit grading feedback and only server-allowed next actions", async () => {
    const wrapper = mount(CoachLearningSessionOverlay, {
      props: {
        open: true,
        session: baseSession({
          status: "evaluated",
          version: 6,
          current_exercise: {
            id: "exercise-1",
            question_type: "sql_query",
            prompt: "查询订单。",
          },
          attempts: [{
            id: "attempt-1",
            attempt_no: 1,
            score: 0,
            evaluator: "sql_deterministic",
            feedback: "结果缺少 total 列，请检查 SELECT 列表。",
            error: null,
            counts_for_mastery: true,
            result_preview: {
              columns: ["name"],
              rows: [["A-100"]],
            },
          }],
          allowed_actions: ["retry", "reveal", "abandon"],
          recommended_action: "retry",
        }),
      },
    });

    expect(wrapper.text()).toContain("第 1 次作答");
    expect(wrapper.text()).toContain("得分 0%");
    expect(wrapper.text()).toContain("结果缺少 total 列");
    expect(wrapper.text()).toContain("A-100");
    expect(wrapper.find('[data-coach-learning-action="retry"]').exists()).toBe(true);
    expect(wrapper.find('[data-coach-learning-action="reveal"]').exists()).toBe(true);
    expect(wrapper.find('[data-coach-learning-action="next"]').exists()).toBe(false);

    await wrapper.find('[data-coach-learning-action="retry"]').trigger("click");
    await wrapper.find('[data-coach-learning-action="reveal"]').trigger("click");
    expect(wrapper.emitted("transition")).toEqual([
      [{ session_id: "learning-1", expected_version: 6, action: "retry" }],
      [{ session_id: "learning-1", expected_version: 6, action: "reveal" }],
    ]);
  });

  it("blocks writes for stale/read-only sessions and exposes recovery errors", () => {
    const wrapper = mount(CoachLearningSessionOverlay, {
      props: {
        open: true,
        error: "会话恢复失败，请刷新后重试。",
        session: baseSession({
          status: "awaiting_answer",
          read_only: true,
          read_only_reason: "analysis_stale",
          current_exercise: {
            id: "exercise-1",
            question_type: "concept",
            prompt: "说明项目入口。",
          },
          allowed_actions: ["retry", "next", "abandon"],
        }),
      },
    });

    expect(wrapper.text()).toContain("来源版本已变化");
    expect(wrapper.text()).toContain("会话恢复失败");
    expect(wrapper.find("textarea").exists()).toBe(false);
    expect(wrapper.find('[data-coach-learning-action="retry"]').exists()).toBe(false);
    expect(wrapper.find('[data-coach-learning-action="next"]').exists()).toBe(false);
    expect(wrapper.find('[data-coach-learning-action="abandon"]').exists()).toBe(false);
  });

  it("renders loading and completed states without inventing another action", () => {
    const loading = mount(CoachLearningSessionOverlay, {
      props: { open: true, loading: true, session: null },
    });
    expect(loading.text()).toContain("正在恢复学习会话");

    const completed = mount(CoachLearningSessionOverlay, {
      props: {
        open: true,
        session: baseSession({
          status: "completed",
          current_exercise: null,
          progress: { current: 2, total: 2, completed: 2 },
          allowed_actions: [],
        }),
      },
    });
    expect(completed.text()).toContain("本次逐点学习已完成");
    expect(completed.text()).not.toContain("当前来源版本已变化");
    expect(completed.findAll("[data-coach-learning-action]")).toHaveLength(1);
    expect(completed.find('[data-coach-learning-action="close"]').exists()).toBe(true);
  });
});

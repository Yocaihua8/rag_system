import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import AnswerPanel from "./AnswerPanel.vue";

describe("AnswerPanel", () => {
  it("renders loading, error, and empty states without an answer", () => {
    expect(mount(AnswerPanel, { props: { loading: true } }).text()).toContain("正在生成回答...");
    expect(mount(AnswerPanel, { props: { error: "服务断开" } }).text()).toContain("服务断开");
    expect(mount(AnswerPanel).text()).toContain("提交问题后会在这里显示回答。");
  });

  it("shows the answer body and feedback without source detail clutter", () => {
    const wrapper = mount(AnswerPanel, {
      props: {
        answerResult: {
          answer: "回答正文",
          mode: "api",
          provider: "deepseek",
          source_quality: { label: "来源充分" },
          sources: [{ path: "README.md", snippet: "项目入口" }],
        },
        lastAnswerMessageId: "m1",
        answerFeedbackSubmitting: true,
      },
    });

    expect(wrapper.text()).toContain("回答正文");
    expect(wrapper.text()).not.toContain("mode: api");
    expect(wrapper.text()).not.toContain("provider: deepseek");
    expect(wrapper.text()).not.toContain("来源充分");
    expect(wrapper.text()).not.toContain("README.md");
    expect(wrapper.find('[data-feedback-rating="useful"]').attributes("disabled")).toBeDefined();
  });

  it("emits feedback from visible controls", async () => {
    const wrapper = mount(AnswerPanel, {
      props: {
        answerResult: { answer: "回答正文", sources: [] },
        lastAnswerMessageId: "m1",
      },
    });

    await wrapper.find('[data-feedback-rating="useful"]').trigger("click");

    expect(wrapper.emitted("submit-answer-feedback")[0]).toEqual(["useful"]);
    expect(wrapper.text()).not.toContain("建议工具");
    expect(wrapper.text()).not.toContain("可用工具结果");
    expect(wrapper.text()).not.toContain("下一问上下文");
  });
});

import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import AnswerPanel from "./AnswerPanel.vue";

describe("AnswerPanel", () => {
  it("renders loading, error, and empty states without an answer", () => {
    expect(mount(AnswerPanel, { props: { loading: true } }).text()).toContain("正在生成回答...");
    expect(mount(AnswerPanel, { props: { error: "服务断开" } }).text()).toContain("服务断开");
    expect(mount(AnswerPanel).text()).toContain("提交问题后会在这里显示回答。");
  });

  it("shows answer metadata, source fallback text, and disabled feedback while submitting", () => {
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

    expect(wrapper.text()).toContain("mode: api");
    expect(wrapper.text()).toContain("provider: deepseek");
    expect(wrapper.text()).toContain("回答正文");
    expect(wrapper.text()).toContain("来源充分");
    expect(wrapper.text()).toContain("README.md");
    expect(wrapper.find('[data-feedback-rating="useful"]').attributes("disabled")).toBeDefined();
  });

  it("emits feedback and tool context actions from visible controls", async () => {
    const wrapper = mount(AnswerPanel, {
      props: {
        answerResult: { answer: "回答正文", sources: [] },
        lastAnswerMessageId: "m1",
        toolSuggestion: { tool: "search_sources", arguments: { query: "RAG" }, reason: "来源不足" },
        lastUsableToolRun: { id: "run1", tool_name: "search_sources", status: "success", result: { query: "RAG" } },
        currentToolContextRunId: "run1",
      },
    });

    await wrapper.find('[data-feedback-rating="useful"]').trigger("click");
    await wrapper.find(".tool-suggestion button").trigger("click");
    await wrapper.find(".tool-context-card button").trigger("click");
    await wrapper.find(".tool-context-notice button").trigger("click");

    expect(wrapper.emitted("submit-answer-feedback")[0]).toEqual(["useful"]);
    expect(wrapper.emitted("run-tool-suggestion")[0]).toEqual([
      { tool: "search_sources", arguments: { query: "RAG" }, reason: "来源不足" },
    ]);
    expect(wrapper.emitted("use-tool-result-context")[0]).toEqual(["run1"]);
    expect(wrapper.emitted("clear-tool-context")[0]).toEqual([]);
  });
});

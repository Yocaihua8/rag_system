import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import EvidenceDrawer from "./EvidenceDrawer.vue";

function mountDrawer(props = {}) {
  return mount(EvidenceDrawer, {
    props: {
      collapsed: true,
      answerResult: {
        answer: "回答正文",
        source_quality: { label: "来源充分" },
        sources: [{ path: "README.md", snippet: "项目入口" }],
        tool_context: { query: "默认入口", tool_run_id: "run1" },
      },
      toolSuggestion: { tool: "search_sources", arguments: { query: "RAG" }, reason: "来源不足" },
      lastUsableToolRun: { id: "run1", tool_name: "search_sources", status: "success", result: { query: "RAG" } },
      currentToolContextRunId: "run1",
      ...props,
    },
    slots: {
      advanced: "<section data-test-advanced>高级内容</section>",
    },
  });
}

describe("EvidenceDrawer", () => {
  it("starts collapsed and keeps evidence details out of the first screen", () => {
    const wrapper = mountDrawer();

    expect(wrapper.text()).toContain("依据");
    expect(wrapper.text()).not.toContain("README.md");
    expect(wrapper.text()).not.toContain("来源充分");
    expect(wrapper.text()).not.toContain("高级内容");
  });

  it("shows sources and tool context when expanded", () => {
    const wrapper = mountDrawer({ collapsed: false });

    expect(wrapper.text()).toContain("README.md");
    expect(wrapper.text()).toContain("来源充分");
    expect(wrapper.text()).toContain("来源不足");
    expect(wrapper.text()).toContain("高级内容");
  });

  it("emits drawer and tool context actions", async () => {
    const wrapper = mountDrawer({ collapsed: false });

    await wrapper.find('[data-evidence-action="toggle"]').trigger("click");
    await wrapper.find('[data-evidence-action="run-tool"]').trigger("click");
    await wrapper.find('[data-evidence-action="use-tool-run"]').trigger("click");
    await wrapper.find('[data-evidence-action="clear-tool-context"]').trigger("click");

    expect(wrapper.emitted("toggle")).toEqual([[]]);
    expect(wrapper.emitted("run-tool-suggestion")[0]).toEqual([
      { tool: "search_sources", arguments: { query: "RAG" }, reason: "来源不足" },
    ]);
    expect(wrapper.emitted("use-tool-result-context")[0]).toEqual(["run1"]);
    expect(wrapper.emitted("clear-tool-context")[0]).toEqual([]);
  });
});

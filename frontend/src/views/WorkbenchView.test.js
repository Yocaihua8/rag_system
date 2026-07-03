import { shallowMount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import WorkbenchView from "./WorkbenchView.vue";

function mountWorkbench(props = {}) {
  return shallowMount(WorkbenchView, {
    props: {
      statusMessage: "等待检查",
      selectedProjectId: "p1",
      evidenceCollapsed: true,
      answerResult: { answer: "回答正文", sources: [{ path: "README.md" }] },
      ...props,
    },
    global: {
      stubs: {
        AnswerPanel: true,
        ChatThread: true,
        EvidenceDrawer: true,
        FirstRunWizard: true,
        QuestionComposer: true,
      },
    },
  });
}

describe("WorkbenchView phase 2 shell", () => {
  it("keeps the chat first screen free of migration copy and advanced tool labels", () => {
    const wrapper = mountWorkbench();

    expect(wrapper.text()).toContain("问资料");
    expect(wrapper.text()).not.toContain("B-142");
    expect(wrapper.text()).not.toContain("检索调试");
    expect(wrapper.text()).not.toContain("Agent 工具");
    expect(wrapper.text()).not.toContain("项目问答");
  });

  it("moves sessions and evidence out of the main chat column", () => {
    const wrapper = mountWorkbench();

    expect(wrapper.findComponent({ name: "ChatSessionPanel" }).exists()).toBe(false);
    expect(wrapper.findComponent({ name: "EvidenceDrawer" }).exists()).toBe(true);
  });
});

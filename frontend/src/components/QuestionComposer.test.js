import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import QuestionComposer from "./QuestionComposer.vue";

function mountComposer(props = {}) {
  return mount(QuestionComposer, {
    props: {
      selectedProjectId: "",
      ...props,
    },
  });
}

describe("QuestionComposer", () => {
  it("blocks submit without a selected project and shows project selection status", () => {
    const wrapper = mountComposer();

    expect(wrapper.text()).toContain("未选择项目空间");
    expect(wrapper.find('button[type="submit"]').attributes("disabled")).toBeDefined();
  });

  it("emits question text, health check, and cancel actions from controls", async () => {
    const wrapper = mountComposer({ selectedProjectId: "p1", statusMessage: "等待提问" });

    await wrapper.find("textarea").setValue("默认入口是什么？");
    await wrapper.find(".section-title-row button").trigger("click");
    await wrapper.find("form").trigger("submit");

    expect(wrapper.emitted("check-health")[0]).toEqual([]);
    expect(wrapper.emitted("submit-question")[0]).toEqual(["默认入口是什么？"]);
  });

  it("emits cancel only while an answer is loading", async () => {
    const wrapper = mountComposer({ selectedProjectId: "p1", loading: true, statusMessage: "提问中" });

    await wrapper.find('[data-composer-action="cancel-answer"]').trigger("click");

    expect(wrapper.emitted("cancel-answer")[0]).toEqual([]);
    expect(wrapper.find("textarea").attributes("disabled")).toBeDefined();
  });

  it("shows chat tools, custom shortcuts, model, and answer depth controls", () => {
    const wrapper = mountComposer({ selectedProjectId: "p1", statusMessage: "等待提问" });

    expect(wrapper.find('[data-composer-action="add"]').exists()).toBe(true);
    expect(wrapper.find('[data-composer-action="shortcut"]').exists()).toBe(true);
    expect(wrapper.text()).toContain("上传临时文件");
    expect(wrapper.text()).toContain("加入资料");
    expect(wrapper.text()).toContain("练习与小测");
    expect(wrapper.text()).toContain("整理要点");
    expect(wrapper.text()).toContain("常用指令");
    expect(wrapper.text()).toContain("连接工具");
    expect(wrapper.text()).toContain("对比回答");
    expect(wrapper.text()).toContain("本机回答");
    expect(wrapper.text()).toContain("标准");
  });

  it("keeps technical terms out of the chat composer", () => {
    const wrapper = mountComposer({ selectedProjectId: "p1", statusMessage: "等待提问" });

    expect(wrapper.text()).not.toContain("API 接入");
    expect(wrapper.text()).not.toContain("LLM");
    expect(wrapper.text()).not.toContain("Prompt");
    expect(wrapper.text()).not.toContain("Profile");
    expect(wrapper.text()).not.toContain("Agent");
  });

  it("emits the lightweight practice tool from the add menu", async () => {
    const wrapper = mountComposer({ selectedProjectId: "p1", statusMessage: "等待提问" });
    const practiceButton = wrapper.findAll("button").find((button) => button.text() === "练习与小测");

    await practiceButton.trigger("click");

    expect(wrapper.emitted("start-assessment-tool")).toEqual([[]]);
  });

  it("shows cancel status and service error while preserving controls", () => {
    const wrapper = mountComposer({
      selectedProjectId: "p1",
      answerCancelStatus: "已取消本次提问",
      error: "本地服务暂时不可用",
    });

    expect(wrapper.text()).toContain("已取消本次提问");
    expect(wrapper.text()).toContain("本地服务暂时不可用");
  });
});

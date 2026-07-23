import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import WorkspaceSidebar from "./WorkspaceSidebar.vue";

function mountSidebar(props = {}) {
  return mount(WorkspaceSidebar, {
    props: {
      sidebarMode: "threads",
      selectedProjectId: "product",
      libraryTargetProjectId: "",
      projects: [
        { id: "product", name: "产品资料", document_count: 28 },
        { id: "notes", name: "学习笔记", document_count: 16 },
      ],
      chatSessions: [
        {
          id: "phase2",
          title: "第二阶段前端设计",
          project_id: "product",
          message_count: 6,
        },
      ],
      selectedChatSessionId: "phase2",
      ...props,
    },
  });
}

describe("WorkspaceSidebar", () => {
  it("keeps material as an action in the fixed coach navigation order", async () => {
    const wrapper = mountSidebar({ currentView: "coach" });
    const navigation = wrapper.find(".main-nav");

    expect(navigation.findAll("button").map((button) => button.attributes("data-view-key") || "library")).toEqual([
      "coach",
      "learning-map",
      "learning-plan",
      "library",
      "settings",
    ]);

    await navigation.find('[data-nav-action="library"]').trigger("click");

    expect(wrapper.emitted("open-library")).toEqual([[]]);
    expect(wrapper.emitted("change-view") || []).toEqual([]);
  });

  it("combines workspace and thread management in threads mode", async () => {
    const wrapper = mountSidebar();

    expect(wrapper.text()).toContain("产品资料");
    expect(wrapper.text()).toContain("加入资料");
    expect(wrapper.text()).toContain("线程");
    expect(wrapper.text()).toContain("搜索线程");

    await wrapper.find('[data-sidebar-action="open-library"]').trigger("click");
    await wrapper.find('[data-sidebar-action="create-chat-session"]').trigger("click");

    expect(wrapper.emitted("open-library")).toEqual([[]]);
    expect(wrapper.emitted("create-chat-session")).toEqual([[""]]);
  });

  it("switches to workspace selection mode for choosing material target", async () => {
    const wrapper = mountSidebar({ sidebarMode: "workspace-select" });

    expect(wrapper.text()).toContain("选择工作区");
    expect(wrapper.text()).toContain("产品资料");
    expect(wrapper.text()).not.toContain("搜索线程");

    await wrapper.findAll("[data-sidebar-workspace]")[1].trigger("click");

    expect(wrapper.emitted("select-library-target-project")).toEqual([["notes"]]);
    expect(wrapper.emitted("select-project") || []).toEqual([]);
  });
});

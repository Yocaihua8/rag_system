import { mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";

import AppShell from "./AppShell.vue";

function mountShell(props = {}) {
  return mount(AppShell, {
    props: {
      currentView: "chat",
      sidebarMode: "threads",
      selectedProjectId: "product",
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
          updated_at: "2026-07-02T10:00:00Z",
        },
      ],
      selectedChatSessionId: "phase2",
      ...props,
    },
    slots: {
      default: "<section>聊天内容</section>",
    },
  });
}

describe("AppShell phase 2 navigation", () => {
  it("shows simple primary entries and removes assessment from page navigation", () => {
    const wrapper = mountShell();

    expect(wrapper.text()).toContain("聊");
    expect(wrapper.text()).toContain("库");
    expect(wrapper.text()).toContain("设");
    expect(wrapper.text()).not.toContain("评估");
  });

  it("opens library as a modal action instead of changing the page", async () => {
    const wrapper = mountShell();
    const libraryButton = wrapper.find('[data-nav-action="library"]');

    expect(libraryButton.exists()).toBe(true);
    await libraryButton.trigger("click");

    expect(wrapper.emitted("open-library")).toEqual([[]]);
    expect(wrapper.emitted("change-view") || []).toEqual([]);
  });

  it("changes to settings through the settings entry", async () => {
    const wrapper = mountShell();

    await wrapper.find('[data-view-key="settings"]').trigger("click");

    expect(wrapper.emitted("change-view")).toEqual([["settings"]]);
  });

  it("changes the left sidebar to workspace selection while choosing material", () => {
    const wrapper = mountShell({ sidebarMode: "workspace-select" });

    expect(wrapper.text()).toContain("选择工作区");
    expect(wrapper.text()).toContain("产品资料");
    expect(wrapper.text()).not.toContain("搜索线程");
  });

  it("selects a library target workspace without selecting the chat workspace", async () => {
    const wrapper = mountShell({ sidebarMode: "workspace-select" });

    await wrapper.findAll("[data-sidebar-workspace]")[1].trigger("click");

    expect(wrapper.emitted("select-library-target-project")).toEqual([["notes"]]);
    expect(wrapper.emitted("select-project") || []).toEqual([]);
  });

  it("can collapse the sidebar and reopen it from the top bar", async () => {
    const wrapper = mountShell();

    await wrapper.find('[data-shell-action="collapse-sidebar"]').trigger("click");

    expect(wrapper.find("[data-workspace-sidebar]").exists()).toBe(false);
    expect(wrapper.find('[data-shell-action="open-sidebar"]').exists()).toBe(true);

    await wrapper.find('[data-shell-action="open-sidebar"]').trigger("click");

    expect(wrapper.find("[data-workspace-sidebar]").exists()).toBe(true);
  });

  it("starts with only the top bar menu on narrow screens", async () => {
    const originalMatchMedia = window.matchMedia;
    window.matchMedia = vi.fn().mockReturnValue({ matches: true });

    const wrapper = mountShell();

    expect(wrapper.find("[data-workspace-sidebar]").exists()).toBe(false);
    expect(wrapper.find('[data-shell-action="open-sidebar"]').exists()).toBe(true);

    window.matchMedia = originalMatchMedia;
  });
});

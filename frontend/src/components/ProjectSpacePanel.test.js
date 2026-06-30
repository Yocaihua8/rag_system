import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import ProjectSpacePanel from "./ProjectSpacePanel.vue";

function mountPanel(props = {}) {
  return mount(ProjectSpacePanel, {
    props: {
      projects: [],
      selectedProjectId: "",
      ...props,
    },
  });
}

describe("ProjectSpacePanel", () => {
  it("shows empty, load error, and missing-root project states", () => {
    expect(mountPanel().text()).toContain("未选择项目空间");
    expect(mountPanel({ loadError: "读取失败" }).text()).toContain("读取失败");
    expect(
      mountPanel({
        projects: [{ id: "p1", name: "知识岛", root: "E:/missing", root_exists: false }],
        selectedProjectId: "p1",
      }).text(),
    ).toContain("项目目录不存在");
  });

  it("emits project selection, creation, rename, and delete actions", async () => {
    const wrapper = mountPanel({
      projects: [{ id: "p1", name: "旧名称", root: "E:/Code/demo" }],
      selectedProjectId: "p1",
    });

    await wrapper.find("select").setValue("p1");
    await wrapper.find('input[name="project-name"]').setValue("新名称");
    await wrapper.find(".project-mutation-form").trigger("submit");
    await wrapper.find(".danger-link").trigger("click");
    await wrapper.find('input[name="name"]').setValue("新项目");
    await wrapper.find('input[name="path"]').setValue("E:/Code/new");
    await wrapper.find(".project-form").trigger("submit");

    expect(wrapper.emitted("select-project")[0]).toEqual(["p1"]);
    expect(wrapper.emitted("rename-project")[0]).toEqual(["新名称"]);
    expect(wrapper.emitted("delete-project")[0]).toEqual([]);
    expect(wrapper.emitted("create-project")[0]).toEqual([{ name: "新项目", path: "E:/Code/new" }]);
  });

  it("disables mutation controls while no project is selected or submission is active", () => {
    const wrapper = mountPanel({ formSubmitting: true, projectRenameSubmitting: true, projectDeleteSubmitting: true });

    expect(wrapper.find('input[name="project-name"]').attributes("disabled")).toBeDefined();
    expect(wrapper.find(".project-mutation-form button[type='submit']").attributes("disabled")).toBeDefined();
    expect(wrapper.find(".danger-link").attributes("disabled")).toBeDefined();
    expect(wrapper.find(".project-form button[type='submit']").attributes("disabled")).toBeDefined();
  });
});

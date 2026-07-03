import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import LibraryModal from "./LibraryModal.vue";

function mountModal(props = {}) {
  return mount(LibraryModal, {
    global: {
      stubs: {
        teleport: true,
      },
    },
    props: {
      open: true,
      step: "upload",
      documents: [],
      documentCollections: [],
      ...props,
    },
  });
}

describe("LibraryModal", () => {
  it("asks the app to switch the sidebar to workspace selection when choosing material", async () => {
    const wrapper = mountModal();

    await wrapper.find('[data-library-action="choose-material"]').trigger("click");

    expect(wrapper.emitted("choose-material")).toEqual([[]]);
  });

  it("keeps advanced sources behind the more sources card", async () => {
    const wrapper = mountModal();

    expect(wrapper.text()).toContain("文件");
    expect(wrapper.text()).toContain("文件夹");
    expect(wrapper.text()).toContain("笔记");
    expect(wrapper.text()).toContain("网页摘录");
    expect(wrapper.text()).toContain("更多来源");
    expect(wrapper.text()).not.toContain("GitHub 仓库");
    expect(wrapper.text()).not.toContain("Notion");
    expect(wrapper.text()).not.toContain("Obsidian");

    await wrapper.find('[data-library-source="more"]').trigger("click");

    expect(wrapper.text()).toContain("GitHub 仓库");
    expect(wrapper.text()).toContain("Notion");
    expect(wrapper.text()).toContain("Obsidian");
    expect(wrapper.text()).not.toContain("加入当前工作区资料");
    expect(wrapper.find('[data-library-advanced-sources]').exists()).toBe(true);
  });

  it("shows import results through a collapsed summary when nothing new happened", () => {
    const wrapper = mountModal();

    expect(wrapper.find('[data-import-result-list]').exists()).toBe(true);
    expect(wrapper.find('[data-import-result-details]').exists()).toBe(false);
    expect(wrapper.text()).toContain("本次结果");
  });

  it("expands import results when an import status is available", () => {
    const wrapper = mountModal({ importStatus: "文件上传导入完成：新增 3 份资料" });

    expect(wrapper.find('[data-import-result-details]').exists()).toBe(true);
    expect(wrapper.text()).toContain("文件上传导入完成：新增 3 份资料");
  });

  it("shows folders and existing documents in the selection step", async () => {
    const wrapper = mountModal({
      step: "select",
      selectedDocumentCollectionId: "c1",
      documentCollections: [{ id: "c1", name: "产品资料", document_count: 2 }],
      documents: [{ id: "d1", title: "接口说明", collection_name: "产品资料" }],
    });

    expect(wrapper.find('[data-library-folder-list]').exists()).toBe(true);
    expect(wrapper.text()).toContain("资料夹");
    expect(wrapper.text()).toContain("产品资料");
    expect(wrapper.text()).toContain("接口说明");

    await wrapper.findAll(".library-folder-item")[0].trigger("click");
    await wrapper.find(".library-document-item").trigger("click");

    expect(wrapper.emitted("select-collection")).toEqual([[""]]);
    expect(wrapper.emitted("select-document")).toEqual([["d1"]]);
  });
});

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

  it("shows the active Obsidian plugin connection and exposes connection actions", async () => {
    const wrapper = mountModal({
      obsidianConnections: [{
        id: "connection-1",
        status: "active",
        sync_status: "syncing",
        vault_name: "学习 Vault",
        output_root: "Knowledge Island/示例项目",
        last_synced_at: "2026-07-23T10:00:00+00:00",
      }],
    });

    await wrapper.find('[data-library-source="more"]').trigger("click");

    const obsidianCard = wrapper.find("[data-library-obsidian]");
    expect(obsidianCard.text()).toContain("已连接");
    expect(obsidianCard.text()).toContain("学习 Vault");
    expect(obsidianCard.text()).toContain("同步中");
    expect(obsidianCard.text()).toContain("Knowledge Island/示例项目");
    expect(obsidianCard.text()).not.toContain("token");

    const actionButtons = obsidianCard.findAll(".library-obsidian-actions button");
    await actionButtons[0].trigger("click");
    await actionButtons[1].trigger("click");

    expect(wrapper.emitted("refresh-obsidian-connections")).toEqual([[]]);
    expect(wrapper.emitted("open-obsidian-settings")).toEqual([[]]);
  });

  it("keeps the one-time read-only Vault import separate from plugin pairing", async () => {
    const wrapper = mountModal();

    await wrapper.find('[data-library-source="more"]').trigger("click");

    const obsidianCard = wrapper.find("[data-library-obsidian]");
    expect(obsidianCard.text()).toContain("未连接");
    expect(obsidianCard.text()).toContain("一次性只读导入");
    expect(obsidianCard.text()).toContain("不会建立插件连接");
    expect(obsidianCard.text()).toContain("不会向 Vault 写回");

    await obsidianCard.find('input[name="obsidian_vault_path"]').setValue("D:\\Notes\\My Vault");
    await obsidianCard.find(".library-obsidian-readonly-import").trigger("submit");

    expect(wrapper.emitted("import-obsidian-vault")).toEqual([
      [{ vaultPath: "D:\\Notes\\My Vault" }],
    ]);
  });

  it("shows Obsidian connection loading and error states", async () => {
    const loadingWrapper = mountModal({ obsidianConnectionsLoading: true });
    await loadingWrapper.find('[data-library-source="more"]').trigger("click");
    expect(loadingWrapper.text()).toContain("正在读取 Obsidian 连接");

    const errorWrapper = mountModal({ obsidianConnectionsError: "连接状态读取失败" });
    await errorWrapper.find('[data-library-source="more"]').trigger("click");
    expect(errorWrapper.text()).toContain("连接状态读取失败");
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

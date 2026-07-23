import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import ObsidianPublicationDialog from "./ObsidianPublicationDialog.vue";

function preview(status = "draft") {
  return {
    source_mode: "current",
    scope_notice: "只写入当前项目的 Knowledge Island/示例项目/ 目录。",
    publication: {
      id: "publication-1",
      revision: 3,
      status,
      artifacts: [{
        revision_id: "revision-1",
        artifact_type: "learning_plan",
        stable_id: "learning-plan-project-1",
        target_path: "Knowledge Island/示例项目/学习计划.md",
        content: "---\nknowledge_island_managed: true\n---\n# 学习计划\n\n完整正文",
        content_hash: "content-hash",
        expected_vault_hash: "vault-hash",
        status,
      }],
    },
  };
}

describe("ObsidianPublicationDialog", () => {
  it("shows target paths, full Markdown, hashes and scope before confirmation", async () => {
    const wrapper = mount(ObsidianPublicationDialog, {
      props: { open: true, preview: preview() },
    });

    expect(wrapper.text()).toContain("Knowledge Island/示例项目/学习计划.md");
    expect(wrapper.text()).toContain("knowledge_island_managed: true");
    expect(wrapper.text()).toContain("完整正文");
    expect(wrapper.text()).toContain("content-hash");
    expect(wrapper.text()).toContain("vault-hash");
    expect(wrapper.text()).toContain("只写入当前项目");

    await wrapper.find('[data-publication-action="confirm"]').trigger("click");
    expect(wrapper.emitted("confirm")[0][0]).toEqual({
      publicationId: "publication-1",
    });
  });

  it("describes queued as pending plugin execution instead of applied", () => {
    const wrapper = mount(ObsidianPublicationDialog, {
      props: { open: true, preview: preview("queued") },
    });

    expect(wrapper.find('[data-publication-action="confirm"]').exists()).toBe(false);
    expect(wrapper.find('[data-publication-notice="queued"]').text()).toContain("等待 Obsidian 桌面插件回报结果");
    expect(wrapper.find('[data-publication-notice="queued"]').text()).toContain("不代表文件已经写入");
    expect(wrapper.find('[data-publication-notice="applied"]').exists()).toBe(false);
  });

  it.each([
    ["conflict", "未覆盖 Vault 中的文件"],
    ["failed", "没有被标记为已应用"],
  ])("renders %s without offering another confirmation", (status, message) => {
    const wrapper = mount(ObsidianPublicationDialog, {
      props: { open: true, preview: preview(status) },
    });

    expect(wrapper.find(`[data-publication-notice="${status}"]`).text()).toContain(message);
    expect(wrapper.find('[data-publication-action="confirm"]').exists()).toBe(false);
  });

  it("closes from both explicit controls without mutating publication state", async () => {
    const wrapper = mount(ObsidianPublicationDialog, {
      props: { open: true, preview: preview() },
    });

    await wrapper.find('[data-publication-action="close"]').trigger("click");
    await wrapper.find('[data-publication-action="cancel"]').trigger("click");
    await wrapper.find('[data-publication-action="backdrop"]').trigger("click");

    expect(wrapper.emitted("close")).toEqual([[], [], []]);
    expect(wrapper.emitted("confirm")).toBeUndefined();
  });
});

import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import SettingsView from "./SettingsView.vue";

function mountSettings(props = {}) {
  return mount(SettingsView, {
    props: {
      settingsPage: "answer",
      selectedProjectId: "p1",
      llmSettings: { provider: "api", model: "deepseek-chat", has_api_key: true },
      modelProfiles: [{ id: "local", name: "本机快速", provider: "ollama", model: "qwen2.5:7b" }],
      promptPresets: [{ id: "default", name: "资料问答", description: "默认回答方式" }],
      promptPresetTemplates: [{ name: "资料问答", description: "只根据资料回答" }],
      ...props,
    },
  });
}

describe("SettingsView phase 2 layout", () => {
  it("uses a full-screen settings layout with a back button and page menu", async () => {
    const wrapper = mountSettings();

    expect(wrapper.classes()).toContain("settings-fullscreen");
    expect(wrapper.find('[data-settings-action="back"]').exists()).toBe(true);
    expect(wrapper.findAll("[data-settings-page]").map((button) => button.text())).toEqual([
      "回答",
      "资料",
      "Obsidian",
      "外观",
    ]);

    await wrapper.find('[data-settings-action="back"]').trigger("click");
    await wrapper.find('[data-settings-page="data"]').trigger("click");

    expect(wrapper.emitted("back")).toEqual([[]]);
    expect(wrapper.emitted("change-settings-page")).toEqual([["data"]]);
  });

  it("shows only answer settings first and hides technical connection fields", async () => {
    const wrapper = mountSettings();

    expect(wrapper.text()).toContain("本机回答");
    expect(wrapper.text()).toContain("本机快速");
    expect(wrapper.text()).toContain("在线回答");
    expect(wrapper.text()).toContain("连接详情");
    expect(wrapper.text()).not.toContain("Prompt");
    expect(wrapper.text()).not.toContain("Profile");
    expect(wrapper.text()).not.toContain("LLM");
    expect(wrapper.text()).not.toContain("API Key");

    await wrapper.find('[data-settings-action="connection-details"]').trigger("click");

    expect(wrapper.text()).toContain("服务地址");
    expect(wrapper.text()).toContain("模型名");
    expect(wrapper.text()).toContain("Key 引用");
  });

  it("shows one settings page at a time", () => {
    const dataPage = mountSettings({ settingsPage: "data" });
    expect(dataPage.text()).toContain("资料保存位置");
    expect(dataPage.text()).toContain("备份");
    expect(dataPage.text()).toContain("恢复");
    expect(dataPage.text()).not.toContain("本机回答");
    expect(dataPage.text()).not.toContain("系统提示词");

    const appearancePage = mountSettings({ settingsPage: "appearance" });
    expect(appearancePage.text()).toContain("深色模式");
    expect(appearancePage.text()).toContain("回答方式");
    expect(appearancePage.text()).not.toContain("服务地址");
    expect(appearancePage.text()).not.toContain("系统提示词");
  });

  it("shows Obsidian connection details and emits refresh and revoke payloads", async () => {
    const wrapper = mountSettings({
      settingsPage: "obsidian",
      obsidianConnections: [{
        id: "connection-1",
        status: "active",
        sync_status: "error",
        vault_name: "学习 Vault",
        output_root: "Knowledge Island/示例项目",
        last_synced_at: "2026-07-23T10:00:00+00:00",
        created_at: "2026-07-23T09:00:00+00:00",
        revoked_at: "",
      }],
    });

    expect(wrapper.text()).toContain("桌面插件连接");
    expect(wrapper.text()).toContain("学习 Vault");
    expect(wrapper.text()).toContain("同步异常");
    expect(wrapper.text()).toContain("Knowledge Island/示例项目");

    await wrapper.find('[data-obsidian-settings] > .section-title-row button').trigger("click");
    await wrapper.find(".danger-link").trigger("click");

    expect(wrapper.emitted("load-obsidian-connections")).toEqual([[]]);
    expect(wrapper.emitted("revoke-obsidian-connection")).toEqual([[
      { projectId: "p1", connectionId: "connection-1" },
    ]]);
  });

  it("starts pairing with an optional output root and only renders the temporary code", async () => {
    const wrapper = mountSettings({
      settingsPage: "obsidian",
      obsidianConnections: [],
      obsidianPairing: {
        code: "PAIR-ONCE",
        token: "must-never-render",
        output_root: "Knowledge Island/自定义",
        expires_at: "2026-07-23T10:05:00+00:00",
        ttl_seconds: 300,
      },
    });

    const pairingForm = wrapper.find("[data-obsidian-pairing-form]");
    await pairingForm.find('input[name="obsidian_output_root"]').setValue("Knowledge Island/自定义/");
    await pairingForm.trigger("submit");

    expect(wrapper.emitted("start-obsidian-pairing")).toEqual([[
      {
        projectId: "p1",
        outputRoot: "Knowledge Island/自定义/",
      },
    ]]);
    expect(wrapper.find("[data-obsidian-pairing-result]").text()).toContain("PAIR-ONCE");
    expect(wrapper.text()).toContain("300 秒");
    expect(wrapper.text()).not.toContain("must-never-render");
  });

  it("blocks a second pairing while an active connection exists and shows failures", async () => {
    const wrapper = mountSettings({
      settingsPage: "obsidian",
      obsidianConnections: [{
        id: "connection-1",
        status: "active",
        sync_status: "idle",
        vault_name: "学习 Vault",
      }],
      obsidianConnectionError: "连接列表读取失败",
      obsidianPairingError: "配对码创建失败",
    });

    expect(wrapper.text()).toContain("连接列表读取失败");
    expect(wrapper.text()).toContain("配对码创建失败");
    expect(wrapper.text()).toContain("撤销后才能生成新的配对码");
    expect(wrapper.find('[data-obsidian-pairing-form] button[type="submit"]').attributes("disabled")).toBeDefined();

    await wrapper.find("[data-obsidian-pairing-form]").trigger("submit");
    expect(wrapper.emitted("start-obsidian-pairing")).toBeUndefined();
  });

  it("keeps existing settings payloads behind connection details", async () => {
    const wrapper = mountSettings();

    await wrapper.find('[data-settings-action="connection-details"]').trigger("click");
    const forms = wrapper.findAll("form");

    await forms[0].find('input[name="api_base"]').setValue("https://api.example.com/v1");
    await forms[0].find('input[name="model"]').setValue("deepseek-chat");
    await forms[0].find('input[name="api_key"]').setValue("");
    await forms[0].trigger("submit");

    await forms[1].find('input[name="name"]').setValue("本机慢速");
    await forms[1].find('input[name="model"]').setValue("qwen2.5:14b");
    await forms[1].find('select[name="api_key_ref"]').setValue("env:RAG_LLM_API_KEY");
    await forms[1].trigger("submit");

    await forms[2].find('input[name="prompt_name"]').setValue("资料回答");
    await forms[2].find('textarea[name="system_prompt"]').setValue("只根据资料回答");
    await forms[2].find('textarea[name="answer_format"]').setValue("先结论");
    await forms[2].trigger("submit");

    expect(wrapper.emitted("save-llm-settings")[0][0]).toMatchObject({
      provider: "api",
      apiBase: "https://api.example.com/v1",
      model: "deepseek-chat",
      apiKey: "",
    });
    expect(wrapper.emitted("save-model-profile")[0][0]).toMatchObject({
      name: "本机慢速",
      model: "qwen2.5:14b",
      apiKeyRef: "env:RAG_LLM_API_KEY",
    });
    expect(wrapper.emitted("save-prompt-preset")[0][0]).toMatchObject({
      name: "资料回答",
      systemPrompt: "只根据资料回答",
      answerFormat: "先结论",
      projectId: "p1",
    });
  });
});

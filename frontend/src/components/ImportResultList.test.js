import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import ImportResultList from "./ImportResultList.vue";

describe("ImportResultList", () => {
  it("keeps empty import results collapsed by default", () => {
    const wrapper = mount(ImportResultList);

    expect(wrapper.find("[data-import-result-list]").exists()).toBe(true);
    expect(wrapper.find("[data-import-result-details]").exists()).toBe(false);
    expect(wrapper.text()).toContain("本次结果");
  });

  it("opens when a status is provided", () => {
    const wrapper = mount(ImportResultList, {
      props: {
        status: "文件夹导入完成：新增 12 份资料",
      },
    });

    expect(wrapper.find("[data-import-result-details]").exists()).toBe(true);
    expect(wrapper.text()).toContain("文件夹导入完成：新增 12 份资料");
  });

  it("can be expanded manually", async () => {
    const wrapper = mount(ImportResultList);

    await wrapper.find("[data-import-result-toggle]").trigger("click");

    expect(wrapper.find("[data-import-result-details]").exists()).toBe(true);
    expect(wrapper.text()).toContain("还没有新的加入结果");
  });

  it("opens when an error arrives after the list is rendered", async () => {
    const wrapper = mount(ImportResultList);

    await wrapper.setProps({ error: "资料导入失败" });

    expect(wrapper.find("[data-import-result-details]").exists()).toBe(true);
    expect(wrapper.text()).toContain("资料导入失败");
  });
});

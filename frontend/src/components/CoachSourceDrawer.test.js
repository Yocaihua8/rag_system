import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import CoachSourceDrawer from "./CoachSourceDrawer.vue";

describe("CoachSourceDrawer", () => {
  it("renders the real path, excerpt and locator for selected sources", () => {
    const wrapper = mount(CoachSourceDrawer, {
      props: {
        open: true,
        sourceIds: ["source-1"],
        sources: {
          "source-1": {
            id: "source-1",
            path: "backend/domain/project_analysis.py",
            excerpt: "def analyze_project(...):",
            locator: { line_start: 60, line_end: 90 },
          },
          "source-2": { id: "source-2", path: "README.md", excerpt: "不应显示" },
        },
      },
    });

    expect(wrapper.text()).toContain("backend/domain/project_analysis.py");
    expect(wrapper.text()).toContain("def analyze_project");
    expect(wrapper.text()).toContain("line_start");
    expect(wrapper.text()).toContain("60");
    expect(wrapper.text()).not.toContain("不应显示");
  });

  it("emits close from the close button and backdrop", async () => {
    const wrapper = mount(CoachSourceDrawer, { props: { open: true } });

    await wrapper.find('[data-coach-source-action="close"]').trigger("click");
    await wrapper.find('[data-coach-source-action="backdrop"]').trigger("click");

    expect(wrapper.emitted("close")).toEqual([[], []]);
  });
});

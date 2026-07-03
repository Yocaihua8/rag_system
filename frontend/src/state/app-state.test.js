import { describe, expect, it } from "vitest";

import { VIEW_KEYS, createInitialState } from "./app-state.js";

describe("app-state phase 2 shell state", () => {
  it("starts on chat and keeps library out of primary page navigation", () => {
    const state = createInitialState();

    expect(VIEW_KEYS).toEqual(["chat", "settings"]);
    expect(state).toMatchObject({
      currentView: "chat",
      libraryModalOpen: false,
      libraryStep: "upload",
      libraryTargetProjectId: "",
      sidebarMode: "threads",
      sidebarCollapsed: false,
      mobileSidebarOpen: false,
      evidenceCollapsed: true,
      settingsPage: "answer",
    });
  });
});

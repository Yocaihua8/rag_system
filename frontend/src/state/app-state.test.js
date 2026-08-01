import { describe, expect, it } from "vitest";

import { VIEW_KEYS, createInitialState } from "./app-state.js";

describe("app-state Knowledge Island 2.0 shell state", () => {
  it("starts on coach and keeps library and assessment out of primary page navigation", () => {
    const state = createInitialState();

    expect(VIEW_KEYS).toEqual(["coach", "learning-map", "learning-plan", "settings"]);
    expect(state).toMatchObject({
      currentView: "coach",
      libraryModalOpen: false,
      libraryStep: "upload",
      libraryTargetProjectId: "",
      sidebarMode: "threads",
      sidebarCollapsed: false,
      mobileSidebarOpen: false,
      evidenceCollapsed: true,
      settingsPage: "answer",
      coachOverview: null,
      coachKnowledgePoints: [],
      coachSkills: [],
      coachCoverage: null,
      coachAnalyzing: false,
      coachSourceDrawerOpen: false,
      coachAssessmentOverlayOpen: false,
      coachAssessmentTarget: null,
      coachAssessmentResult: null,
      coachAssessmentSubmitting: false,
      coachLearningOverlayOpen: false,
      coachLearningSession: null,
      coachLearningLoading: false,
      coachLearningSubmitting: false,
      learningPlan: null,
      learningPlanGenerating: false,
      learningPlanConfirming: false,
      obsidianConnections: [],
      obsidianRevokingId: "",
      obsidianPublicationPreview: null,
      obsidianPublicationDialogOpen: false,
    });
  });
});

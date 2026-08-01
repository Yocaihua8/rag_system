import { flushPromises, shallowMount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import App from "./App.vue";
import CoachLearningSessionOverlay from "./components/CoachLearningSessionOverlay.vue";
import { appState, createInitialState } from "./state/app-state.js";
import WorkbenchView from "./views/WorkbenchView.vue";

const API_BASE_URL = "http://127.0.0.1:8765";

function jsonResponse(data) {
  return new Response(JSON.stringify(data), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}

async function settleMountedWorkspace() {
  for (let index = 0; index < 8; index += 1) {
    await flushPromises();
  }
}

describe("App coach learning workspace integration", () => {
  beforeEach(() => {
    Object.assign(appState, createInitialState());
    localStorage.clear();
    globalThis.fetch = vi.fn().mockImplementation(async (path) => {
      if (path === `${API_BASE_URL}/api/projects`) {
        return jsonResponse({
          projects: [{ id: "project-1", name: "当前项目" }],
        });
      }
      if (String(path).startsWith(`${API_BASE_URL}/api/coach/learning-sessions/current?`)) {
        return jsonResponse({
          session: {
            id: "learning-1",
            project_id: "project-1",
            status: "awaiting_answer",
            version: 4,
            read_only: false,
            progress: { current: 1, completed: 0, total: 2 },
            current_step: { id: "step-1", title: "理解 Web 入口" },
            current_exercise: { id: "exercise-1", question_type: "concept" },
            attempts: [],
            allowed_actions: ["submit", "abandon"],
            sources: [],
          },
        });
      }
      return jsonResponse({});
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("loads an active session summary without opening the learning overlay", async () => {
    const wrapper = shallowMount(App, {
      global: {
        stubs: {
          AppShell: {
            template: "<main><slot /></main>",
          },
        },
      },
    });
    await settleMountedWorkspace();

    expect(fetch).toHaveBeenCalledWith(
      `${API_BASE_URL}/api/coach/learning-sessions/current?project_id=project-1`,
    );
    expect(appState.coachLearningSession?.id).toBe("learning-1");
    expect(appState.coachLearningOverlayOpen).toBe(false);
    expect(wrapper.findComponent(CoachLearningSessionOverlay).props("open")).toBe(false);
    expect(wrapper.findComponent(WorkbenchView).props("coachLearningSession")).toMatchObject({
      id: "learning-1",
      status: "awaiting_answer",
    });
  });
});

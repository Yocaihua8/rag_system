import { reactive } from "vue";

export const VIEW_KEYS = ["workbench", "library", "assessment", "settings"];

export function createInitialState() {
  return {
    currentView: "workbench",
    projects: [],
    selectedProjectId: "",
    projectsLoading: false,
    projectLoadError: "",
    projectFormSubmitting: false,
    projectFormError: "",
    importSubmitting: false,
    importError: "",
    importStatus: "",
    currentQuestion: "",
    answerResult: null,
    answerLoading: false,
    answerError: "",
    answerStatus: "等待提问",
    documents: [],
    documentsLoading: false,
    documentsLoadError: "",
    selectedDocumentId: "",
    selectedDocument: null,
    documentPreviewLoading: false,
    documentPreviewError: "",
    chatMessages: [],
    chatSessions: [],
    selectedChatSessionId: "",
    promptPresets: [],
    promptPresetTemplates: [],
    selectedPromptPresetId: "",
    editingPromptPresetId: "",
    documentCollections: [],
    selectedDocumentCollectionId: "",
    importBatches: [],
    selectedImportBatch: null,
    modelProfiles: [],
    defaultModelProfileId: "",
    editingModelProfileId: "",
    lastAnswerMessageId: "",
    agentTools: [],
    agentToolRuns: [],
    selectedAgentToolRun: null,
    documentFilter: "",
    assessmentSession: null,
    assessmentQuestion: null,
    currentToolSuggestion: null,
    currentToolContextRunId: "",
    currentAnswerAbortController: null,
    lastUsableToolRun: null,
    searchDebugResult: null,
    retrievalReviews: [],
    selectedRetrievalReview: null,
    projectSummary: null,
    retrievalSettings: null,
    assessmentQuestionIndex: 0,
    assessmentResults: [],
    assessmentMissedQuestions: [],
    assessmentAnsweredCurrent: false,
  };
}

export const appState = reactive(createInitialState());

export function showView(view) {
  if (!VIEW_KEYS.includes(view)) {
    return;
  }
  appState.currentView = view;
}

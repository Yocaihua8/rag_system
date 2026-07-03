from pathlib import Path


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_vue_api_client_normalizes_fetch_errors_like_legacy_frontend():
    client_js = _read("frontend/src/api/client.js")

    assert "SERVICE_UNAVAILABLE_MESSAGE" in client_js
    assert "本地服务暂时不可用" in client_js
    assert "apiGet(path)" in client_js
    assert "apiPost(path, payload, options = {})" in client_js
    assert "readJson(response)" in client_js
    assert "normalizeFetchError(error)" in client_js
    assert "throw normalizeFetchError(error)" in client_js
    assert "Content-Type" in client_js
    assert "application/json" in client_js


def test_vue_state_model_contains_migration_fields_and_view_switching():
    state_js = _read("frontend/src/state/app-state.js")

    assert 'currentView: "chat"' in state_js
    assert 'VIEW_KEYS = ["chat", "settings"]' in state_js
    for field_name in [
        "libraryModalOpen",
        "libraryStep",
        "libraryTargetProjectId",
        "sidebarMode",
        "settingsPage",
    ]:
        assert f"{field_name}:" in state_js

    for field_name in [
        "projects",
        "selectedProjectId",
        "documents",
        "chatMessages",
        "chatSessions",
        "promptPresets",
        "documentCollections",
        "modelProfiles",
        "agentTools",
        "assessmentSession",
        "searchDebugResult",
        "retrievalReviews",
        "projectSummary",
    ]:
        assert f"{field_name}:" in state_js

    assert "export const appState = reactive(createInitialState())" in state_js
    assert "export function showView(view)" in state_js
    assert "VIEW_KEYS.includes(view)" in state_js


def test_vue_layout_components_define_phase2_primary_entries():
    shell_vue = _read("frontend/src/components/AppShell.vue")
    sidebar_vue = _read("frontend/src/components/WorkspaceSidebar.vue")
    app_vue = _read("frontend/src/App.vue")

    for view in ["chat", "settings"]:
        assert f'data-view-key="{view}"' in sidebar_vue
    assert 'data-nav-action="library"' in sidebar_vue
    assert "WorkspaceSidebar" in shell_vue
    assert 'data-shell-action="open-sidebar"' in shell_vue
    assert 'data-shell-action="collapse-sidebar"' in sidebar_vue
    assert "sidebarCollapsed" in shell_vue
    assert "matchMedia" in shell_vue
    for label in ["聊", "库", "设", "选择工作区", "搜索线程"]:
        assert label in sidebar_vue
    for old_label in ["工作台", "资料库", "评估"]:
        assert old_label not in shell_vue
        assert old_label not in sidebar_vue

    for component_name in [
        "WorkbenchView",
        "SettingsView",
    ]:
        assert component_name in app_vue
    for removed_component_name in [
        "LibraryView",
        "AssessmentView",
    ]:
        assert removed_component_name not in app_vue

    assert "AppShell" in app_vue
    assert "LibraryModal" in app_vue
    assert "currentViewComponent" in app_vue
    assert "computed" in app_vue
    assert "B-142 Vue Workbench" not in shell_vue
    assert "流式问答、会话历史、消息管理" not in shell_vue
    assert "完整业务流程仍由 legacy 静态前端承载" not in shell_vue
    assert "SSE 和会话后续迁移" not in shell_vue


def test_vue_placeholder_views_keep_business_migration_boundary_explicit():
    assessment_vue = _read("frontend/src/views/AssessmentView.vue")
    assert "评估" in assessment_vue
    assert "B-141T 已迁移评估最小闭环" in assessment_vue

    settings_vue = _read("frontend/src/views/SettingsView.vue")
    assert "设置" in settings_vue
    assert "settings-fullscreen" in settings_vue
    assert "B-141S 已迁移模型设置、模型 Profile 和 Prompt 预设" not in settings_vue

    workbench_vue = _read("frontend/src/views/WorkbenchView.vue")
    assert "问资料" in workbench_vue
    assert "EvidenceDrawer" in workbench_vue
    assert "ChatSessionPanel" not in workbench_vue
    assert "B-142 已接入流式问答、取消、会话历史和消息管理" not in workbench_vue
    assert "Agent 工具" not in workbench_vue
    assert "SSE 和会话后续迁移" not in workbench_vue

    library_vue = _read("frontend/src/views/LibraryView.vue")
    assert "资料库" in library_vue
    assert "ProjectSpacePanel" in library_vue
    assert "B-141C" in library_vue
    assert "B-141C 至 B-141Q" in library_vue


def test_vue_assessment_api_helper_uses_existing_assessment_contracts():
    assessment_path = Path("frontend/src/api/assessment.js")
    assert assessment_path.exists(), "B-141T should add a Vue assessment API helper"
    assessment_js = _read(str(assessment_path))

    for marker in [
        'import { apiGet, apiPost } from "./client.js";',
        "export async function startAssessmentSession(projectId)",
        'throw new Error("请先创建或选择项目空间")',
        'apiPost("/api/assessment/start"',
        "project_id: projectId",
        "export async function submitAssessmentAnswer({ projectId, question, answer })",
        'throw new Error("请先开始评估")',
        'throw new Error("请输入评估回答")',
        'apiPost("/api/assessment/answer"',
        "question",
        "answer: cleanAnswer",
        "export async function loadAssessmentLibrary(projectId)",
        'apiGet(`/api/assessment/library?project_id=${encodeURIComponent(projectId)}`)',
        "return data.library || null",
    ]:
        assert marker in assessment_js


def test_vue_assessment_view_renders_assessment_flow_controls():
    assessment_vue = _read("frontend/src/views/AssessmentView.vue")

    for marker in [
        "掌握评估",
        "开始评估",
        "重新开始",
        "当前题目",
        "题型",
        "知识点",
        "来源",
        "提交回答",
        "下一题",
        "完成评估",
        "结果概览",
        "匹配要点",
        "缺失要点",
        "答题记录",
        "待复测列表",
        "assessmentAnswer",
        "currentQuestionNumber",
        "scorePercent",
        "statusClass",
        'defineEmits(["start-assessment", "submit-assessment-answer", "next-assessment-question", "reset-assessment"])',
    ]:
        assert marker in assessment_vue

    for prop_name in [
        "selectedProjectId",
        "assessmentSession",
        "assessmentQuestion",
        "assessmentQuestionIndex",
        "assessmentResults",
        "assessmentMissedQuestions",
        "assessmentAnsweredCurrent",
        "assessmentLoading",
        "assessmentSubmitting",
        "assessmentError",
        "assessmentStatus",
    ]:
        assert f"{prop_name}:" in assessment_vue


def test_vue_app_handles_assessment_flow_state_and_events():
    app_vue = _read("frontend/src/App.vue")
    state_js = _read("frontend/src/state/app-state.js")

    for imported_name in [
        "startAssessmentSession",
        "submitAssessmentAnswer",
    ]:
        assert imported_name in app_vue

    for marker in [
        ":assessment-session=\"appState.assessmentSession\"",
        ":assessment-question=\"appState.assessmentQuestion\"",
        ":assessment-question-index=\"appState.assessmentQuestionIndex\"",
        ":assessment-results=\"appState.assessmentResults\"",
        ":assessment-missed-questions=\"appState.assessmentMissedQuestions\"",
        ":assessment-answered-current=\"appState.assessmentAnsweredCurrent\"",
        ":assessment-loading=\"appState.assessmentLoading\"",
        ":assessment-submitting=\"appState.assessmentSubmitting\"",
        ":assessment-error=\"appState.assessmentError\"",
        ":assessment-status=\"appState.assessmentStatus\"",
        "@start-assessment=\"handleStartAssessment\"",
        "@submit-assessment-answer=\"handleSubmitAssessmentAnswer\"",
        "@next-assessment-question=\"handleNextAssessmentQuestion\"",
        "@reset-assessment=\"resetAssessmentState\"",
        "handleStartAssessment",
        "handleSubmitAssessmentAnswer",
        "handleNextAssessmentQuestion",
        "resetAssessmentState",
        "currentAssessmentQuestion",
        "hasNextAssessmentQuestion",
        "appState.assessmentStatus = \"评估题已生成\"",
        "appState.assessmentStatus = \"评估反馈已生成\"",
        "appState.assessmentStatus = \"本轮评估已完成\"",
    ]:
        assert marker in app_vue

    for state_field in [
        "assessmentLoading",
        "assessmentSubmitting",
        "assessmentError",
        "assessmentStatus",
    ]:
        assert f"{state_field}:" in state_js


def test_vue_project_api_helper_preserves_project_selection_contract():
    projects_js = _read("frontend/src/api/projects.js")

    assert 'PROJECT_SELECTION_STORAGE_KEY = "knowledge-island:selected-project-id"' in projects_js
    assert 'apiGet("/api/projects")' in projects_js
    assert 'apiPost("/api/projects", payload)' in projects_js
    assert "export async function loadProjects()" in projects_js
    assert "export async function createProject(payload)" in projects_js
    assert "export function selectProject(projectId)" in projects_js
    assert "export function restoreSelectedProjectId(projects)" in projects_js
    assert "localStorage.getItem(PROJECT_SELECTION_STORAGE_KEY)" in projects_js
    assert "localStorage.setItem(PROJECT_SELECTION_STORAGE_KEY, projectId)" in projects_js
    assert "localStorage.removeItem(PROJECT_SELECTION_STORAGE_KEY)" in projects_js
    assert "appState.projects" in projects_js
    assert "appState.selectedProjectId" in projects_js
    assert "export async function getProjectSummary(projectId)" in projects_js
    assert 'apiGet(`/api/projects/summary?project_id=${encodeURIComponent(projectId)}`)' in projects_js
    assert "return data.summary || null" in projects_js


def test_vue_knowledge_base_management_panel_renders_daily_management_overview():
    panel_path = Path("frontend/src/components/KnowledgeBaseManagementPanel.vue")
    assert panel_path.exists(), "B-42 should add KnowledgeBaseManagementPanel"
    panel_vue = _read(str(panel_path))
    library_vue = _read("frontend/src/views/LibraryView.vue")

    for marker in [
        "知识库辅助管理",
        "项目状态",
        "检索健康",
        "摄入进度",
        "文件列表",
        "评估题库",
        "最近结果",
        "请选择项目空间后查看知识库管理概览",
        "知识库为空",
        "暂无导入批次历史",
        "暂无评估题目",
        "projectSummary",
        "assessmentLibrary",
        "latestImportBatch",
        "retrievalHealthLabel",
        "questionTypeRows",
        "statusCountRows",
    ]:
        assert marker in panel_vue

    assert "KnowledgeBaseManagementPanel" in library_vue
    assert ":project-summary=\"projectSummary\"" in library_vue
    assert ":assessment-library=\"assessmentLibrary\"" in library_vue
    assert ":import-batches=\"importBatches\"" in library_vue
    assert ":documents=\"documents\"" in library_vue


def test_vue_app_loads_knowledge_base_management_overview_for_library_page():
    app_vue = _read("frontend/src/App.vue")
    state_js = _read("frontend/src/state/app-state.js")

    for imported_name in [
        "getProjectSummary",
        "loadAssessmentLibrary",
    ]:
        assert imported_name in app_vue

    for marker in [
        ":project-summary=\"appState.projectSummary\"",
        ":project-summary-loading=\"appState.projectSummaryLoading\"",
        ":project-summary-error=\"appState.projectSummaryError\"",
        ":assessment-library=\"appState.assessmentLibrary\"",
        ":assessment-library-loading=\"appState.assessmentLibraryLoading\"",
        ":assessment-library-error=\"appState.assessmentLibraryError\"",
        "loadKnowledgeBaseManagementOverview",
        "clearKnowledgeBaseManagementOverview",
        "await loadKnowledgeBaseManagementOverview()",
    ]:
        assert marker in app_vue

    for state_field in [
        "projectSummary",
        "projectSummaryLoading",
        "projectSummaryError",
        "assessmentLibrary",
        "assessmentLibraryLoading",
        "assessmentLibraryError",
    ]:
        assert f"{state_field}:" in state_js


def test_vue_project_space_panel_renders_project_selection_and_creation_form():
    panel_vue = _read("frontend/src/components/ProjectSpacePanel.vue")
    library_vue = _read("frontend/src/views/LibraryView.vue")

    for marker in [
        "当前项目",
        "项目空间",
        "未选择项目空间",
        "项目目录不存在",
        "新建项目空间",
        "项目名称",
        "本地目录",
        "创建项目空间",
    ]:
        assert marker in panel_vue

    assert 'v-for="project in projects"' in panel_vue
    assert ':value="project.id"' in panel_vue
    assert "@change=" in panel_vue
    assert '@submit.prevent="submitProject"' in panel_vue
    assert 'defineEmits(["refresh-projects", "select-project", "create-project", "rename-project", "delete-project"])' in panel_vue
    assert "ProjectSpacePanel" in library_vue


def test_vue_app_loads_project_spaces_on_startup_and_handles_panel_events():
    app_vue = _read("frontend/src/App.vue")
    state_js = _read("frontend/src/state/app-state.js")

    for imported_name in [
        "loadProjects",
        "createProject",
        "selectProject",
        "restoreSelectedProjectId",
    ]:
        assert imported_name in app_vue

    assert "onMounted" in app_vue
    assert "loadProjectSpaces" in app_vue
    assert "handleCreateProject" in app_vue
    assert "handleSelectProject" in app_vue
    assert "projectStatusMessage" in app_vue
    assert "projectFormStatus" in app_vue
    assert ":projects=\"appState.projects\"" in app_vue
    assert "@create-project=\"handleCreateProject\"" in app_vue

    for state_field in [
        "projectsLoading",
        "projectLoadError",
        "projectFormSubmitting",
        "projectFormError",
    ]:
        assert f"{state_field}:" in state_js


def test_vue_answer_api_helper_uses_existing_non_streaming_answer_contract():
    answer_js = _read("frontend/src/api/answer.js")

    assert "export async function askQuestion({ projectId, question, toolRunId = \"\", parentMessageId = \"\" })" in answer_js
    assert 'apiPost("/api/answer"' in answer_js
    assert "project_id: projectId" in answer_js
    assert "question" in answer_js
    assert "请先创建或选择项目空间" in answer_js
    assert "请输入问题" in answer_js
    assert "payload.tool_run_id = toolRunId" in answer_js
    assert "payload.parent_message_id = parentMessageId" in answer_js
    assert 'return apiPost("/api/answer", payload)' in answer_js


def test_vue_answer_api_helper_supports_streaming_answer_and_chat_contracts():
    answer_js = _read("frontend/src/api/answer.js")

    for marker in [
        "export function askQuestionStream({",
        "new EventSource(`/api/answer/stream?${params.toString()}`)",
        "source.addEventListener(\"token\"",
        "source.addEventListener(\"done\"",
        "source.addEventListener(\"answer_error\"",
        "source.onerror",
        "source.close()",
        "new DOMException(\"已取消本次提问\", \"AbortError\")",
        "handlers.onToken?.(answer, text)",
        "params.set(\"session_id\", sessionId)",
        "params.set(\"tool_run_id\", toolRunId)",
        "parentMessageId = \"\"",
        "params.set(\"parent_message_id\", parentMessageId)",
        "export async function listChatSessions(projectId)",
        "apiGet(`/api/chat/sessions?project_id=${encodeURIComponent(projectId)}`)",
        "export async function createChatSession({ projectId, title = \"\" })",
        'apiPost("/api/chat/sessions"',
        "export async function renameChatSession({ sessionId, title })",
        'apiPost("/api/chat/sessions/rename"',
        "export async function deleteChatSession(sessionId)",
        'apiPost("/api/chat/sessions/delete"',
        "export async function listChatMessages({ projectId, sessionId = \"\" })",
        "apiGet(`/api/chat/messages?${params.toString()}`)",
        "export async function deleteChatMessage(messageId)",
        'apiPost("/api/chat/messages/delete", { message_id: messageId })',
        "export async function clearChatMessages(projectId)",
        'apiPost("/api/chat/messages/clear", { project_id: projectId })',
    ]:
        assert marker in answer_js


def test_vue_answer_api_helper_uses_existing_feedback_contract():
    answer_js = _read("frontend/src/api/answer.js")

    for marker in [
        "export async function submitAnswerFeedback({ projectId, messageId, rating, note = \"\" })",
        'throw new Error("请先创建或选择项目空间")',
        'throw new Error("请先完成一次提问")',
        'throw new Error("请选择反馈类型")',
        'apiPost("/api/answer/feedback"',
        "project_id: projectId",
        "message_id: messageId",
        "rating",
        "note",
    ]:
        assert marker in answer_js


def test_vue_answer_api_helper_supports_multi_model_comparison_contract():
    answer_js = _read("frontend/src/api/answer.js")

    for marker in [
        "export async function compareAnswers({",
        "profileIds = []",
        'throw new Error("请选择 2 个模型 Profile")',
        'apiPost("/api/answer/compare"',
        "profile_ids: profileIds",
        "tool_run_id: toolRunId",
        "parent_message_id: parentMessageId",
    ]:
        assert marker in answer_js


def test_vue_workbench_wires_multi_model_comparison_state_and_panel():
    app_vue = _read("frontend/src/App.vue")
    state_js = _read("frontend/src/state/app-state.js")
    workbench_vue = _read("frontend/src/views/WorkbenchView.vue")
    panel_path = Path("frontend/src/components/ModelComparisonPanel.vue")
    assert panel_path.exists(), "B-135 should add a Vue comparison panel component"
    panel_vue = _read(str(panel_path))

    for state_field in [
        "modelComparisonResult",
        "modelComparisonLoading",
        "modelComparisonError",
        "modelComparisonStatus",
    ]:
        assert f"{state_field}:" in state_js

    for marker in [
        "compareAnswers",
        ":model-comparison-result=\"appState.modelComparisonResult\"",
        ":model-comparison-loading=\"appState.modelComparisonLoading\"",
        ":model-comparison-error=\"appState.modelComparisonError\"",
        ":model-comparison-status=\"appState.modelComparisonStatus\"",
        "@compare-answers=\"handleCompareAnswers\"",
        "async function handleCompareAnswers(payload)",
        "appState.modelComparisonResult = data",
        "appState.modelComparisonStatus = \"对比回答已生成\"",
    ]:
        assert marker in app_vue

    for marker in [
        "ModelComparisonPanel",
        ":model-profiles=\"modelProfiles\"",
        ":model-comparison-result=\"modelComparisonResult\"",
        "@compare-answers",
    ]:
        assert marker in workbench_vue

    for marker in [
        "模型并排对比",
        "选择 2 个模型 Profile",
        "开始对比",
        "result.profile_name",
        "result.answer",
        'defineEmits(["compare-answers"])',
    ]:
        assert marker in panel_vue


def test_vue_workbench_question_and_answer_panels_render_entrypoint():
    question_panel_vue = _read("frontend/src/components/QuestionPanel.vue")
    answer_panel_vue = _read("frontend/src/components/AnswerPanel.vue")
    workbench_vue = _read("frontend/src/views/WorkbenchView.vue")

    for marker in [
        "输入问题",
        "例如：这个项目的默认入口是什么？",
        "提问",
        "未选择项目空间",
        "defineEmits([\"submit-question\", \"check-health\"])",
    ]:
        assert marker in question_panel_vue

    for marker in [
        "回答",
        "提交问题后会在这里显示回答。",
        "answerResult.answer",
        "回答反馈",
    ]:
        assert marker in answer_panel_vue
    for marker in ["来源质量", "暂无来源", "mode", "provider"]:
        assert marker not in answer_panel_vue

    assert "QuestionComposer" in workbench_vue
    assert "AnswerPanel" in workbench_vue
    assert "@submit-question" in workbench_vue
    assert ":answer-result=\"answerResult\"" in workbench_vue


def test_vue_answer_panel_renders_answer_feedback_controls():
    answer_panel_vue = _read("frontend/src/components/AnswerPanel.vue")
    workbench_vue = _read("frontend/src/views/WorkbenchView.vue")

    for marker in [
        "回答反馈",
        "有用",
        "无用",
        "来源不准",
        "需要更多上下文",
        'data-feedback-rating="useful"',
        'data-feedback-rating="not_useful"',
        'data-feedback-rating="source_wrong"',
        'data-feedback-rating="need_more_context"',
        "submitAnswerFeedback",
        'defineEmits(["submit-answer-feedback", "run-tool-suggestion", "use-tool-result-context", "clear-tool-context"])',
        "lastAnswerMessageId",
        "answerFeedbackSubmitting",
        "answerFeedbackStatus",
        "answerFeedbackError",
    ]:
        assert marker in answer_panel_vue

    assert "@submit-answer-feedback" in workbench_vue
    assert ":last-answer-message-id=\"lastAnswerMessageId\"" in workbench_vue
    assert ":answer-feedback-submitting=\"answerFeedbackSubmitting\"" in workbench_vue
    assert ":answer-feedback-status=\"answerFeedbackStatus\"" in workbench_vue
    assert ":answer-feedback-error=\"answerFeedbackError\"" in workbench_vue


def test_vue_app_handles_non_streaming_workbench_question_state():
    app_vue = _read("frontend/src/App.vue")
    state_js = _read("frontend/src/state/app-state.js")

    assert "askQuestion" in app_vue
    assert "handleSubmitQuestion" in app_vue
    assert "@submit-question=\"handleSubmitQuestion\"" in app_vue
    assert ":answer-result=\"appState.answerResult\"" in app_vue
    assert ":answer-loading=\"appState.answerLoading\"" in app_vue
    assert ":answer-error=\"appState.answerError\"" in app_vue
    assert "appState.selectedProjectId" in app_vue
    assert "appState.answerResult = data" in app_vue

    for state_field in [
        "currentQuestion",
        "answerResult",
        "answerLoading",
        "answerError",
        "answerStatus",
    ]:
        assert f"{state_field}:" in state_js


def test_vue_app_wires_chat_sessions_messages_streaming_and_cancel_state():
    app_vue = _read("frontend/src/App.vue")
    state_js = _read("frontend/src/state/app-state.js")
    workbench_vue = _read("frontend/src/views/WorkbenchView.vue")

    for imported_name in [
        "askQuestionStream",
        "listChatSessions",
        "createChatSession",
        "renameChatSession",
        "deleteChatSession",
        "listChatMessages",
        "deleteChatMessage",
        "clearChatMessages",
    ]:
        assert imported_name in app_vue

    for marker in [
        ":chat-messages=\"appState.chatMessages\"",
        ":chat-sessions=\"appState.chatSessions\"",
        ":selected-chat-session-id=\"appState.selectedChatSessionId\"",
        ":chat-sessions-loading=\"appState.chatSessionsLoading\"",
        ":chat-messages-loading=\"appState.chatMessagesLoading\"",
        ":answer-streaming-text=\"appState.answerStreamingText\"",
        "@select-chat-session=\"handleSelectChatSession\"",
        "@create-chat-session=\"handleCreateChatSession\"",
        "@rename-chat-session=\"handleRenameChatSession\"",
        "@delete-chat-session=\"handleDeleteChatSession\"",
        "@delete-chat-message=\"handleDeleteChatMessage\"",
        "@clear-chat-messages=\"handleClearChatMessages\"",
        "@cancel-answer=\"handleCancelAnswer\"",
        "loadChatSessions",
        "loadChatMessages",
        "handleSelectChatSession",
        "handleCreateChatSession",
        "handleRenameChatSession",
        "handleDeleteChatSession",
        "handleDeleteChatMessage",
        "handleClearChatMessages",
        "handleCancelAnswer",
        "appState.currentAnswerAbortController?.abort()",
        "askQuestionStream({",
        "sessionId: appState.selectedChatSessionId",
        "handlers: {",
        "onToken(fullText)",
    ]:
        assert marker in app_vue

    for state_field in [
        "chatMessages",
        "chatSessions",
        "selectedChatSessionId",
        "chatMessagesLoading",
        "chatMessagesError",
        "chatSessionsLoading",
        "chatSessionsError",
        "chatSessionMutationError",
        "chatSessionMutationStatus",
        "answerStreamingText",
        "answerCancelStatus",
        "currentAnswerAbortController",
    ]:
        assert f"{state_field}:" in state_js

    for marker in [
        "chatMessages",
        "ChatThread",
        "QuestionComposer",
        "@cancel-answer",
    ]:
        assert marker in workbench_vue
    assert "ChatSessionPanel" not in workbench_vue


def test_vue_workbench_supports_editing_chat_message_and_resending_branch():
    answer_js = _read("frontend/src/api/answer.js")
    app_vue = _read("frontend/src/App.vue")
    chat_thread_vue = _read("frontend/src/components/ChatThread.vue")
    workbench_vue = _read("frontend/src/views/WorkbenchView.vue")

    for marker in [
        "parentMessageId",
        "parent_message_id",
    ]:
        assert marker in answer_js

    for marker in [
        "编辑重发",
        "edit-chat-message",
        "$emit('edit-chat-message', message)",
        "message.parent_message_id",
        "message.branch_index",
    ]:
        assert marker in chat_thread_vue

    for marker in [
        "@edit-chat-message=\"handleEditChatMessage\"",
        "handleEditChatMessage",
        "window.prompt(\"编辑问题后重发\"",
        "parentMessageId",
        "message?.id || message?.message_id",
    ]:
        assert marker in app_vue

    assert "@edit-chat-message=\"(message) => emit('edit-chat-message', message)\"" in workbench_vue


def test_vue_app_handles_answer_feedback_state_and_events():
    app_vue = _read("frontend/src/App.vue")
    state_js = _read("frontend/src/state/app-state.js")

    for marker in [
        "submitAnswerFeedback",
        "handleSubmitAnswerFeedback",
        "@submit-answer-feedback=\"handleSubmitAnswerFeedback\"",
        ":last-answer-message-id=\"appState.lastAnswerMessageId\"",
        ":answer-feedback-submitting=\"appState.answerFeedbackSubmitting\"",
        ":answer-feedback-status=\"appState.answerFeedbackStatus\"",
        ":answer-feedback-error=\"appState.answerFeedbackError\"",
        "appState.lastAnswerMessageId = data.message?.id || \"\"",
        "appState.answerFeedbackStatus = \"回答反馈已保存\"",
        "formatAnswerFeedbackRating",
        "clearAnswerFeedbackState",
    ]:
        assert marker in app_vue

    for state_field in [
        "lastAnswerMessageId",
        "answerFeedbackSubmitting",
        "answerFeedbackError",
        "answerFeedbackStatus",
    ]:
        assert f"{state_field}:" in state_js


def test_vue_answer_panel_renders_tool_suggestion_and_context_controls():
    answer_panel_vue = _read("frontend/src/components/AnswerPanel.vue")
    evidence_drawer_vue = _read("frontend/src/components/EvidenceDrawer.vue")
    workbench_vue = _read("frontend/src/views/WorkbenchView.vue")

    for marker in [
        "建议",
        "查更多来源",
        "用到下一问",
        "下一问将带入",
        "clear-tool-context",
        "toolSuggestion",
        "lastUsableToolRun",
        "currentToolContextRunId",
        "formatToolSuggestion",
        "formatUsableToolRun",
    ]:
        assert marker in evidence_drawer_vue
    assert "建议工具" not in answer_panel_vue
    assert "可用工具结果" not in answer_panel_vue

    for marker in [
        "EvidenceDrawer",
        ":tool-suggestion=\"currentToolSuggestion\"",
        ":last-usable-tool-run=\"lastUsableToolRun\"",
        ":current-tool-context-run-id=\"currentToolContextRunId\"",
        "@run-tool-suggestion",
        "@use-tool-result-context",
        "@clear-tool-context",
    ]:
        assert marker in workbench_vue


def test_vue_library_modal_keeps_advanced_sources_and_import_results_collapsed():
    library_modal_vue = _read("frontend/src/components/LibraryModal.vue")
    import_result_list_vue = _read("frontend/src/components/ImportResultList.vue")
    app_vue = _read("frontend/src/App.vue")

    for marker in [
        "ImportResultList",
        "data-library-source=\"more\"",
        "data-library-advanced-sources",
        "更多来源",
        "GitHub 仓库",
        "Notion",
        "Obsidian",
        ":status=\"importStatus\"",
        ":error=\"importError\"",
        "data-library-folder-list",
        "资料夹",
        "全部资料",
        "未分组",
        "v-for=\"collection in documentCollections\"",
        "emit('select-collection', collection.id)",
    ]:
        assert marker in library_modal_vue

    for marker in [
        ":selected-document-collection-id=\"appState.selectedDocumentCollectionId\"",
        ":document-collections-loading=\"appState.documentCollectionsLoading\"",
        ":document-collections-load-error=\"appState.documentCollectionsLoadError\"",
        "@refresh-collections=\"loadDocumentCollections\"",
        "@select-collection=\"handleSelectDocumentCollection\"",
        "await loadDocumentCollections()",
        "await loadLibraryDocuments()",
    ]:
        assert marker in app_vue

    for marker in [
        "data-import-result-list",
        "data-import-result-toggle",
        "data-import-result-details",
        "默认收起",
        "hasResult",
        "isOpen.value = true",
    ]:
        assert marker in import_result_list_vue

    assert "外部仓库" not in library_modal_vue
    assert "加入当前工作区资料" not in library_modal_vue
    assert "function handleSelectLibraryTargetProject" in app_vue
    select_target_function = app_vue.split("function handleSelectLibraryTargetProject", 1)[1].split("\n}", 1)[0]
    assert "appState.sidebarMode = \"workspace-select\"" in select_target_function
    assert "appState.sidebarMode = \"threads\"" not in select_target_function


def test_vue_app_handles_tool_suggestion_and_next_question_context_state():
    app_vue = _read("frontend/src/App.vue")
    state_js = _read("frontend/src/state/app-state.js")

    for marker in [
        ":current-tool-suggestion=\"appState.currentToolSuggestion\"",
        ":last-usable-tool-run=\"appState.lastUsableToolRun\"",
        ":current-tool-context-run-id=\"appState.currentToolContextRunId\"",
        "@run-tool-suggestion=\"handleRunToolSuggestion\"",
        "@use-tool-result-context=\"handleUseToolResultContext\"",
        "@clear-tool-context=\"clearToolContextState\"",
        "toolRunId: appState.currentToolContextRunId",
        "appState.currentToolSuggestion = data.tool_suggestion || null",
        "if (data.tool_context) {",
        "consumeToolContext()",
        "handleRunToolSuggestion",
        "handleUseToolResultContext",
        "setLastUsableToolRun",
        "clearToolSuggestionState",
        "clearToolContextState",
        "appState.currentToolContextRunId = runId",
        "appState.lastUsableToolRun = data.run",
    ]:
        assert marker in app_vue

    for state_field in [
        "currentToolSuggestion",
        "currentToolContextRunId",
        "lastUsableToolRun",
    ]:
        assert f"{state_field}:" in state_js


def test_vue_search_debug_api_helper_uses_existing_debug_contract():
    search_path = Path("frontend/src/api/search.js")
    assert search_path.exists(), "B-141V should add a Vue search debug API helper"
    search_js = _read(str(search_path))

    for marker in [
        'import { apiGet, apiPost } from "./client.js";',
        "export async function runSearchDebug({ projectId, query, topK = 5, minScore = 0, useKeyword = true, useVector = true })",
        'throw new Error("请先创建或选择项目空间")',
        'throw new Error("请输入检索诊断查询")',
        'apiPost("/api/search/debug"',
        "project_id: projectId",
        "query: trimmedQuery",
        "top_k: Number(topK)",
        "min_score: Number(minScore)",
        "use_keyword: Boolean(useKeyword)",
        "use_vector: Boolean(useVector)",
    ]:
        assert marker in search_js


def test_vue_search_debug_panel_renders_rag_diagnostics_controls():
    panel_path = Path("frontend/src/components/SearchDebugPanel.vue")
    assert panel_path.exists(), "B-141V should add SearchDebugPanel"
    panel_vue = _read(str(panel_path))
    workbench_vue = _read("frontend/src/views/WorkbenchView.vue")

    for marker in [
        "检索调试",
        "查看命中片段、分数和实际上下文",
        "诊断查询",
        "运行诊断",
        "Top K",
        "最低分",
        "关键词",
        "向量",
        "暂无检索诊断",
        "来源质量",
        "文档/分块",
        "向量可用",
        "命中片段",
        "searchDebugQuery",
        "searchDebugParameters",
        "formatScore",
        'defineEmits(["run-search-debug", "save-retrieval-settings", "save-retrieval-review", "select-retrieval-review", "delete-retrieval-review"])',
    ]:
        assert marker in panel_vue

    assert "SearchDebugPanel" in workbench_vue
    assert "@run-search-debug" in workbench_vue
    assert ":search-debug-result=\"searchDebugResult\"" in workbench_vue
    assert ":search-debug-loading=\"searchDebugLoading\"" in workbench_vue
    assert ":search-debug-error=\"searchDebugError\"" in workbench_vue
    assert ":search-debug-status=\"searchDebugStatus\"" in workbench_vue


def test_vue_project_api_helper_uses_existing_retrieval_settings_contract():
    projects_js = _read("frontend/src/api/projects.js")

    for marker in [
        "export async function getRetrievalSettings(projectId)",
        'apiGet(`/api/projects/retrieval-settings?project_id=${encodeURIComponent(projectId)}`)',
        "return data.settings || null",
        "export async function saveRetrievalSettings({ projectId, topK, minScore, useKeyword, useVector })",
        'throw new Error("请先创建或选择项目空间")',
        'apiPost("/api/projects/retrieval-settings"',
        "project_id: projectId",
        "top_k: Number(topK)",
        "min_score: Number(minScore)",
        "use_keyword: Boolean(useKeyword)",
        "use_vector: Boolean(useVector)",
        "return data.settings || null",
    ]:
        assert marker in projects_js


def test_vue_search_debug_panel_renders_retrieval_settings_defaults_and_save_control():
    panel_vue = _read("frontend/src/components/SearchDebugPanel.vue")
    workbench_vue = _read("frontend/src/views/WorkbenchView.vue")

    for marker in [
        "retrievalSettings",
        "retrievalSettingsLoading",
        "retrievalSettingsSaving",
        "retrievalSettingsStatus",
        "retrievalSettingsError",
        "applyRetrievalSettings",
        "watch(",
        "保存为默认",
        "默认值",
        "检索默认值",
        "saveRetrievalSettings",
        'defineEmits(["run-search-debug", "save-retrieval-settings", "save-retrieval-review", "select-retrieval-review", "delete-retrieval-review"])',
    ]:
        assert marker in panel_vue

    for marker in [
        ":retrieval-settings=\"retrievalSettings\"",
        ":retrieval-settings-loading=\"retrievalSettingsLoading\"",
        ":retrieval-settings-saving=\"retrievalSettingsSaving\"",
        ":retrieval-settings-status=\"retrievalSettingsStatus\"",
        ":retrieval-settings-error=\"retrievalSettingsError\"",
        "@save-retrieval-settings",
    ]:
        assert marker in workbench_vue


def test_vue_app_handles_search_debug_state_and_events():
    app_vue = _read("frontend/src/App.vue")
    state_js = _read("frontend/src/state/app-state.js")

    for marker in [
        "runSearchDebug",
        "handleRunSearchDebug",
        "@run-search-debug=\"handleRunSearchDebug\"",
        ":search-debug-result=\"appState.searchDebugResult\"",
        ":search-debug-loading=\"appState.searchDebugLoading\"",
        ":search-debug-error=\"appState.searchDebugError\"",
        ":search-debug-status=\"appState.searchDebugStatus\"",
        "appState.searchDebugResult = data",
        "appState.searchDebugStatus = `检索诊断完成：${data.hits?.length || 0} 条来源。`",
        "clearSearchDebugState",
    ]:
        assert marker in app_vue

    for state_field in [
        "searchDebugResult",
        "searchDebugLoading",
        "searchDebugError",
        "searchDebugStatus",
    ]:
        assert f"{state_field}:" in state_js


def test_vue_app_loads_and_saves_project_retrieval_settings():
    app_vue = _read("frontend/src/App.vue")
    state_js = _read("frontend/src/state/app-state.js")

    for marker in [
        "getRetrievalSettings",
        "saveRetrievalSettings",
        "loadRetrievalSettings",
        "handleSaveRetrievalSettings",
        "@save-retrieval-settings=\"handleSaveRetrievalSettings\"",
        ":retrieval-settings=\"appState.retrievalSettings\"",
        ":retrieval-settings-loading=\"appState.retrievalSettingsLoading\"",
        ":retrieval-settings-saving=\"appState.retrievalSettingsSaving\"",
        ":retrieval-settings-status=\"appState.retrievalSettingsStatus\"",
        ":retrieval-settings-error=\"appState.retrievalSettingsError\"",
        "appState.retrievalSettings = settings",
        "appState.retrievalSettingsStatus = \"检索默认值已保存\"",
        "await loadRetrievalSettings()",
        "clearRetrievalSettingsState",
    ]:
        assert marker in app_vue

    for state_field in [
        "retrievalSettings",
        "retrievalSettingsLoading",
        "retrievalSettingsSaving",
        "retrievalSettingsError",
        "retrievalSettingsStatus",
    ]:
        assert f"{state_field}:" in state_js


def test_vue_search_api_helper_uses_existing_retrieval_review_contracts():
    search_js = _read("frontend/src/api/search.js")

    for marker in [
        'import { apiGet, apiPost } from "./client.js";',
        "export async function saveRetrievalReview({ projectId, query, note = \"\", topK = 5, minScore = 0, useKeyword = true, useVector = true })",
        'throw new Error("请先创建或选择项目空间")',
        'throw new Error("请输入检索复盘查询")',
        'apiPost("/api/retrieval/reviews"',
        "project_id: projectId",
        "query: trimmedQuery",
        "note",
        "top_k: Number(topK)",
        "min_score: Number(minScore)",
        "use_keyword: Boolean(useKeyword)",
        "use_vector: Boolean(useVector)",
        "return data.review || null",
        "export async function listRetrievalReviews(projectId)",
        'apiGet(`/api/retrieval/reviews?project_id=${encodeURIComponent(projectId)}`)',
        "return data.reviews || []",
        "export async function getRetrievalReviewDetail(reviewId)",
        'throw new Error("请选择检索复盘记录")',
        'apiGet(`/api/retrieval/reviews/detail?review_id=${encodeURIComponent(reviewId)}`)',
        "export async function deleteRetrievalReview(reviewId)",
        'apiPost("/api/retrieval/reviews/delete"',
        "review_id: reviewId",
    ]:
        assert marker in search_js


def test_vue_search_debug_panel_renders_retrieval_review_controls_and_detail():
    panel_vue = _read("frontend/src/components/SearchDebugPanel.vue")
    workbench_vue = _read("frontend/src/views/WorkbenchView.vue")

    for marker in [
        "检索复盘",
        "复盘备注",
        "保存复盘",
        "复盘历史",
        "查看详情",
        "删除",
        "请选择一条检索复盘查看详情",
        "retrievalReviews",
        "retrievalReviewsLoading",
        "retrievalReviewsError",
        "retrievalReviewSaving",
        "retrievalReviewStatus",
        "selectedRetrievalReview",
        "retrievalReviewDetailLoading",
        "retrievalReviewDetailError",
        "deletingRetrievalReviewId",
        "retrievalReviewNote",
        "saveRetrievalReview",
        "selectRetrievalReview",
        "deleteRetrievalReview",
        "selectedReviewHits",
        'defineEmits(["run-search-debug", "save-retrieval-settings", "save-retrieval-review", "select-retrieval-review", "delete-retrieval-review"])',
    ]:
        assert marker in panel_vue

    for marker in [
        ":retrieval-reviews=\"retrievalReviews\"",
        ":retrieval-reviews-loading=\"retrievalReviewsLoading\"",
        ":retrieval-reviews-error=\"retrievalReviewsError\"",
        ":retrieval-review-saving=\"retrievalReviewSaving\"",
        ":retrieval-review-status=\"retrievalReviewStatus\"",
        ":selected-retrieval-review=\"selectedRetrievalReview\"",
        ":retrieval-review-detail-loading=\"retrievalReviewDetailLoading\"",
        ":retrieval-review-detail-error=\"retrievalReviewDetailError\"",
        ":deleting-retrieval-review-id=\"deletingRetrievalReviewId\"",
        "@save-retrieval-review",
        "@select-retrieval-review",
        "@delete-retrieval-review",
    ]:
        assert marker in workbench_vue


def test_vue_app_handles_retrieval_review_state_and_events():
    app_vue = _read("frontend/src/App.vue")
    state_js = _read("frontend/src/state/app-state.js")

    for marker in [
        "listRetrievalReviews",
        "saveRetrievalReview",
        "getRetrievalReviewDetail",
        "deleteRetrievalReview",
        "loadRetrievalReviews",
        "handleSaveRetrievalReview",
        "handleSelectRetrievalReview",
        "handleDeleteRetrievalReview",
        "clearRetrievalReviewState",
        "@save-retrieval-review=\"handleSaveRetrievalReview\"",
        "@select-retrieval-review=\"handleSelectRetrievalReview\"",
        "@delete-retrieval-review=\"handleDeleteRetrievalReview\"",
        ":retrieval-reviews=\"appState.retrievalReviews\"",
        ":retrieval-reviews-loading=\"appState.retrievalReviewsLoading\"",
        ":retrieval-reviews-error=\"appState.retrievalReviewsError\"",
        ":retrieval-review-saving=\"appState.retrievalReviewSaving\"",
        ":retrieval-review-status=\"appState.retrievalReviewStatus\"",
        ":selected-retrieval-review=\"appState.selectedRetrievalReview\"",
        ":retrieval-review-detail-loading=\"appState.retrievalReviewDetailLoading\"",
        ":retrieval-review-detail-error=\"appState.retrievalReviewDetailError\"",
        ":deleting-retrieval-review-id=\"appState.deletingRetrievalReviewId\"",
        "appState.retrievalReviewStatus = \"检索复盘已保存\"",
        "confirm(\"确认删除这条检索复盘吗？\")",
        "await loadRetrievalReviews()",
    ]:
        assert marker in app_vue

    for state_field in [
        "retrievalReviews",
        "retrievalReviewsLoading",
        "retrievalReviewsError",
        "retrievalReviewSaving",
        "retrievalReviewError",
        "retrievalReviewStatus",
        "selectedRetrievalReview",
        "retrievalReviewDetailLoading",
        "retrievalReviewDetailError",
        "deletingRetrievalReviewId",
    ]:
        assert f"{state_field}:" in state_js


def test_vue_agent_api_helper_uses_existing_readonly_tool_contracts():
    agent_path = Path("frontend/src/api/agent.js")
    assert agent_path.exists(), "B-141W should add a Vue Agent tools API helper"
    agent_js = _read(str(agent_path))

    for marker in [
        'import { apiGet, apiPost } from "./client.js";',
        "export async function listAgentTools()",
        'apiGet("/api/agent/tools")',
        "return data.tools || []",
        "export async function listAgentToolRuns(projectId)",
        'throw new Error("请先创建或选择项目空间")',
        'apiGet(`/api/agent/tools/runs?project_id=${encodeURIComponent(projectId)}`)',
        "return data.runs || []",
        "export async function getAgentToolRunDetail(runId)",
        'throw new Error("请选择工具运行记录")',
        'apiGet(`/api/agent/tools/runs/detail?run_id=${encodeURIComponent(runId)}`)',
        "return data.run || null",
        "export async function runAgentTool({ projectId, toolName, argumentsPayload = {} })",
        'throw new Error("请选择只读工具")',
        'apiPost("/api/agent/tools/run"',
        "project_id: projectId",
        "tool: toolName",
        "arguments: argumentsPayload",
    ]:
        assert marker in agent_js


def test_vue_agent_tools_panel_renders_readonly_tool_controls():
    panel_path = Path("frontend/src/components/AgentToolsPanel.vue")
    assert panel_path.exists(), "B-141W should add AgentToolsPanel"
    panel_vue = _read(str(panel_path))
    workbench_vue = _read("frontend/src/views/WorkbenchView.vue")

    for marker in [
        "Agent 工具",
        "当前只开放只读工具，并记录工具调用",
        "刷新工具",
        "项目概览",
        "检索来源",
        "工具参数：query",
        "运行",
        "工具结果",
        "暂无工具结果",
        "运行历史",
        "暂无工具运行历史",
        "查看详情",
        "工具运行详情",
        "请选择一条工具运行查看详情",
        "formatToolParameters",
        "formatToolResult",
        "formatToolRunDetail",
        "defineEmits([\"load-agent-tools\", \"run-agent-tool\", \"load-agent-tool-runs\", \"select-agent-tool-run\"])",
    ]:
        assert marker in panel_vue

    assert "AgentToolsPanel" in workbench_vue
    assert "@load-agent-tools" in workbench_vue
    assert "@run-agent-tool" in workbench_vue
    assert "@load-agent-tool-runs" in workbench_vue
    assert "@select-agent-tool-run" in workbench_vue
    assert ":agent-tools=\"agentTools\"" in workbench_vue
    assert ":agent-tool-runs=\"agentToolRuns\"" in workbench_vue
    assert ":selected-agent-tool-run=\"selectedAgentToolRun\"" in workbench_vue
    assert ":agent-tool-result=\"agentToolResult\"" in workbench_vue


def test_vue_app_handles_agent_tool_state_and_events():
    app_vue = _read("frontend/src/App.vue")
    state_js = _read("frontend/src/state/app-state.js")

    for imported_name in [
        "listAgentTools",
        "listAgentToolRuns",
        "getAgentToolRunDetail",
        "runAgentTool",
    ]:
        assert imported_name in app_vue

    for marker in [
        ":agent-tools=\"appState.agentTools\"",
        ":agent-tools-loading=\"appState.agentToolsLoading\"",
        ":agent-tools-error=\"appState.agentToolsError\"",
        ":agent-tool-runs=\"appState.agentToolRuns\"",
        ":agent-tool-runs-loading=\"appState.agentToolRunsLoading\"",
        ":agent-tool-runs-error=\"appState.agentToolRunsError\"",
        ":selected-agent-tool-run=\"appState.selectedAgentToolRun\"",
        ":agent-tool-result=\"appState.agentToolResult\"",
        ":agent-tool-status=\"appState.agentToolStatus\"",
        ":agent-tool-error=\"appState.agentToolError\"",
        ":agent-tool-submitting-name=\"appState.agentToolSubmittingName\"",
        "@load-agent-tools=\"loadAgentTools\"",
        "@run-agent-tool=\"handleRunAgentTool\"",
        "@load-agent-tool-runs=\"loadAgentToolRuns\"",
        "@select-agent-tool-run=\"handleSelectAgentToolRun\"",
        "loadAgentTools",
        "loadAgentToolRuns",
        "handleRunAgentTool",
        "handleSelectAgentToolRun",
        "clearAgentToolState",
        "appState.agentTools = tools",
        "appState.agentToolRuns = runs",
        "appState.agentToolResult = data",
        "appState.selectedAgentToolRun = run",
        "appState.agentToolStatus = \"工具运行完成\"",
        "await loadAgentToolRuns()",
    ]:
        assert marker in app_vue

    for state_field in [
        "agentToolsLoading",
        "agentToolsError",
        "agentToolRunsLoading",
        "agentToolRunsError",
        "agentToolSubmittingName",
        "agentToolResult",
        "agentToolStatus",
        "agentToolError",
        "agentToolDetailLoading",
        "agentToolDetailError",
    ]:
        assert f"{state_field}:" in state_js


def test_vue_document_api_helper_uses_existing_read_only_document_contract():
    documents_path = Path("frontend/src/api/documents.js")
    assert documents_path.exists(), "B-141E should add a Vue documents API helper"
    documents_js = _read(str(documents_path))

    assert "export async function listDocuments(projectId" in documents_js
    assert 'apiGet(`/api/documents?${params.toString()}`)' in documents_js
    assert "project_id" in documents_js
    assert "collection_id" in documents_js
    assert "data.documents || []" in documents_js
    assert "export async function getDocument(documentId)" in documents_js
    assert 'apiGet(`/api/document?document_id=${encodeURIComponent(documentId)}`)' in documents_js
    assert "data.document || null" in documents_js
    assert "请选择要预览的文档" in documents_js


def test_vue_document_api_helper_uses_existing_delete_contract():
    documents_js = _read("frontend/src/api/documents.js")

    assert 'import { apiGet, apiPost } from "./client.js";' in documents_js
    assert "export async function deleteDocument(documentId)" in documents_js
    assert 'throw new Error("请选择要删除的文档")' in documents_js
    assert 'apiPost("/api/documents/delete", { document_id: documentId })' in documents_js


def test_vue_library_document_panels_render_list_and_preview_states():
    list_path = Path("frontend/src/components/DocumentListPanel.vue")
    preview_path = Path("frontend/src/components/DocumentPreviewPanel.vue")
    assert list_path.exists(), "B-141E should add DocumentListPanel"
    assert preview_path.exists(), "B-141E should add DocumentPreviewPanel"

    list_panel_vue = _read(str(list_path))
    preview_panel_vue = _read(str(preview_path))
    library_vue = _read("frontend/src/views/LibraryView.vue")

    for marker in [
        "文档列表",
        "正在读取文档...",
        "暂无文档",
        "未选择项目空间",
        'v-for="document in documents"',
        '@click="$emit(\'select-document\', document.id)"',
        'defineEmits(["refresh-documents", "select-document", "add-document-to-collection", "remove-document-from-collection", "delete-document"])',
    ]:
        assert marker in list_panel_vue

    for marker in [
        "文档预览",
        "请选择文档查看正文",
        "正在读取正文...",
        "正文预览",
        "relative_path",
        "content",
    ]:
        assert marker in preview_panel_vue

    assert "DocumentListPanel" in library_vue
    assert "DocumentPreviewPanel" in library_vue
    assert "@refresh-documents" in library_vue
    assert "@select-document" in library_vue
    assert ":selected-document-id=\"selectedDocumentId\"" in library_vue


def test_vue_app_loads_library_documents_and_preview_state():
    app_vue = _read("frontend/src/App.vue")
    state_js = _read("frontend/src/state/app-state.js")

    for imported_name in [
        "listDocuments",
        "getDocument",
    ]:
        assert imported_name in app_vue

    assert "loadLibraryDocuments" in app_vue
    assert "handleSelectDocument" in app_vue
    assert "appState.selectedProjectId" in app_vue
    assert "appState.documents = documents" in app_vue
    assert "appState.selectedDocument = document" in app_vue
    assert "@refresh-documents=\"loadLibraryDocuments\"" in app_vue
    assert "@select-document=\"handleSelectDocument\"" in app_vue
    assert ":documents=\"appState.documents\"" in app_vue
    assert ":selected-document=\"appState.selectedDocument\"" in app_vue
    assert ":documents-loading=\"appState.documentsLoading\"" in app_vue
    assert ":document-preview-loading=\"appState.documentPreviewLoading\"" in app_vue

    for state_field in [
        "documentsLoading",
        "documentsLoadError",
        "selectedDocumentId",
        "selectedDocument",
        "documentPreviewLoading",
        "documentPreviewError",
    ]:
        assert f"{state_field}:" in state_js


def test_vue_import_api_helper_uses_existing_note_and_url_contracts():
    imports_path = Path("frontend/src/api/imports.js")
    assert imports_path.exists(), "B-141F should add a Vue imports API helper"
    imports_js = _read(str(imports_path))

    assert "export async function importPlainTextNote({ projectId, title, content })" in imports_js
    assert 'apiPost("/api/import/note"' in imports_js
    assert "project_id: projectId" in imports_js
    assert "title" in imports_js
    assert "content" in imports_js
    assert "请先创建或选择项目空间" in imports_js
    assert "请输入笔记标题" in imports_js
    assert "请输入笔记正文" in imports_js
    assert "export async function importUrlExcerpt({ projectId, url, title, content })" in imports_js
    assert 'apiPost("/api/import/url"' in imports_js
    assert "url" in imports_js
    assert "请输入 URL" in imports_js
    assert "请输入网页标题" in imports_js
    assert "请输入网页正文或摘要" in imports_js


def test_vue_document_import_panel_renders_note_and_url_forms():
    panel_path = Path("frontend/src/components/DocumentImportPanel.vue")
    assert panel_path.exists(), "B-141F should add DocumentImportPanel"

    panel_vue = _read(str(panel_path))
    library_vue = _read("frontend/src/views/LibraryView.vue")

    for marker in [
        "导入资料",
        "文本笔记",
        "导入文本笔记",
        "笔记标题",
        "笔记正文",
        "URL 摘录",
        "保存网页来源",
        "网页地址",
        "网页标题",
        "网页正文或摘要",
        "导入 URL 摘录",
        "未选择项目空间",
        "import-folder",
    ]:
        assert marker in panel_vue

    assert "@submit.prevent=\"submitNote\"" in panel_vue
    assert "@submit.prevent=\"submitUrl\"" in panel_vue
    assert "DocumentImportPanel" in library_vue
    assert "@import-note" in library_vue
    assert "@import-url" in library_vue
    assert ":import-submitting=\"importSubmitting\"" in library_vue
    assert ":import-status=\"importStatus\"" in library_vue


def test_vue_app_handles_library_note_and_url_import_state():
    app_vue = _read("frontend/src/App.vue")
    state_js = _read("frontend/src/state/app-state.js")

    for imported_name in [
        "importPlainTextNote",
        "importUrlExcerpt",
    ]:
        assert imported_name in app_vue

    assert "handleImportNote" in app_vue
    assert "handleImportUrl" in app_vue
    assert "@import-note=\"handleImportNote\"" in app_vue
    assert "@import-url=\"handleImportUrl\"" in app_vue
    assert ":import-submitting=\"appState.importSubmitting\"" in app_vue
    assert ":import-error=\"appState.importError\"" in app_vue
    assert ":import-status=\"appState.importStatus\"" in app_vue
    assert "appState.selectedProjectId" in app_vue
    assert "await loadLibraryDocuments()" in app_vue
    assert "文本笔记已导入" in app_vue
    assert "URL 摘录已导入" in app_vue

    for state_field in [
        "importSubmitting",
        "importError",
        "importStatus",
    ]:
        assert f"{state_field}:" in state_js


def test_vue_import_api_helper_uses_existing_import_batch_contracts():
    imports_js = _read("frontend/src/api/imports.js")

    assert "apiGet" in imports_js
    assert "export async function listImportBatches(projectId)" in imports_js
    assert 'apiGet(`/api/import/batches?${params.toString()}`)' in imports_js
    assert "project_id" in imports_js
    assert "data.batches || []" in imports_js
    assert "export async function getImportBatchDetail(batchId)" in imports_js
    assert 'apiGet(`/api/import/batches/detail?batch_id=${encodeURIComponent(batchId)}`)' in imports_js
    assert "请选择导入批次" in imports_js


def test_vue_import_batch_history_panel_renders_read_only_batch_states():
    panel_path = Path("frontend/src/components/ImportBatchHistoryPanel.vue")
    assert panel_path.exists(), "B-141G should add ImportBatchHistoryPanel"

    panel_vue = _read(str(panel_path))
    library_vue = _read("frontend/src/views/LibraryView.vue")

    for marker in [
        "导入批次历史",
        "正在读取导入批次...",
        "暂无导入批次历史",
        "未选择项目空间",
        "查看详情",
        "批次详情",
        "请选择一条导入批次查看详情",
        "跳过 / 错误明细",
        "本批次没有跳过或错误明细",
        'defineEmits(["refresh-batches", "select-batch"])',
    ]:
        assert marker in panel_vue

    for forbidden_action in ["回滚", "删除批次", "重试"]:
        assert forbidden_action not in panel_vue

    assert "formatImportSourceType" in panel_vue
    assert "formatImportBatchStatus" in panel_vue
    assert "formatImportBatchItemKind" in panel_vue
    assert "ImportBatchHistoryPanel" in library_vue
    assert "@refresh-batches" in library_vue
    assert "@select-batch" in library_vue
    assert ":import-batches=\"importBatches\"" in library_vue
    assert ":selected-import-batch=\"selectedImportBatch\"" in library_vue


def test_vue_app_loads_import_batches_and_refreshes_after_imports():
    app_vue = _read("frontend/src/App.vue")
    state_js = _read("frontend/src/state/app-state.js")

    for imported_name in [
        "listImportBatches",
        "getImportBatchDetail",
    ]:
        assert imported_name in app_vue

    assert "loadImportBatches" in app_vue
    assert "handleSelectImportBatch" in app_vue
    assert "appState.importBatches = batches" in app_vue
    assert "appState.selectedImportBatch = data.batch" in app_vue
    assert "appState.selectedImportBatchItems = data.items || []" in app_vue
    assert "@refresh-batches=\"loadImportBatches\"" in app_vue
    assert "@select-batch=\"handleSelectImportBatch\"" in app_vue
    assert ":import-batches=\"appState.importBatches\"" in app_vue
    assert ":import-batches-loading=\"appState.importBatchesLoading\"" in app_vue
    assert ":import-batch-detail-loading=\"appState.importBatchDetailLoading\"" in app_vue
    assert "await loadImportBatches()" in app_vue

    for state_field in [
        "importBatches",
        "importBatchesLoading",
        "importBatchesLoadError",
        "selectedImportBatch",
        "selectedImportBatchItems",
        "importBatchDetailLoading",
        "importBatchDetailError",
    ]:
        assert f"{state_field}:" in state_js


def test_vue_import_api_helper_uses_existing_file_upload_contract():
    imports_js = _read("frontend/src/api/imports.js")

    assert "export async function importBrowserFiles({ projectId, files })" in imports_js
    assert 'throw new Error("请选择一个或多个本地文件")' in imports_js
    assert 'source_type: "file_upload"' in imports_js
    assert "payload.project_id = projectId" in imports_js
    assert 'payload.project_name = "browser-upload"' in imports_js
    assert 'apiPost("/api/import/upload", payload)' in imports_js
    assert "relative_path: file.name" in imports_js
    assert "content_base64" in imports_js
    assert "size: file.size" in imports_js
    assert "await file.text()" in imports_js
    assert "await file.arrayBuffer()" in imports_js
    assert "btoa(binary)" in imports_js
    assert 'new Set([".docx", ".pdf"])' in imports_js


def test_vue_import_api_helper_uses_notion_and_obsidian_contracts():
    imports_js = _read("frontend/src/api/imports.js")

    for marker in [
        "export async function importNotionZip({ projectId, file })",
        'throw new Error("请选择 Notion 导出的 zip 文件")',
        'apiPost("/api/import/notion-zip"',
        "project_id: projectId",
        "filename: file.name",
        "content_base64",
        "export async function importObsidianVault({ projectId, vaultPath })",
        'throw new Error("请输入 Obsidian vault 本机目录")',
        'apiPost("/api/import/obsidian-vault"',
        "vault_path: cleanVaultPath",
    ]:
        assert marker in imports_js


def test_vue_import_api_helper_uses_github_repo_contract():
    imports_js = _read("frontend/src/api/imports.js")

    for marker in [
        "export async function importGithubRepo({ repoUrl, branch = \"\", projectName = \"\" })",
        'throw new Error("请输入 GitHub 仓库地址")',
        'apiPost("/api/import/github-repo"',
        "repo_url: cleanRepoUrl",
        "branch: cleanBranch",
        "project_name: cleanProjectName",
    ]:
        assert marker in imports_js


def test_vue_document_import_panel_renders_notion_and_obsidian_import_controls():
    panel_vue = _read("frontend/src/components/DocumentImportPanel.vue")
    library_vue = _read("frontend/src/views/LibraryView.vue")

    for marker in [
        "Notion 导出",
        "导入 Notion zip",
        'ref="notionZipInput"',
        '@change="submitNotionZip"',
        "Obsidian vault",
        "Vault 本机路径",
        "导入 Obsidian vault",
        "obsidianVaultPath",
        "submitObsidianVault",
        "import-notion-zip",
        "import-obsidian-vault",
    ]:
        assert marker in panel_vue

    assert "@import-notion-zip" in library_vue
    assert "@import-obsidian-vault" in library_vue


def test_vue_document_import_panel_renders_github_repo_import_controls():
    panel_vue = _read("frontend/src/components/DocumentImportPanel.vue")
    library_vue = _read("frontend/src/views/LibraryView.vue")

    for marker in [
        "GitHub 仓库",
        "导入 GitHub 仓库",
        "仓库地址",
        "分支名",
        "项目名称",
        "githubRepoForm",
        "repoUrl",
        "branch",
        "projectName",
        "submitGithubRepo",
        "import-github-repo",
    ]:
        assert marker in panel_vue

    assert '@submit.prevent="submitGithubRepo"' in panel_vue
    assert "@import-github-repo" in library_vue


def test_vue_app_handles_notion_and_obsidian_import_response_and_refreshes_library():
    app_vue = _read("frontend/src/App.vue")

    for imported_name in [
        "importNotionZip",
        "importObsidianVault",
    ]:
        assert imported_name in app_vue

    for marker in [
        "@import-notion-zip=\"handleImportNotionZip\"",
        "@import-obsidian-vault=\"handleImportObsidianVault\"",
        "handleImportNotionZip",
        "handleImportObsidianVault",
        "importNotionZip({",
        "importObsidianVault({",
        "Notion 导出导入完成",
        "Obsidian vault 导入完成",
        "await loadLibraryDocuments()",
        "await loadImportBatches()",
    ]:
        assert marker in app_vue


def test_vue_app_handles_github_repo_import_response_and_refreshes_library():
    app_vue = _read("frontend/src/App.vue")

    for marker in [
        "importGithubRepo",
        "@import-github-repo=\"handleImportGithubRepo\"",
        "handleImportGithubRepo",
        "importGithubRepo({",
        "repoUrl: payload.repoUrl",
        "branch: payload.branch",
        "projectName: payload.projectName",
        "selectProject(data.project.id)",
        "appState.documents = data.documents || []",
        "GitHub 仓库导入完成",
        "await loadProjectSpaces()",
        "await loadImportBatches()",
    ]:
        assert marker in app_vue


def test_vue_document_import_panel_renders_file_upload_without_directory_picker():
    panel_vue = _read("frontend/src/components/DocumentImportPanel.vue")
    library_vue = _read("frontend/src/views/LibraryView.vue")

    for marker in [
        "文件上传",
        "选择文件上传导入",
        'type="file"',
        "multiple",
        'ref="fileInput"',
        '@change="submitFiles"',
    ]:
        assert marker in panel_vue

    file_input_block = panel_vue.split('ref="fileInput"', 1)[1].split("/>", 1)[0]
    assert "webkitdirectory" not in file_input_block
    assert "@import-files" in library_vue


def test_vue_app_handles_browser_file_upload_response_and_refreshes_library():
    app_vue = _read("frontend/src/App.vue")

    assert "importBrowserFiles" in app_vue
    assert "handleImportFiles" in app_vue
    assert "@import-files=\"handleImportFiles\"" in app_vue
    assert "importBrowserFiles({" in app_vue
    assert "projectId: appState.selectedProjectId" in app_vue
    assert "files" in app_vue
    assert "selectProject(data.project.id)" in app_vue
    assert "appState.documents = data.documents || []" in app_vue
    assert "文件上传导入完成" in app_vue
    assert "await loadProjectSpaces()" in app_vue
    assert "await loadImportBatches()" in app_vue


def test_vue_import_api_helper_uses_existing_browser_folder_upload_contract():
    imports_js = _read("frontend/src/api/imports.js")

    assert "export async function importBrowserFolder({ files })" in imports_js
    assert 'throw new Error("请选择一个本地项目文件夹")' in imports_js
    assert 'source_type: "browser_folder_upload"' in imports_js
    assert "payload.project_name = projectName" in imports_js
    assert "file.webkitRelativePath || file.name" in imports_js
    assert 'rawPath.replace(/\\\\/g, "/")' in imports_js
    assert "parts.slice(1).join" in imports_js
    assert "relative_path: entry.relativePath" in imports_js
    assert 'apiPost("/api/import/upload", payload)' in imports_js


def test_vue_document_import_panel_renders_browser_folder_picker_separately_from_file_upload():
    panel_vue = _read("frontend/src/components/DocumentImportPanel.vue")
    library_vue = _read("frontend/src/views/LibraryView.vue")

    for marker in [
        "浏览器文件夹",
        "选择本机文件夹导入",
        'ref="folderInput"',
        "webkitdirectory",
        '@change="submitFolder"',
        "import-folder",
    ]:
        assert marker in panel_vue

    file_input_block = panel_vue.split('ref="fileInput"', 1)[1].split("/>", 1)[0]
    assert "webkitdirectory" not in file_input_block
    folder_input_block = panel_vue.split('ref="folderInput"', 1)[1].split("/>", 1)[0]
    assert "webkitdirectory" in folder_input_block
    assert "multiple" in folder_input_block
    assert "@import-folder" in library_vue


def test_vue_app_handles_browser_folder_upload_response_and_refreshes_library():
    app_vue = _read("frontend/src/App.vue")

    assert "importBrowserFolder" in app_vue
    assert "handleImportFolder" in app_vue
    assert "@import-folder=\"handleImportFolder\"" in app_vue
    assert "importBrowserFolder({" in app_vue
    assert "files" in app_vue
    assert "selectProject(data.project.id)" in app_vue
    assert "appState.documents = data.documents || []" in app_vue
    assert "浏览器文件夹导入完成" in app_vue
    assert "await loadProjectSpaces()" in app_vue
    assert "await loadImportBatches()" in app_vue


def test_vue_import_api_helper_uses_existing_directory_sync_contract():
    imports_js = _read("frontend/src/api/imports.js")

    assert "export async function syncProjectDirectory({ projectId })" in imports_js
    assert 'throw new Error("请先创建或选择项目空间")' in imports_js
    assert 'apiPost("/api/import", {' in imports_js
    assert "project_id: projectId" in imports_js


def test_vue_document_import_panel_renders_directory_sync_button_for_selected_project():
    panel_vue = _read("frontend/src/components/DocumentImportPanel.vue")
    library_vue = _read("frontend/src/views/LibraryView.vue")

    for marker in [
        "同步当前项目目录",
        "sync-directory",
        ":disabled=\"importSubmitting || !selectedProjectId\"",
        "sync-directory",
    ]:
        assert marker in panel_vue

    assert "@sync-directory" in library_vue


def test_vue_app_handles_directory_sync_response_and_refreshes_library():
    app_vue = _read("frontend/src/App.vue")

    assert "syncProjectDirectory" in app_vue
    assert "handleSyncDirectory" in app_vue
    assert "@sync-directory=\"handleSyncDirectory\"" in app_vue
    assert "syncProjectDirectory({" in app_vue
    assert "projectId: appState.selectedProjectId" in app_vue
    assert "appState.documents = data.documents || []" in app_vue
    assert "同步当前项目目录完成" in app_vue
    assert "await loadLibraryDocuments()" in app_vue
    assert "await loadImportBatches()" in app_vue


def test_vue_import_api_helper_uses_existing_import_preview_contract():
    imports_js = _read("frontend/src/api/imports.js")

    assert "export async function previewProjectImport({ projectId })" in imports_js
    assert 'throw new Error("请先创建或选择项目空间")' in imports_js
    assert "new URLSearchParams({ project_id: projectId })" in imports_js
    assert 'apiGet(`/api/import/preview?${params.toString()}`)' in imports_js
    assert "return data.preview || null" in imports_js


def test_vue_import_api_helper_uses_web_fetch_preview_and_commit_contracts():
    imports_js = _read("frontend/src/api/imports.js")

    assert "export async function previewWebFetch({ projectId, url })" in imports_js
    assert 'apiPost("/api/import/web-fetch/preview"' in imports_js
    assert "project_id: projectId" in imports_js
    assert "return data.preview || null" in imports_js
    assert "export async function commitWebFetch({ projectId, preview })" in imports_js
    assert 'apiPost("/api/import/web-fetch/commit"' in imports_js
    assert "preview" in imports_js
    assert "请输入要抓取的网页地址" in imports_js
    assert "请先抓取网页预览" in imports_js


def test_vue_document_import_panel_renders_import_preview_summary():
    panel_vue = _read("frontend/src/components/DocumentImportPanel.vue")
    library_vue = _read("frontend/src/views/LibraryView.vue")

    for marker in [
        "导入预检",
        "预检当前项目目录",
        "预检结果",
        "可导入",
        "跳过",
        "skipped_details",
        "preview-import",
        "importPreview",
        "importPreviewLoading",
        "importPreviewError",
        ':disabled="importSubmitting || importPreviewLoading || !selectedProjectId"',
        "preview-import",
    ]:
        assert marker in panel_vue

    assert "@preview-import" in library_vue
    assert ":import-preview=\"importPreview\"" in library_vue
    assert ":import-preview-loading=\"importPreviewLoading\"" in library_vue
    assert ":import-preview-error=\"importPreviewError\"" in library_vue


def test_vue_document_import_panel_renders_web_fetch_preview_controls():
    panel_vue = _read("frontend/src/components/DocumentImportPanel.vue")
    library_vue = _read("frontend/src/views/LibraryView.vue")

    for marker in [
        "网页抓取",
        "抓取公开网页",
        "网页抓取预览",
        "webFetchPreview",
        "webFetchPreviewLoading",
        "webFetchPreviewError",
        "preview-web-fetch",
        "commit-web-fetch",
        "抓取网页预览",
        "确认导入网页快照",
        "robots.txt",
        "content_length",
        "final_url",
        "fetched_at",
    ]:
        assert marker in panel_vue

    assert "@submit.prevent=\"previewWebFetchUrl\"" in panel_vue
    assert "@click=\"commitWebFetchPreview\"" in panel_vue
    assert ":disabled=\"importSubmitting || webFetchPreviewLoading || !selectedProjectId\"" in panel_vue
    assert ":disabled=\"importSubmitting || !selectedProjectId || !webFetchPreview\"" in panel_vue
    assert "@preview-web-fetch" in library_vue
    assert "@commit-web-fetch" in library_vue
    assert ":web-fetch-preview=\"webFetchPreview\"" in library_vue
    assert ":web-fetch-preview-loading=\"webFetchPreviewLoading\"" in library_vue
    assert ":web-fetch-preview-error=\"webFetchPreviewError\"" in library_vue


def test_vue_app_handles_import_preview_state_without_import_side_effects():
    app_vue = _read("frontend/src/App.vue")
    state_js = _read("frontend/src/state/app-state.js")

    assert "previewProjectImport" in app_vue
    assert "handlePreviewImport" in app_vue
    assert "@preview-import=\"handlePreviewImport\"" in app_vue
    assert ":import-preview=\"appState.importPreview\"" in app_vue
    assert ":import-preview-loading=\"appState.importPreviewLoading\"" in app_vue
    assert ":import-preview-error=\"appState.importPreviewError\"" in app_vue
    assert "formatImportPreview" in app_vue
    assert "导入预检完成" in app_vue

    preview_block = app_vue.split("async function handlePreviewImport()", 1)[1].split("\nasync function", 1)[0]
    assert "previewProjectImport({" in preview_block
    assert "projectId: appState.selectedProjectId" in preview_block
    assert "appState.importPreview = preview" in preview_block
    assert "await loadLibraryDocuments()" not in preview_block
    assert "await loadImportBatches()" not in preview_block

    for state_field in [
        "importPreview",
        "importPreviewLoading",
        "importPreviewError",
    ]:
        assert f"{state_field}:" in state_js


def test_vue_app_handles_web_fetch_preview_and_commit_state():
    app_vue = _read("frontend/src/App.vue")
    state_js = _read("frontend/src/state/app-state.js")

    for imported_name in [
        "previewWebFetch",
        "commitWebFetch",
    ]:
        assert imported_name in app_vue

    assert "handlePreviewWebFetch" in app_vue
    assert "handleCommitWebFetch" in app_vue
    assert "@preview-web-fetch=\"handlePreviewWebFetch\"" in app_vue
    assert "@commit-web-fetch=\"handleCommitWebFetch\"" in app_vue
    assert ":web-fetch-preview=\"appState.webFetchPreview\"" in app_vue
    assert ":web-fetch-preview-loading=\"appState.webFetchPreviewLoading\"" in app_vue
    assert ":web-fetch-preview-error=\"appState.webFetchPreviewError\"" in app_vue
    assert "网页抓取预览完成" in app_vue
    assert "网页抓取已导入" in app_vue

    preview_block = app_vue.split("async function handlePreviewWebFetch", 1)[1].split("\nasync function", 1)[0]
    assert "previewWebFetch({" in preview_block
    assert "projectId: appState.selectedProjectId" in preview_block
    assert "appState.webFetchPreview = preview" in preview_block
    assert "await loadLibraryDocuments()" not in preview_block
    assert "await loadImportBatches()" not in preview_block

    commit_block = app_vue.split("async function handleCommitWebFetch", 1)[1].split("\nasync function", 1)[0]
    assert "commitWebFetch({" in commit_block
    assert "preview: payload.preview || appState.webFetchPreview" in commit_block
    assert "await loadLibraryDocuments()" not in commit_block
    assert "clearWebFetchPreview()" in commit_block

    for state_field in [
        "webFetchPreview",
        "webFetchPreviewLoading",
        "webFetchPreviewError",
    ]:
        assert f"{state_field}:" in state_js


def test_vue_document_collections_api_helper_uses_existing_management_contracts():
    collections_path = Path("frontend/src/api/document-collections.js")
    assert collections_path.exists(), "B-141L should add a Vue document collections API helper"
    collections_js = _read(str(collections_path))

    assert 'import { apiGet, apiPost } from "./client.js";' in collections_js
    assert "export async function listDocumentCollections(projectId)" in collections_js
    assert "if (!projectId)" in collections_js
    assert "return []" in collections_js
    assert "new URLSearchParams({ project_id: projectId })" in collections_js
    assert 'apiGet(`/api/document-collections?${params.toString()}`)' in collections_js
    assert "data.collections || []" in collections_js
    assert "export async function createDocumentCollection({ projectId, name })" in collections_js
    assert 'throw new Error("请先创建或选择项目空间")' in collections_js
    assert 'throw new Error("请输入文档集合名称")' in collections_js
    assert 'apiPost("/api/document-collections"' in collections_js
    assert "project_id: projectId" in collections_js
    assert "name: cleanName" in collections_js
    assert "export async function deleteDocumentCollection(collectionId)" in collections_js
    assert 'throw new Error("请选择文档集合")' in collections_js
    assert 'apiPost("/api/document-collections/delete", { collection_id: collectionId })' in collections_js
    assert "export async function updateDocumentCollection({ collectionId, name })" in collections_js
    assert 'apiPost("/api/document-collections/update"' in collections_js
    assert "collection_id: collectionId" in collections_js


def test_vue_document_collection_panel_renders_readonly_filter_controls():
    panel_path = Path("frontend/src/components/DocumentCollectionPanel.vue")
    assert panel_path.exists(), "B-141L should add DocumentCollectionPanel"

    panel_vue = _read(str(panel_path))
    library_vue = _read("frontend/src/views/LibraryView.vue")

    for marker in [
        "文档集合",
        "新建集合",
        "集合名称",
        "创建集合",
        "重命名集合",
        "保存名称",
        "取消",
        "新的集合名称",
        "全部文档",
        "未分组",
        "刷新集合",
        "删除集合",
        "暂无文档集合",
        "document_count",
        'v-for="collection in documentCollections"',
        "collectionFormSubmitting",
        "collectionFormError",
        "collectionFormStatus",
        "collectionRenameSubmitting",
        "collectionRenameError",
        "collectionRenameStatus",
        "deletingCollectionId",
        "editingCollectionId",
        'defineEmits(["refresh-collections", "select-collection", "create-collection", "delete-collection", "update-collection"])',
    ]:
        assert marker in panel_vue

    for forbidden_action in ["加入集合", "移出集合"]:
        assert forbidden_action not in panel_vue

    assert "DocumentCollectionPanel" in library_vue
    assert ":document-collections=\"documentCollections\"" in library_vue
    assert ":selected-document-collection-id=\"selectedDocumentCollectionId\"" in library_vue
    assert ":document-collections-loading=\"documentCollectionsLoading\"" in library_vue
    assert ":document-collections-load-error=\"documentCollectionsLoadError\"" in library_vue
    assert ":collection-form-submitting=\"collectionFormSubmitting\"" in library_vue
    assert ":collection-form-error=\"collectionFormError\"" in library_vue
    assert ":collection-form-status=\"collectionFormStatus\"" in library_vue
    assert ":collection-rename-submitting=\"collectionRenameSubmitting\"" in library_vue
    assert ":collection-rename-error=\"collectionRenameError\"" in library_vue
    assert ":collection-rename-status=\"collectionRenameStatus\"" in library_vue
    assert ":deleting-collection-id=\"deletingCollectionId\"" in library_vue
    assert "@refresh-collections" in library_vue
    assert "@select-collection" in library_vue
    assert "@create-collection" in library_vue
    assert "@delete-collection" in library_vue
    assert "@update-collection" in library_vue


def test_vue_document_collections_api_helper_uses_existing_item_contracts():
    collections_js = _read("frontend/src/api/document-collections.js")

    assert "export async function addDocumentToCollection({ collectionId, documentId })" in collections_js
    assert 'apiPost("/api/document-collections/items/add"' in collections_js
    assert "collection_id: collectionId" in collections_js
    assert "document_ids: [documentId]" in collections_js
    assert "export async function removeDocumentFromCollection({ collectionId, documentId })" in collections_js
    assert 'apiPost("/api/document-collections/items/remove"' in collections_js
    assert 'throw new Error("请选择文档集合")' in collections_js
    assert 'throw new Error("请选择文档")' in collections_js


def test_vue_document_list_panel_renders_collection_item_controls():
    list_panel_vue = _read("frontend/src/components/DocumentListPanel.vue")
    library_vue = _read("frontend/src/views/LibraryView.vue")

    for marker in [
        "加入集合",
        "移出集合",
        "documentCollections",
        "selectedDocumentCollectionId",
        "collectionSelections",
        "collectionItemSubmittingId",
        "collectionItemError",
        "collectionItemStatus",
        "availableCollectionsForDocument",
        "add-document-to-collection",
        "remove-document-from-collection",
        'v-for="collection in availableCollectionsForDocument(document)"',
        'selectedDocumentCollectionId !== "unassigned"',
    ]:
        assert marker in list_panel_vue

    assert ":document-collections=\"documentCollections\"" in library_vue
    assert ":selected-document-collection-id=\"selectedDocumentCollectionId\"" in library_vue
    assert ":collection-item-submitting-id=\"collectionItemSubmittingId\"" in library_vue
    assert ":collection-item-error=\"collectionItemError\"" in library_vue
    assert ":collection-item-status=\"collectionItemStatus\"" in library_vue
    assert "@add-document-to-collection" in library_vue
    assert "@remove-document-from-collection" in library_vue


def test_vue_document_list_panel_renders_document_delete_control():
    list_panel_vue = _read("frontend/src/components/DocumentListPanel.vue")
    library_vue = _read("frontend/src/views/LibraryView.vue")

    for marker in [
        "删除文档",
        "deletingDocumentId",
        "documentDeleteError",
        "documentDeleteStatus",
        "delete-document",
        'defineEmits(["refresh-documents", "select-document", "add-document-to-collection", "remove-document-from-collection", "delete-document"])',
    ]:
        assert marker in list_panel_vue

    assert ":deleting-document-id=\"deletingDocumentId\"" in library_vue
    assert ":document-delete-error=\"documentDeleteError\"" in library_vue
    assert ":document-delete-status=\"documentDeleteStatus\"" in library_vue
    assert "@delete-document" in library_vue


def test_vue_app_loads_document_collections_and_filters_document_list():
    app_vue = _read("frontend/src/App.vue")
    state_js = _read("frontend/src/state/app-state.js")

    assert "listDocumentCollections" in app_vue
    assert "createDocumentCollection" in app_vue
    assert "deleteDocumentCollection" in app_vue
    assert "updateDocumentCollection" in app_vue
    assert "loadDocumentCollections" in app_vue
    assert "handleSelectDocumentCollection" in app_vue
    assert "handleCreateDocumentCollection" in app_vue
    assert "handleDeleteDocumentCollection" in app_vue
    assert "handleUpdateDocumentCollection" in app_vue
    assert ":document-collections=\"appState.documentCollections\"" in app_vue
    assert ":selected-document-collection-id=\"appState.selectedDocumentCollectionId\"" in app_vue
    assert ":document-collections-loading=\"appState.documentCollectionsLoading\"" in app_vue
    assert ":document-collections-load-error=\"appState.documentCollectionsLoadError\"" in app_vue
    assert ":collection-form-submitting=\"appState.collectionFormSubmitting\"" in app_vue
    assert ":collection-form-error=\"appState.collectionFormError\"" in app_vue
    assert ":collection-form-status=\"appState.collectionFormStatus\"" in app_vue
    assert ":collection-rename-submitting=\"appState.collectionRenameSubmitting\"" in app_vue
    assert ":collection-rename-error=\"appState.collectionRenameError\"" in app_vue
    assert ":collection-rename-status=\"appState.collectionRenameStatus\"" in app_vue
    assert ":deleting-collection-id=\"appState.deletingCollectionId\"" in app_vue
    assert "@refresh-collections=\"loadDocumentCollections\"" in app_vue
    assert "@select-collection=\"handleSelectDocumentCollection\"" in app_vue
    assert "@create-collection=\"handleCreateDocumentCollection\"" in app_vue
    assert "@delete-collection=\"handleDeleteDocumentCollection\"" in app_vue
    assert "@update-collection=\"handleUpdateDocumentCollection\"" in app_vue
    assert "appState.documentCollections = collections" in app_vue
    assert "appState.selectedDocumentCollectionId = collectionId" in app_vue
    assert "await loadDocumentCollections()" in app_vue
    assert "listDocuments(appState.selectedProjectId, appState.selectedDocumentCollectionId)" in app_vue

    selection_block = app_vue.split("async function handleSelectDocumentCollection(collectionId)", 1)[1].split("\nasync function", 1)[0]
    assert "appState.selectedDocumentCollectionId = collectionId" in selection_block
    assert "await loadLibraryDocuments()" in selection_block

    create_block = app_vue.split("async function handleCreateDocumentCollection(name)", 1)[1].split("\nasync function", 1)[0]
    assert "createDocumentCollection({" in create_block
    assert "projectId: appState.selectedProjectId" in create_block
    assert "await loadDocumentCollections()" in create_block
    assert "appState.collectionFormStatus = \"文档集合已创建\"" in create_block

    update_block = app_vue.split("async function handleUpdateDocumentCollection(payload)", 1)[1].split("\nasync function", 1)[0]
    assert "updateDocumentCollection({" in update_block
    assert "collectionId: payload.collectionId" in update_block
    assert "name: payload.name" in update_block
    assert "await loadDocumentCollections()" in update_block
    assert "appState.collectionRenameStatus = \"文档集合已重命名\"" in update_block

    delete_block = app_vue.split("async function handleDeleteDocumentCollection(collectionId)", 1)[1].split("\nasync function", 1)[0]
    assert "window.confirm" in delete_block
    assert "集合内文档不会被删除" in delete_block
    assert "deleteDocumentCollection(collectionId)" in delete_block
    assert "appState.selectedDocumentCollectionId = \"\"" in delete_block
    assert "await loadDocumentCollections()" in delete_block
    assert "await loadLibraryDocuments()" in delete_block

    for state_field in [
        "documentCollections",
        "selectedDocumentCollectionId",
        "documentCollectionsLoading",
        "documentCollectionsLoadError",
        "collectionFormSubmitting",
        "collectionFormError",
        "collectionFormStatus",
        "collectionRenameSubmitting",
        "collectionRenameError",
        "collectionRenameStatus",
        "deletingCollectionId",
    ]:
        assert f"{state_field}:" in state_js


def test_vue_app_handles_document_collection_item_add_and_remove():
    app_vue = _read("frontend/src/App.vue")
    state_js = _read("frontend/src/state/app-state.js")

    for imported_name in [
        "addDocumentToCollection",
        "removeDocumentFromCollection",
    ]:
        assert imported_name in app_vue

    for marker in [
        ":collection-item-submitting-id=\"appState.collectionItemSubmittingId\"",
        ":collection-item-error=\"appState.collectionItemError\"",
        ":collection-item-status=\"appState.collectionItemStatus\"",
        "@add-document-to-collection=\"handleAddDocumentToCollection\"",
        "@remove-document-from-collection=\"handleRemoveDocumentFromCollection\"",
        "handleAddDocumentToCollection",
        "handleRemoveDocumentFromCollection",
        "appState.collectionItemStatus = \"文档已加入集合\"",
        "appState.collectionItemStatus = \"文档已从集合移出\"",
        "await loadDocumentCollections()",
        "await loadLibraryDocuments()",
    ]:
        assert marker in app_vue

    add_block = app_vue.split("async function handleAddDocumentToCollection(payload)", 1)[1].split("\nasync function", 1)[0]
    assert "addDocumentToCollection({" in add_block
    assert "collectionId: payload.collectionId" in add_block
    assert "documentId: payload.documentId" in add_block

    remove_block = app_vue.split("async function handleRemoveDocumentFromCollection(payload)", 1)[1].split("\nasync function", 1)[0]
    assert "removeDocumentFromCollection({" in remove_block
    assert "collectionId: payload.collectionId" in remove_block
    assert "documentId: payload.documentId" in remove_block

    for state_field in [
        "collectionItemSubmittingId",
        "collectionItemError",
        "collectionItemStatus",
    ]:
        assert f"{state_field}:" in state_js


def test_vue_app_handles_document_delete_state_and_refresh():
    app_vue = _read("frontend/src/App.vue")
    state_js = _read("frontend/src/state/app-state.js")

    assert "deleteDocument" in app_vue

    for marker in [
        ":deleting-document-id=\"appState.deletingDocumentId\"",
        ":document-delete-error=\"appState.documentDeleteError\"",
        ":document-delete-status=\"appState.documentDeleteStatus\"",
        "@delete-document=\"handleDeleteDocument\"",
        "handleDeleteDocument",
        "clearDocumentDeleteStatus",
        "appState.documentDeleteStatus = \"文档已删除\"",
    ]:
        assert marker in app_vue

    delete_block = app_vue.split("async function handleDeleteDocument(documentId)", 1)[1].split("\nfunction clear", 1)[0]
    assert "window.confirm" in delete_block
    assert "源文件不会被删除" in delete_block
    assert "deleteDocument(documentId)" in delete_block
    assert "appState.deletingDocumentId = documentId" in delete_block
    assert "appState.selectedDocumentId = \"\"" in delete_block
    assert "appState.selectedDocument = null" in delete_block
    assert "await loadDocumentCollections()" in delete_block
    assert "await loadLibraryDocuments()" in delete_block

    for state_field in [
        "deletingDocumentId",
        "documentDeleteError",
        "documentDeleteStatus",
    ]:
        assert f"{state_field}:" in state_js


def test_vue_project_api_helper_uses_existing_rename_and_delete_contracts():
    projects_js = _read("frontend/src/api/projects.js")

    assert "export async function renameProject({ projectId, name })" in projects_js
    assert 'throw new Error("请选择项目空间")' in projects_js
    assert 'throw new Error("请输入项目空间名称")' in projects_js
    assert 'apiPost("/api/projects/rename"' in projects_js
    assert "project_id: projectId" in projects_js
    assert "name: cleanName" in projects_js
    assert "export async function deleteProject(projectId)" in projects_js
    assert 'apiPost("/api/projects/delete", { project_id: projectId })' in projects_js


def test_vue_project_space_panel_renders_project_rename_and_delete_controls():
    panel_vue = _read("frontend/src/components/ProjectSpacePanel.vue")
    library_vue = _read("frontend/src/views/LibraryView.vue")

    for marker in [
        "重命名项目空间",
        "新的项目名称",
        "保存项目名称",
        "删除项目空间",
        "项目内文档记录也会被删除",
        "projectRenameSubmitting",
        "projectDeleteSubmitting",
        "projectMutationError",
        "projectMutationStatus",
        'defineEmits(["refresh-projects", "select-project", "create-project", "rename-project", "delete-project"])',
    ]:
        assert marker in panel_vue

    assert "@rename-project" in library_vue
    assert "@delete-project" in library_vue
    assert ":project-rename-submitting=\"projectRenameSubmitting\"" in library_vue
    assert ":project-delete-submitting=\"projectDeleteSubmitting\"" in library_vue
    assert ":project-mutation-error=\"projectMutationError\"" in library_vue
    assert ":project-mutation-status=\"projectMutationStatus\"" in library_vue


def test_vue_app_handles_project_rename_and_delete_state_refresh():
    app_vue = _read("frontend/src/App.vue")
    state_js = _read("frontend/src/state/app-state.js")

    for imported_name in [
        "renameProject",
        "deleteProject",
    ]:
        assert imported_name in app_vue

    for marker in [
        ":project-rename-submitting=\"appState.projectRenameSubmitting\"",
        ":project-delete-submitting=\"appState.projectDeleteSubmitting\"",
        ":project-mutation-error=\"appState.projectMutationError\"",
        ":project-mutation-status=\"appState.projectMutationStatus\"",
        "@rename-project=\"handleRenameProject\"",
        "@delete-project=\"handleDeleteProject\"",
        "handleRenameProject",
        "handleDeleteProject",
        "clearProjectMutationStatus",
        "resetLibraryStateAfterProjectDelete",
        "appState.projectMutationStatus = \"项目空间已重命名\"",
        "appState.projectMutationStatus = \"项目空间已删除\"",
    ]:
        assert marker in app_vue

    rename_block = app_vue.split("async function handleRenameProject(name)", 1)[1].split("\nasync function", 1)[0]
    assert "renameProject({" in rename_block
    assert "projectId: appState.selectedProjectId" in rename_block
    assert "name" in rename_block
    assert "await loadProjectSpaces()" in rename_block

    delete_block = app_vue.split("async function handleDeleteProject()", 1)[1].split("\nfunction reset", 1)[0]
    assert "window.confirm" in delete_block
    assert "项目内文档记录也会被删除" in delete_block
    assert "deleteProject(appState.selectedProjectId)" in delete_block
    assert "selectProject(\"\")" in delete_block
    assert "resetLibraryStateAfterProjectDelete()" in delete_block
    assert "await loadProjectSpaces()" in delete_block

    reset_block = app_vue.split("function resetLibraryStateAfterProjectDelete()", 1)[1].split("\nfunction clear", 1)[0]
    for marker in [
        "appState.documents = []",
        "appState.selectedDocumentId = \"\"",
        "appState.selectedDocument = null",
        "appState.documentCollections = []",
        "appState.selectedDocumentCollectionId = \"\"",
        "appState.importBatches = []",
        "appState.selectedImportBatch = null",
        "appState.selectedImportBatchItems = []",
    ]:
        assert marker in reset_block

    for state_field in [
        "projectRenameSubmitting",
        "projectDeleteSubmitting",
        "projectMutationError",
        "projectMutationStatus",
    ]:
        assert f"{state_field}:" in state_js


def test_vue_settings_api_helper_uses_existing_llm_and_profile_contracts():
    settings_path = Path("frontend/src/api/settings.js")
    assert settings_path.exists(), "B-141R should add a Vue settings API helper"
    settings_js = _read(str(settings_path))

    assert 'import { apiGet, apiPost } from "./client.js";' in settings_js
    assert "export async function loadLlmSettings()" in settings_js
    assert 'apiGet("/api/settings/llm")' in settings_js
    assert "export async function saveLlmSettings({ provider, apiBase, model, apiKey })" in settings_js
    assert 'apiPost("/api/settings/llm"' in settings_js
    assert "api_base: apiBase" in settings_js
    assert "api_key: apiKey" in settings_js
    assert "export async function testLlmSettings()" in settings_js
    assert 'apiPost("/api/settings/llm/test", {})' in settings_js

    for marker in [
        "export async function listModelProfiles()",
        'apiGet("/api/model-profiles")',
        "export async function saveModelProfile(profile)",
        'apiPost(path, payload)',
        '\"/api/model-profiles/update\"',
        '\"/api/model-profiles\"',
        "profile_id: profile.id || profile.profile_id || \"\"",
        "api_key_ref: profile.apiKeyRef",
        "export async function deleteModelProfile(profileId)",
        'apiPost("/api/model-profiles/delete", { profile_id: profileId })',
        "export async function setDefaultModelProfile(profileId)",
        'apiPost("/api/model-profiles/default", { profile_id: profileId || "" })',
        "export async function testModelProfile(profileId)",
        'apiPost("/api/model-profiles/test", { profile_id: profileId })',
    ]:
        assert marker in settings_js


def test_vue_settings_api_helper_uses_existing_prompt_preset_contracts():
    settings_js = _read("frontend/src/api/settings.js")

    for marker in [
        "export async function listPromptPresets(projectId)",
        'throw new Error("请先创建或选择项目空间")',
        "apiGet(`/api/prompt-presets?project_id=${encodeURIComponent(projectId)}`)",
        "export async function savePromptPreset(preset)",
        "project_id: preset.projectId",
        "preset_id: preset.id || preset.preset_id || \"\"",
        "name: String(preset.name || \"\").trim()",
        "description: String(preset.description || \"\").trim()",
        "system_prompt: String(preset.systemPrompt || preset.system_prompt || \"\").trim()",
        "answer_format: String(preset.answerFormat || preset.answer_format || \"\").trim()",
        '"/api/prompt-presets/update"',
        '"/api/prompt-presets"',
        "export async function deletePromptPreset(presetId)",
        'apiPost("/api/prompt-presets/delete", { preset_id: presetId })',
        "export async function setDefaultPromptPreset({ projectId, presetId })",
        'apiPost("/api/prompt-presets/default"',
        "project_id: projectId",
        "preset_id: presetId || \"\"",
    ]:
        assert marker in settings_js


def test_vue_settings_view_renders_llm_settings_and_model_profile_controls():
    settings_vue = _read("frontend/src/views/SettingsView.vue")

    for marker in [
        "settings-fullscreen",
        'data-settings-action="back"',
        'data-settings-page="answer"',
        'data-settings-page="data"',
        'data-settings-page="appearance"',
        "本机回答",
        "本机快速",
        "在线回答",
        "连接详情",
        "服务地址",
        "模型名",
        "Key 引用",
        "留空不覆盖已有 Key",
        "不回显明文",
        "保存连接",
        "当前默认",
        "保存",
        "取消编辑",
        "测试",
        "设为默认",
        "删除",
        "env:RAG_LLM_API_KEY",
        "env:DEEPSEEK_API_KEY",
        "saved:RAG_LLM_API_KEY",
        "profileForm",
        "setLocalAnswer",
        "setOnlineAnswer",
        "editProfile",
        'v-for="profile in modelProfiles"',
        'defineEmits(["back", "change-settings-page", "load-settings", "save-llm-settings", "test-llm-settings", "load-model-profiles", "save-model-profile", "delete-model-profile", "set-default-model-profile", "test-model-profile", "load-prompt-presets", "save-prompt-preset", "delete-prompt-preset", "set-default-prompt-preset"])',
    ]:
        assert marker in settings_vue
    for old_marker in ["模型 Profile", "API Key", "Prompt 预设"]:
        assert old_marker not in settings_vue

    for prop_name in [
        "llmSettings",
        "llmSettingsLoading",
        "llmSettingsSubmitting",
        "llmSettingsTesting",
        "llmSettingsError",
        "llmSettingsStatus",
        "modelProfiles",
        "defaultModelProfileId",
        "modelProfilesLoading",
        "modelProfileSubmitting",
        "modelProfileTestingId",
        "modelProfileDeletingId",
        "modelProfileDefaultSubmitting",
        "modelProfileMutationError",
        "modelProfileStatus",
    ]:
        assert f"{prop_name}:" in settings_vue


def test_vue_settings_view_renders_prompt_preset_controls():
    settings_vue = _read("frontend/src/views/SettingsView.vue")

    for marker in [
        "回答模板",
        "当前默认",
        "保存模板",
        "取消编辑",
        "系统提示词",
        "回答格式",
        "删除",
        "设为默认",
        "请选择工作区后管理回答模板",
        "暂无回答模板",
        "promptPresetForm",
        "editPromptPreset",
        "resetPromptPresetForm",
        'v-for="preset in promptPresets"',
        'defineEmits(["back", "change-settings-page", "load-settings", "save-llm-settings", "test-llm-settings", "load-model-profiles", "save-model-profile", "delete-model-profile", "set-default-model-profile", "test-model-profile", "load-prompt-presets", "save-prompt-preset", "delete-prompt-preset", "set-default-prompt-preset"])',
    ]:
        assert marker in settings_vue

    for prop_name in [
        "selectedProjectId",
        "promptPresets",
        "promptPresetTemplates",
        "selectedPromptPresetId",
        "promptPresetsLoading",
        "promptPresetLoadError",
        "promptPresetSubmitting",
        "promptPresetDeletingId",
        "promptPresetDefaultSubmitting",
        "promptPresetMutationError",
        "promptPresetStatus",
    ]:
        assert f"{prop_name}:" in settings_vue


def test_vue_app_handles_settings_model_config_state_and_events():
    app_vue = _read("frontend/src/App.vue")
    state_js = _read("frontend/src/state/app-state.js")

    for imported_name in [
        "loadLlmSettings",
        "saveLlmSettings",
        "testLlmSettings",
        "listModelProfiles",
        "saveModelProfile",
        "deleteModelProfile",
        "setDefaultModelProfile",
        "testModelProfile",
    ]:
        assert imported_name in app_vue

    for marker in [
        ":llm-settings=\"appState.llmSettings\"",
        ":settings-page=\"appState.settingsPage\"",
        ":llm-settings-loading=\"appState.llmSettingsLoading\"",
        ":llm-settings-submitting=\"appState.llmSettingsSubmitting\"",
        ":llm-settings-testing=\"appState.llmSettingsTesting\"",
        ":llm-settings-error=\"appState.llmSettingsError\"",
        ":llm-settings-status=\"appState.llmSettingsStatus\"",
        ":model-profiles=\"appState.modelProfiles\"",
        ":default-model-profile-id=\"appState.defaultModelProfileId\"",
        ":model-profiles-loading=\"appState.modelProfilesLoading\"",
        ":model-profile-submitting=\"appState.modelProfileSubmitting\"",
        ":model-profile-testing-id=\"appState.modelProfileTestingId\"",
        ":model-profile-deleting-id=\"appState.modelProfileDeletingId\"",
        ":model-profile-default-submitting=\"appState.modelProfileDefaultSubmitting\"",
        ":model-profile-mutation-error=\"appState.modelProfileMutationError\"",
        ":model-profile-status=\"appState.modelProfileStatus\"",
        "@load-settings=\"loadSettingsPage\"",
        "@back=\"showView('chat')\"",
        "@change-settings-page=\"handleChangeSettingsPage\"",
        "@save-llm-settings=\"handleSaveLlmSettings\"",
        "@test-llm-settings=\"handleTestLlmSettings\"",
        "@load-model-profiles=\"loadModelProfiles\"",
        "@save-model-profile=\"handleSaveModelProfile\"",
        "@delete-model-profile=\"handleDeleteModelProfile\"",
        "@set-default-model-profile=\"handleSetDefaultModelProfile\"",
        "@test-model-profile=\"handleTestModelProfile\"",
        "loadSettingsPage",
        "handleChangeSettingsPage",
        "handleSaveLlmSettings",
        "handleTestLlmSettings",
        "handleSaveModelProfile",
        "handleDeleteModelProfile",
        "handleSetDefaultModelProfile",
        "handleTestModelProfile",
        "appState.llmSettingsStatus = \"模型设置已保存\"",
        "appState.modelProfileStatus = \"模型 Profile 已保存\"",
        "appState.modelProfileStatus = \"默认模型 Profile 已更新\"",
        "appState.modelProfileStatus = \"模型 Profile 已删除\"",
    ]:
        assert marker in app_vue

    for state_field in [
        "llmSettings",
        "llmSettingsLoading",
        "llmSettingsSubmitting",
        "llmSettingsTesting",
        "llmSettingsError",
        "llmSettingsStatus",
        "modelProfilesLoading",
        "modelProfileLoadError",
        "modelProfileSubmitting",
        "modelProfileTestingId",
        "modelProfileDeletingId",
        "modelProfileDefaultSubmitting",
        "modelProfileMutationError",
        "modelProfileStatus",
    ]:
        assert f"{state_field}:" in state_js


def test_vue_app_handles_settings_prompt_preset_state_and_events():
    app_vue = _read("frontend/src/App.vue")
    state_js = _read("frontend/src/state/app-state.js")

    for imported_name in [
        "listPromptPresets",
        "savePromptPreset",
        "deletePromptPreset",
        "setDefaultPromptPreset",
    ]:
        assert imported_name in app_vue

    for marker in [
        ":selected-project-id=\"appState.selectedProjectId\"",
        ":prompt-presets=\"appState.promptPresets\"",
        ":prompt-preset-templates=\"appState.promptPresetTemplates\"",
        ":selected-prompt-preset-id=\"appState.selectedPromptPresetId\"",
        ":prompt-presets-loading=\"appState.promptPresetsLoading\"",
        ":prompt-preset-load-error=\"appState.promptPresetLoadError\"",
        ":prompt-preset-submitting=\"appState.promptPresetSubmitting\"",
        ":prompt-preset-deleting-id=\"appState.promptPresetDeletingId\"",
        ":prompt-preset-default-submitting=\"appState.promptPresetDefaultSubmitting\"",
        ":prompt-preset-mutation-error=\"appState.promptPresetMutationError\"",
        ":prompt-preset-status=\"appState.promptPresetStatus\"",
        "@load-prompt-presets=\"loadPromptPresets\"",
        "@save-prompt-preset=\"handleSavePromptPreset\"",
        "@delete-prompt-preset=\"handleDeletePromptPreset\"",
        "@set-default-prompt-preset=\"handleSetDefaultPromptPreset\"",
        "loadPromptPresets",
        "handleSavePromptPreset",
        "handleDeletePromptPreset",
        "handleSetDefaultPromptPreset",
        "clearPromptPresetState",
        "await loadPromptPresets()",
        "appState.promptPresetStatus = \"Prompt 预设已保存\"",
        "appState.promptPresetStatus = \"Prompt 预设已删除\"",
        "appState.promptPresetStatus = \"默认 Prompt 预设已更新\"",
    ]:
        assert marker in app_vue

    for state_field in [
        "promptPresetsLoading",
        "promptPresetLoadError",
        "promptPresetSubmitting",
        "promptPresetDeletingId",
        "promptPresetDefaultSubmitting",
        "promptPresetMutationError",
        "promptPresetStatus",
    ]:
        assert f"{state_field}:" in state_js

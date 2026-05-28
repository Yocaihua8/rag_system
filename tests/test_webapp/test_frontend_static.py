from pathlib import Path


def test_delete_project_requires_browser_confirmation():
    app_js = Path("webapp/static/js/app.js").read_text(encoding="utf-8")

    assert "confirm(" in app_js
    assert "确认删除当前项目空间" in app_js
    assert "return;" in app_js.split("deleteProjectButton.addEventListener", 1)[1].split("deleteSelectedProject", 1)[0]


def test_empty_states_are_rendered_by_ui_helpers():
    ui_js = Path("webapp/static/js/ui.js").read_text(encoding="utf-8")

    for message in [
        "暂无导入文件",
        "暂无检索结果",
        "暂无来源",
        "本次没有跳过文件",
        "请选择左侧文件查看内容",
    ]:
        assert message in ui_js


def test_empty_states_tell_first_time_users_next_action():
    ui_js = Path("webapp/static/js/ui.js").read_text(encoding="utf-8")
    app_js = Path("webapp/static/js/app.js").read_text(encoding="utf-8")

    for message in [
        "暂无导入文件。点击“选择本机文件夹导入”开始。",
        "暂无来源。请先在资料库导入文件，或换一个更贴近资料内容的问题。",
        "暂无检索结果。请换一个关键词，或先到资料库导入文件。",
        "请先在资料库导入文件，再开始评估。",
    ]:
        assert message in ui_js

    assert "暂无导入文件。点击“选择本机文件夹导入”开始。" in app_js


def test_frontend_errors_include_recovery_hint():
    ui_js = Path("webapp/static/js/ui.js").read_text(encoding="utf-8")
    app_js = Path("webapp/static/js/app.js").read_text(encoding="utf-8")

    assert "function formatRecoverableError" in ui_js
    assert "function setErrorStatus" in ui_js
    assert "function setInlineErrorStatus" in ui_js
    assert "请检查项目空间、资料或网络后重试。" in ui_js
    assert "当前项目目录不可访问" in ui_js
    assert "Docker 模式可填写 /workspace" in ui_js
    assert "请选择包含 Markdown、TXT、代码、配置、DOCX 或 PDF 文件的文件夹" in ui_js
    assert "请先到设置页创建项目空间，或在资料库选择已有项目空间" in ui_js
    assert "setErrorStatus(error)" in app_js
    assert "setInlineErrorStatus(llmSettingsStatusEl, error" in app_js
    assert "setStatus(error.message)" not in app_js


def test_frontend_global_error_boundary_is_wired_to_recoverable_status():
    app_js = Path("webapp/static/js/app.js").read_text(encoding="utf-8")

    assert "function handleGlobalFrontendError" in app_js
    assert 'window.addEventListener("error", handleGlobalFrontendError)' in app_js
    assert 'window.addEventListener("unhandledrejection", handleGlobalFrontendError)' in app_js
    assert "前端出现未处理错误" in app_js
    assert "setErrorStatus(" in app_js.split("function handleGlobalFrontendError", 1)[1]


def test_model_settings_errors_include_specific_recovery_hints():
    ui_js = Path("webapp/static/js/ui.js").read_text(encoding="utf-8")
    app_js = Path("webapp/static/js/app.js").read_text(encoding="utf-8")

    assert "模型 API Key 未配置" in ui_js
    assert "请在设置页填写 API Key，或配置 RAG_LLM_API_KEY / DEEPSEEK_API_KEY" in ui_js
    assert "模型服务连接失败" in ui_js
    assert "请检查 API 地址、模型名称和本地网络后重试" in ui_js
    assert "模型服务鉴权失败" in ui_js
    assert "请确认 API Key 是否有效，且账号有当前模型权限" in ui_js
    assert "setInlineErrorStatus(llmSettingsStatusEl, error)" in app_js


def test_model_settings_status_summarizes_provider_base_and_model_without_key():
    app_js = Path("webapp/static/js/app.js").read_text(encoding="utf-8")

    assert "function formatLlmSettingsSummary" in app_js
    assert "providerText" in app_js
    assert "baseText" in app_js
    assert "modelText" in app_js
    assert "模型服务：" in app_js
    assert "API 地址：" in app_js
    assert "模型名称：" in app_js
    assert "API Key：" in app_js
    assert "Provider：" not in app_js
    assert "API Base：" not in app_js
    assert " / Key：" not in app_js
    assert "模型设置已保存。" in app_js
    assert "连接成功：" in app_js
    assert "formatLlmSettingsSummary(data.settings)" in app_js
    assert "formatLlmSettingsSummary(data.settings || currentLlmSettings())" in app_js
    assert "llmApiKeyInput.value" not in app_js.split("function formatLlmSettingsSummary", 1)[1]


def test_model_settings_inputs_have_non_technical_hints_without_key_examples():
    index_html = Path("webapp/static/index.html").read_text(encoding="utf-8")

    for text in [
        "例如：https://api.deepseek.com/v1",
        "填写 OpenAI-compatible API 地址，通常以 /v1 结尾。",
        "例如：deepseek-chat",
        "填写服务商提供的模型名称，需和账号权限一致。",
        "粘贴 API Key；留空不覆盖已有 Key",
        "页面只显示 Key 状态，不回显明文。",
    ]:
        assert text in index_html

    key_input_block = index_html.split('id="llm-api-key"', 1)[1].split('id="llm-settings-status"', 1)[0]
    assert "sk-" not in key_input_block
    assert "API Key 示例" not in key_input_block


def test_api_layer_has_service_unavailable_fallbacks():
    api_js = Path("webapp/static/js/api.js").read_text(encoding="utf-8")

    assert "SERVICE_UNAVAILABLE_MESSAGE" in api_js
    assert "本地服务暂时不可用" in api_js
    assert "请确认应用已启动后刷新页面" in api_js
    assert "normalizeFetchError" in api_js
    assert api_js.count("throw normalizeFetchError(error)") >= 2
    assert "error instanceof TypeError" in api_js
    assert "new Error(SERVICE_UNAVAILABLE_MESSAGE)" in api_js
    assert "response.json()" in api_js
    assert "服务返回格式异常" in api_js
    assert "服务返回异常" in api_js
    assert "HTTP ${response.status}" in api_js


def test_recent_project_selection_is_persisted_in_browser_storage():
    projects_js = Path("webapp/static/js/projects.js").read_text(encoding="utf-8")

    assert "knowledge-island:selected-project-id" in projects_js
    assert "localStorage.getItem" in projects_js
    assert "localStorage.setItem" in projects_js
    assert "localStorage.removeItem" in projects_js


def test_project_rename_has_dedicated_frontend_entrypoint():
    index_html = Path("webapp/static/index.html").read_text(encoding="utf-8")
    projects_js = Path("webapp/static/js/projects.js").read_text(encoding="utf-8")
    app_js = Path("webapp/static/js/app.js").read_text(encoding="utf-8")

    assert 'id="rename-project-button"' in index_html
    assert "renameSelectedProject" in projects_js
    assert '"/api/projects/rename"' in projects_js
    assert "renameProjectButton.addEventListener" in app_js


def test_document_list_has_single_document_delete_action():
    ui_js = Path("webapp/static/js/ui.js").read_text(encoding="utf-8")
    projects_js = Path("webapp/static/js/projects.js").read_text(encoding="utf-8")
    app_js = Path("webapp/static/js/app.js").read_text(encoding="utf-8")

    assert "deleteDocument" in projects_js
    assert '"/api/documents/delete"' in projects_js
    assert "onDelete" in ui_js
    assert "移除" in ui_js
    assert "deleteDocument(" in app_js


def test_document_list_can_be_filtered_by_path():
    index_html = Path("webapp/static/index.html").read_text(encoding="utf-8")
    state_js = Path("webapp/static/js/state.js").read_text(encoding="utf-8")
    ui_js = Path("webapp/static/js/ui.js").read_text(encoding="utf-8")
    app_js = Path("webapp/static/js/app.js").read_text(encoding="utf-8")

    assert 'id="document-filter"' in index_html
    assert "documents:" in state_js
    assert "documentFilter:" in state_js
    assert "emptyMessage" in ui_js
    assert "没有匹配文件" in app_js
    assert "documentFilterInput.addEventListener" in app_js
    assert "renderFilteredDocuments" in app_js


def test_document_list_shows_filtered_and_total_count():
    index_html = Path("webapp/static/index.html").read_text(encoding="utf-8")
    ui_js = Path("webapp/static/js/ui.js").read_text(encoding="utf-8")
    app_js = Path("webapp/static/js/app.js").read_text(encoding="utf-8")

    assert 'id="document-count"' in index_html
    assert "renderDocumentCount" in ui_js
    assert "documentCountEl" in app_js
    assert "renderDocumentCount(documentCountEl" in app_js


def test_selected_project_root_path_is_shown_in_sidebar():
    index_html = Path("webapp/static/index.html").read_text(encoding="utf-8")
    ui_js = Path("webapp/static/js/ui.js").read_text(encoding="utf-8")
    app_js = Path("webapp/static/js/app.js").read_text(encoding="utf-8")

    assert 'id="project-root"' in index_html
    assert "renderProjectRoot" in ui_js
    assert "projectRootEl" in app_js
    assert "root_path" in ui_js
    assert "renderSelectedProjectRoot" in app_js


def test_missing_project_root_path_is_shown_in_sidebar():
    ui_js = Path("webapp/static/js/ui.js").read_text(encoding="utf-8")

    assert "root_exists" in ui_js
    assert "目录不存在" in ui_js


def test_import_errors_are_rendered_separately_from_skipped_files():
    index_html = Path("webapp/static/index.html").read_text(encoding="utf-8")
    ui_js = Path("webapp/static/js/ui.js").read_text(encoding="utf-8")
    app_js = Path("webapp/static/js/app.js").read_text(encoding="utf-8")

    assert 'id="import-errors"' in index_html
    assert "renderImportErrors" in ui_js
    assert "没有读取失败的文件。" in ui_js
    assert "读取失败：" in ui_js
    assert "importErrorsEl" in app_js
    assert "data.result.errors" in app_js


def test_import_status_explains_skipped_files_are_not_failures():
    ui_js = Path("webapp/static/js/ui.js").read_text(encoding="utf-8")
    index_html = Path("webapp/static/index.html").read_text(encoding="utf-8")

    assert "以下文件没有导入，通常是格式不支持、文件过大，或属于系统自动忽略的目录。" in ui_js
    assert "未导入：" in ui_js
    assert "本次没有跳过文件。" in ui_js
    assert "导入状态" in index_html


def test_frontend_blocks_import_when_selected_project_root_is_missing():
    projects_js = Path("webapp/static/js/projects.js").read_text(encoding="utf-8")

    assert "selectedProject" in projects_js
    assert "root_exists === false" in projects_js
    assert "项目目录不存在，无法导入" in projects_js


def test_first_run_guide_is_visible_on_web_homepage():
    index_html = Path("webapp/static/index.html").read_text(encoding="utf-8")

    assert 'id="first-run-guide"' in index_html
    assert "创建项目空间" in index_html
    assert "导入目录" in index_html
    assert "配置 DeepSeek" in index_html


def test_first_run_guide_matches_current_non_technical_path():
    index_html = Path("webapp/static/index.html").read_text(encoding="utf-8")

    assert "设置页创建项目空间" in index_html
    assert "选择本机文件夹导入" in index_html
    assert "设置页" in index_html
    assert "未配置模型" in index_html


def test_library_import_actions_are_distinct_for_non_technical_users():
    index_html = Path("webapp/static/index.html").read_text(encoding="utf-8")

    assert "选择本机文件夹导入" in index_html
    assert "同步当前项目目录" in index_html
    assert "/workspace" in index_html


def test_first_run_async_actions_use_busy_button_guard():
    app_js = Path("webapp/static/js/app.js").read_text(encoding="utf-8")

    assert "async function withBusyButton" in app_js
    for button_name in [
        "importButton",
        "folderImportButton",
        "noteImportButton",
        "askButton",
        "startAssessmentButton",
        "assessmentAnswerButton",
        "llmSaveButton",
        "llmTestButton",
    ]:
        assert f"withBusyButton({button_name}" in app_js


def test_web_assessment_entrypoint_is_wired():
    index_html = Path("webapp/static/index.html").read_text(encoding="utf-8")
    app_js = Path("webapp/static/js/app.js").read_text(encoding="utf-8")
    qa_js = Path("webapp/static/js/qa.js").read_text(encoding="utf-8")
    ui_js = Path("webapp/static/js/ui.js").read_text(encoding="utf-8")

    assert 'id="start-assessment-button"' in index_html
    assert 'id="assessment-answer-button"' in index_html
    assert '"/api/assessment/start"' in qa_js
    assert '"/api/assessment/answer"' in qa_js
    assert "startAssessmentButton.addEventListener" in app_js
    assert "renderAssessmentQuestion" in ui_js


def test_browser_folder_import_entrypoint_is_wired():
    index_html = Path("webapp/static/index.html").read_text(encoding="utf-8")
    projects_js = Path("webapp/static/js/projects.js").read_text(encoding="utf-8")
    app_js = Path("webapp/static/js/app.js").read_text(encoding="utf-8")

    assert 'id="folder-import-input"' in index_html
    assert "webkitdirectory" in index_html
    assert 'id="folder-import-button"' in index_html
    assert "/api/import/upload" in projects_js
    assert "webkitRelativePath" in projects_js
    assert "folderImportInput.addEventListener" in app_js


def test_browser_file_upload_entrypoint_is_wired_without_directory_picker():
    index_html = Path("webapp/static/index.html").read_text(encoding="utf-8")
    projects_js = Path("webapp/static/js/projects.js").read_text(encoding="utf-8")
    app_js = Path("webapp/static/js/app.js").read_text(encoding="utf-8")

    assert 'id="file-import-button"' in index_html
    assert "选择文件上传导入" in index_html
    assert 'id="file-import-input"' in index_html
    file_input_block = index_html.split('id="file-import-input"', 1)[1].split("/>", 1)[0]
    assert 'type="file"' in file_input_block
    assert "multiple" in file_input_block
    assert "webkitdirectory" not in file_input_block
    assert "importBrowserFiles" in projects_js
    assert "fileImportInput.addEventListener" in app_js
    assert "fileImportButton" in app_js


def test_browser_file_upload_keeps_filename_relative_path_and_uses_selected_project():
    projects_js = Path("webapp/static/js/projects.js").read_text(encoding="utf-8")

    assert "file.webkitRelativePath || file.name" in projects_js
    assert "relative_path: entry.relativePath" in projects_js
    file_import_block = projects_js.split("export async function importBrowserFiles", 1)[1].split(
        "export async function importPlainTextNote",
        1,
    )[0]
    assert "state.selectedProjectId" in file_import_block
    assert "payload.project_id = state.selectedProjectId" in file_import_block
    assert "apiPost(\"/api/import/upload\", payload)" in file_import_block
    assert "browser-upload" in file_import_block


def test_browser_folder_import_sends_binary_documents_as_base64():
    projects_js = Path("webapp/static/js/projects.js").read_text(encoding="utf-8")

    assert '".docx"' in projects_js
    assert '".pdf"' in projects_js
    assert "content_base64" in projects_js
    assert "arrayBuffer" in projects_js
    assert "btoa" in projects_js


def test_web_homepage_uses_simplified_three_column_workbench_layout():
    index_html = Path("webapp/static/index.html").read_text(encoding="utf-8")
    styles_css = Path("webapp/static/styles.css").read_text(encoding="utf-8")

    for class_name in [
        "workspace-shell",
        "workspace-left",
        "workspace-main",
        "workspace-center",
        "workspace-right",
        "ask-card",
        "source-preview-card",
    ]:
        assert class_name in index_html

    assert "grid-template-columns: 252px minmax(0, 1fr)" in styles_css
    assert "--color-bg: #f5f7fa" in styles_css
    assert "--color-primary: #0e7c70" in styles_css
    assert "color-scheme: light" in styles_css


def test_left_navigation_switches_between_dedicated_views():
    index_html = Path("webapp/static/index.html").read_text(encoding="utf-8")
    app_js = Path("webapp/static/js/app.js").read_text(encoding="utf-8")
    styles_css = Path("webapp/static/styles.css").read_text(encoding="utf-8")

    assert 'data-view-target="workbench-view"' in index_html
    assert 'data-view-target="library-view"' in index_html
    assert 'data-view-target="assessment-view"' in index_html
    assert 'data-view-target="settings-view"' in index_html

    assert 'id="workbench-view"' in index_html
    assert 'id="library-view"' in index_html
    assert 'id="assessment-view"' in index_html
    assert 'id="settings-view"' in index_html
    assert 'class="workspace-view active"' in index_html

    assert "viewNavButtons" in app_js
    assert "showView" in app_js
    assert "hidden" in app_js
    assert "workspace-view" in styles_css
    assert ".workspace-view[hidden]" in styles_css


def test_assessment_view_has_radar_and_score_overview():
    index_html = Path("webapp/static/index.html").read_text(encoding="utf-8")
    app_js = Path("webapp/static/js/app.js").read_text(encoding="utf-8")
    ui_js = Path("webapp/static/js/ui.js").read_text(encoding="utf-8")
    styles_css = Path("webapp/static/styles.css").read_text(encoding="utf-8")

    assert 'id="assessment-overview"' in index_html
    assert 'id="assessment-radar-polygon"' in index_html
    assert 'id="assessment-score-ring"' in index_html
    assert 'id="assessment-score-value"' in index_html
    assert 'id="assessment-matched-points"' in index_html
    assert 'id="assessment-missing-points"' in index_html
    assert 'id="assessment-source-path"' in index_html

    assert "assessmentOverviewEl" in app_js
    assert "renderAssessmentOverview" in app_js
    assert "export function renderAssessmentOverview" in ui_js
    assert "buildRadarPoints" in ui_js
    assert "--score-percent" in ui_js
    assert "assessment-radar" in styles_css
    assert "score-ring" in styles_css


def test_assessment_view_supports_multi_question_frontend_flow():
    index_html = Path("webapp/static/index.html").read_text(encoding="utf-8")
    app_js = Path("webapp/static/js/app.js").read_text(encoding="utf-8")
    state_js = Path("webapp/static/js/state.js").read_text(encoding="utf-8")
    ui_js = Path("webapp/static/js/ui.js").read_text(encoding="utf-8")

    for element_id in [
        "assessment-progress",
        "assessment-next-button",
        "assessment-result-history",
        "assessment-missed-questions",
    ]:
        assert f'id="{element_id}"' in index_html

    for state_field in [
        "assessmentQuestionIndex",
        "assessmentResults",
        "assessmentMissedQuestions",
        "assessmentAnsweredCurrent",
    ]:
        assert state_field in state_js

    for function_name in [
        "advanceAssessmentQuestion",
        "completeAssessmentSession",
        "renderAssessmentProgress",
        "renderAssessmentResultHistory",
        "renderAssessmentMissedQuestions",
    ]:
        assert function_name in app_js or function_name in ui_js

    assert "assessmentNextButton.addEventListener" in app_js
    assert "state.assessmentResults.push" in app_js
    assert "state.assessmentMissedQuestions" in app_js


def test_model_settings_view_is_wired():
    index_html = Path("webapp/static/index.html").read_text(encoding="utf-8")
    app_js = Path("webapp/static/js/app.js").read_text(encoding="utf-8")
    settings_js = Path("webapp/static/js/settings.js").read_text(encoding="utf-8")

    for element_id in [
        "llm-settings-form",
        "llm-provider",
        "llm-api-base",
        "llm-api-model",
        "llm-api-key",
        "llm-settings-status",
        "llm-test-button",
    ]:
        assert f'id="{element_id}"' in index_html

    assert "/api/settings/llm" in settings_js
    assert "/api/settings/llm/test" in settings_js
    assert "loadLlmSettings" in app_js
    assert "saveLlmSettings" in app_js
    assert "testLlmSettings" in app_js


def test_model_profile_settings_are_wired():
    index_html = Path("webapp/static/index.html").read_text(encoding="utf-8")
    app_js = Path("webapp/static/js/app.js").read_text(encoding="utf-8")
    settings_js = Path("webapp/static/js/settings.js").read_text(encoding="utf-8")
    state_js = Path("webapp/static/js/state.js").read_text(encoding="utf-8")

    for marker in [
        'id="model-profile-form"',
        'id="model-profile-list"',
        'id="model-profile-name"',
        'id="model-profile-provider"',
        'id="model-profile-api-base"',
        'id="model-profile-model"',
        'id="model-profile-temperature"',
        'id="model-profile-max-tokens"',
        'id="model-profile-api-key-ref"',
        'id="clear-default-model-profile-button"',
    ]:
        assert marker in index_html
    for endpoint in [
        "/api/model-profiles",
        "/api/model-profiles/update",
        "/api/model-profiles/delete",
        "/api/model-profiles/default",
        "/api/model-profiles/test",
    ]:
        assert endpoint in settings_js + app_js
    assert "modelProfiles:" in state_js
    assert "defaultModelProfileId:" in state_js
    assert "refreshModelProfiles" in app_js
    assert "renderModelProfileList" in app_js
    assert "api_key_ref" in settings_js
    assert "sk-" not in index_html.split('id="model-profile-api-key-ref"', 1)[1].split("</section>", 1)[0]


def test_project_chat_history_is_wired():
    index_html = Path("webapp/static/index.html").read_text(encoding="utf-8")
    state_js = Path("webapp/static/js/state.js").read_text(encoding="utf-8")
    qa_js = Path("webapp/static/js/qa.js").read_text(encoding="utf-8")
    ui_js = Path("webapp/static/js/ui.js").read_text(encoding="utf-8")
    app_js = Path("webapp/static/js/app.js").read_text(encoding="utf-8")

    assert 'id="chat-history"' in index_html
    assert "chatMessages:" in state_js
    assert "listChatMessages" in qa_js
    assert "/api/chat/messages" in qa_js
    assert "renderChatHistory" in ui_js
    assert "chatHistoryEl" in app_js
    assert "refreshChatHistory" in app_js


def test_chat_sessions_frontend_is_wired():
    index_html = Path("webapp/static/index.html").read_text(encoding="utf-8")
    qa_js = Path("webapp/static/js/qa.js").read_text(encoding="utf-8")
    state_js = Path("webapp/static/js/state.js").read_text(encoding="utf-8")
    app_js = Path("webapp/static/js/app.js").read_text(encoding="utf-8")
    ui_js = Path("webapp/static/js/ui.js").read_text(encoding="utf-8")

    assert 'id="chat-session-select"' in index_html
    assert 'id="new-chat-session-button"' in index_html
    assert 'id="rename-chat-session-button"' in index_html
    assert 'id="delete-chat-session-button"' in index_html
    for endpoint in [
        "/api/chat/sessions",
        "/api/chat/sessions/rename",
        "/api/chat/sessions/delete",
    ]:
        assert endpoint in qa_js
    assert "chatSessions:" in state_js
    assert "selectedChatSessionId:" in state_js
    assert "renderChatSessions" in ui_js
    assert "refreshChatSessions" in app_js
    assert "state.selectedChatSessionId" in app_js
    assert "session_id" in qa_js


def test_answer_feedback_entrypoint_is_wired():
    index_html = Path("webapp/static/index.html").read_text(encoding="utf-8")
    qa_js = Path("webapp/static/js/qa.js").read_text(encoding="utf-8")
    app_js = Path("webapp/static/js/app.js").read_text(encoding="utf-8")
    ui_js = Path("webapp/static/js/ui.js").read_text(encoding="utf-8")

    assert 'id="answer-feedback"' in index_html
    for rating in ["useful", "not_useful", "source_wrong", "need_more_context"]:
        assert f'data-feedback-rating="{rating}"' in index_html
        assert rating in app_js
    for label in ["有用", "无用", "来源不准", "需要更多上下文"]:
        assert label in index_html

    assert "submitAnswerFeedback" in qa_js
    assert 'apiPost("/api/answer/feedback"' in qa_js
    assert "answerFeedbackEl" in app_js
    assert "answerFeedbackButtons" in app_js
    assert "submitAnswerFeedback(" in app_js
    assert "renderAnswerFeedback" in ui_js
    assert "state.lastAnswerMessageId" in app_js


def test_answer_observability_metadata_is_rendered():
    ui_js = Path("webapp/static/js/ui.js").read_text(encoding="utf-8")
    api_spec = Path("docs/design/api-spec.md").read_text(encoding="utf-8")
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "formatAnswerObservability" in ui_js
    for text in ["问答观测", "top_k", "min_score", "keyword", "vector", "命中来源", "模型", "mode", "provider", "耗时"]:
        assert text in ui_js
    assert "observability" in api_spec
    assert "问答可观察性" in readme


def test_answer_markdown_rendering_uses_sanitizer_and_highlighting():
    index_html = Path("webapp/static/index.html").read_text(encoding="utf-8")
    ui_js = Path("webapp/static/js/ui.js").read_text(encoding="utf-8")
    styles_css = Path("webapp/static/styles.css").read_text(encoding="utf-8")

    assert "marked" in index_html
    assert "dompurify" in index_html
    assert "highlight.js" in index_html
    assert 'id="answer" class="answer markdown-body"' in index_html
    assert "function renderMarkdownElement" in ui_js
    assert "marked.parse" in ui_js
    assert "DOMPurify.sanitize" in ui_js
    assert "hljs.highlightElement" in ui_js
    assert "answerEl.innerHTML" not in ui_js
    assert "answerEl.textContent = `${data.answer}" not in ui_js
    assert "renderMarkdownElement(answerEl" in ui_js
    assert ".markdown-body" in styles_css
    assert ".hljs" in styles_css


def test_chat_history_delete_and_clear_entrypoints_are_wired():
    index_html = Path("webapp/static/index.html").read_text(encoding="utf-8")
    qa_js = Path("webapp/static/js/qa.js").read_text(encoding="utf-8")
    app_js = Path("webapp/static/js/app.js").read_text(encoding="utf-8")
    ui_js = Path("webapp/static/js/ui.js").read_text(encoding="utf-8")

    assert 'id="clear-chat-history-button"' in index_html
    assert "/api/chat/messages/delete" in qa_js
    assert "/api/chat/messages/clear" in qa_js
    assert "确认删除这条聊天记录" in app_js
    assert "确认清空当前项目的全部聊天记录" in app_js
    assert "deleteButton.addEventListener" in ui_js


def test_agent_readonly_tool_entrypoint_is_wired():
    index_html = Path("webapp/static/index.html").read_text(encoding="utf-8")
    agent_js = Path("webapp/static/js/agent.js").read_text(encoding="utf-8")
    app_js = Path("webapp/static/js/app.js").read_text(encoding="utf-8")
    ui_js = Path("webapp/static/js/ui.js").read_text(encoding="utf-8")

    assert 'id="agent-tools-panel"' in index_html
    assert 'id="agent-overview-button"' in index_html
    assert 'id="agent-search-query"' in index_html
    assert 'id="agent-search-button"' in index_html
    assert 'id="agent-tool-result"' in index_html
    assert 'id="agent-tool-runs"' in index_html
    assert 'from "./agent.js"' in app_js
    assert "runAgentTool" in app_js
    assert "listAgentToolRuns" in agent_js
    assert "/api/agent/tools/runs" in agent_js
    assert "search_sources" in app_js
    assert "renderAgentToolResult" in ui_js
    assert "renderAgentToolRuns" in ui_js
    assert "refreshAgentToolRuns" in app_js


def test_agent_tools_metadata_and_run_details_are_wired():
    index_html = Path("webapp/static/index.html").read_text(encoding="utf-8")
    agent_js = Path("webapp/static/js/agent.js").read_text(encoding="utf-8")
    state_js = Path("webapp/static/js/state.js").read_text(encoding="utf-8")
    app_js = Path("webapp/static/js/app.js").read_text(encoding="utf-8")
    ui_js = Path("webapp/static/js/ui.js").read_text(encoding="utf-8")

    assert 'id="agent-tools-list"' in index_html
    assert 'id="agent-tool-run-detail"' in index_html
    assert "agentTools:" in state_js
    assert "selectedAgentToolRun:" in state_js
    assert "listAgentTools" in agent_js
    assert 'apiGet("/api/agent/tools")' in agent_js
    assert "getAgentToolRunDetail" in agent_js
    assert "/api/agent/tools/runs/detail?run_id=" in agent_js
    assert "renderAgentTools" in ui_js
    assert "renderAgentToolRunDetail" in ui_js
    assert "tool.label || tool.title || tool.name" in ui_js
    assert "tool.parameters_schema || tool.parameters" in ui_js
    assert "参数：" in ui_js
    assert "适用场景：" in ui_js
    assert "查看详情" in ui_js
    assert "arguments" in ui_js
    assert "result" in ui_js
    assert "created_at" in ui_js
    assert "refreshAgentTools" in app_js
    assert "showAgentToolRunDetail" in app_js
    assert "setInlineErrorStatus(agentToolRunDetailEl, error)" in app_js


def test_agent_tool_panel_runs_tools_from_metadata_cards():
    index_html = Path("webapp/static/index.html").read_text(encoding="utf-8")
    app_js = Path("webapp/static/js/app.js").read_text(encoding="utf-8")
    ui_js = Path("webapp/static/js/ui.js").read_text(encoding="utf-8")

    assert "工具参数" in index_html
    assert 'id="agent-tool-parameter-query"' in index_html
    assert "renderAgentTools(agentToolsListEl, state.agentTools, runAgentToolFromPanel)" in app_js
    assert "async function runAgentToolFromPanel" in app_js
    assert 'runAgentTool("project_overview", {})' in app_js
    assert 'runAgentTool("search_sources", { query })' in app_js
    assert "await refreshAgentToolRuns()" in app_js
    assert "renderAgentTools(toolsEl, tools, onRunTool = null)" in ui_js
    assert "data-tool-name" in ui_js
    assert "parameters_schema" in ui_js
    assert "运行" in ui_js
    assert "无参数" in ui_js
    assert "query" in ui_js


def test_answer_tool_suggestion_is_rendered_without_auto_running_tools():
    ui_js = Path("webapp/static/js/ui.js").read_text(encoding="utf-8")

    assert "tool_suggestion" in ui_js
    assert "建议工具" in ui_js
    assert "search_sources" in ui_js
    assert "runAgentTool(" not in ui_js


def test_answer_tool_suggestion_can_be_accepted_by_user_action():
    index_html = Path("webapp/static/index.html").read_text(encoding="utf-8")
    state_js = Path("webapp/static/js/state.js").read_text(encoding="utf-8")
    app_js = Path("webapp/static/js/app.js").read_text(encoding="utf-8")
    ui_js = Path("webapp/static/js/ui.js").read_text(encoding="utf-8")

    assert 'id="apply-tool-suggestion-button"' in index_html
    assert "currentToolSuggestion:" in state_js
    assert "renderToolSuggestionAction" in ui_js
    assert "clearToolSuggestion" in app_js
    assert "applyToolSuggestionButton.addEventListener" in app_js
    assert 'runAgentTool("search_sources"' in app_js
    assert "state.currentToolSuggestion.arguments" in app_js


def test_answer_request_can_be_cancelled_from_frontend():
    index_html = Path("webapp/static/index.html").read_text(encoding="utf-8")
    api_js = Path("webapp/static/js/api.js").read_text(encoding="utf-8")
    qa_js = Path("webapp/static/js/qa.js").read_text(encoding="utf-8")
    state_js = Path("webapp/static/js/state.js").read_text(encoding="utf-8")
    app_js = Path("webapp/static/js/app.js").read_text(encoding="utf-8")
    ui_js = Path("webapp/static/js/ui.js").read_text(encoding="utf-8")

    assert 'id="ask-cancel-button"' in index_html
    assert "currentAnswerAbortController:" in state_js
    assert "apiPost(path, payload, options = {})" in api_js
    assert "askStream(question" in qa_js
    assert "new EventSource" in qa_js
    assert "/api/answer/stream" in qa_js
    assert "addEventListener(\"token\"" in qa_js
    assert "addEventListener(\"done\"" in qa_js
    assert "source.close()" in qa_js
    assert "const askCancelButton" in app_js
    assert "renderStreamingAnswer" in ui_js
    assert "onToken" in app_js
    assert "askCancelButton.addEventListener" in app_js
    assert "state.currentAnswerAbortController.abort()" in app_js
    assert "AbortError" in app_js
    assert "已取消本次提问" in app_js


def test_dark_mode_theme_toggle_is_wired_and_persisted():
    index_html = Path("webapp/static/index.html").read_text(encoding="utf-8")
    app_js = Path("webapp/static/js/app.js").read_text(encoding="utf-8")
    styles_css = Path("webapp/static/styles.css").read_text(encoding="utf-8")

    assert 'id="theme-toggle-button"' in index_html
    assert "knowledge-island:theme" in app_js
    assert "localStorage.getItem(THEME_STORAGE_KEY)" in app_js
    assert "localStorage.setItem(THEME_STORAGE_KEY, theme)" in app_js
    assert "window.matchMedia(\"(prefers-color-scheme: dark)\")" in app_js
    assert "document.documentElement.dataset.theme = theme" in app_js
    assert "themeToggleButton.addEventListener" in app_js
    assert "@media (prefers-color-scheme: dark)" in styles_css
    assert ':root[data-theme="dark"]' in styles_css
    assert ':root[data-theme="light"]' in styles_css
    assert "--color-bg: #101418" in styles_css
    assert "color-scheme: dark" in styles_css


def test_recent_search_sources_run_can_be_used_as_next_answer_context():
    state_js = Path("webapp/static/js/state.js").read_text(encoding="utf-8")
    qa_js = Path("webapp/static/js/qa.js").read_text(encoding="utf-8")
    app_js = Path("webapp/static/js/app.js").read_text(encoding="utf-8")
    ui_js = Path("webapp/static/js/ui.js").read_text(encoding="utf-8")

    assert 'id="tool-context-notice"' in Path("webapp/static/index.html").read_text(encoding="utf-8")
    assert "currentToolContextRunId:" in state_js
    assert "tool_run_id" in qa_js
    assert "state.currentToolContextRunId" in app_js
    assert "renderToolContextNotice" in ui_js


def test_agent_tool_result_can_be_referenced_with_visible_run_id():
    index_html = Path("webapp/static/index.html").read_text(encoding="utf-8")
    app_js = Path("webapp/static/js/app.js").read_text(encoding="utf-8")
    ui_js = Path("webapp/static/js/ui.js").read_text(encoding="utf-8")

    assert 'id="use-tool-result-button"' in index_html
    assert "renderUseToolResultAction" in ui_js
    assert "使用工具结果作为下一问上下文" in ui_js
    assert "state.currentToolContextRunId = runId" in app_js
    assert "run.id" in ui_js
    assert "使用工具来源" in ui_js
    assert "consumeToolContext();" in app_js


def test_search_debug_panel_is_wired_to_rag_diagnostics():
    index_html = Path("webapp/static/index.html").read_text(encoding="utf-8")
    styles_css = Path("webapp/static/styles.css").read_text(encoding="utf-8")
    qa_js = Path("webapp/static/js/qa.js").read_text(encoding="utf-8")
    app_js = Path("webapp/static/js/app.js").read_text(encoding="utf-8")
    ui_js = Path("webapp/static/js/ui.js").read_text(encoding="utf-8")

    assert 'id="search-debug-button"' in index_html
    assert 'id="rag-top-k"' in index_html
    assert 'id="rag-min-score"' in index_html
    assert 'id="rag-use-vector"' in index_html
    assert 'id="search-debug-results"' in index_html
    assert 'apiPost("/api/search/debug"' in qa_js
    assert "searchDebug(" in app_js
    assert "renderSearchDebug" in ui_js
    assert "来源质量" in ui_js
    assert "source_quality" in ui_js
    assert "clearSearchDebug();" in app_js
    assert 'input[type="checkbox"]' in styles_css


def test_project_retrieval_settings_are_wired_to_debug_controls():
    index_html = Path("webapp/static/index.html").read_text(encoding="utf-8")
    qa_js = Path("webapp/static/js/qa.js").read_text(encoding="utf-8")
    state_js = Path("webapp/static/js/state.js").read_text(encoding="utf-8")
    app_js = Path("webapp/static/js/app.js").read_text(encoding="utf-8")

    assert 'id="save-rag-defaults-button"' in index_html
    assert 'id="rag-settings-status"' in index_html
    assert "getRetrievalSettings" in qa_js
    assert "saveRetrievalSettings" in qa_js
    assert "/api/projects/retrieval-settings" in qa_js
    assert "retrievalSettings:" in state_js


def test_prompt_preset_settings_are_wired():
    index_html = Path("webapp/static/index.html").read_text(encoding="utf-8")
    app_js = Path("webapp/static/js/app.js").read_text(encoding="utf-8")
    state_js = Path("webapp/static/js/state.js").read_text(encoding="utf-8")

    for marker in [
        'id="prompt-preset-form"',
        'id="prompt-preset-list"',
        'id="prompt-preset-template-list"',
        'id="prompt-preset-name"',
        'id="prompt-preset-system"',
        'id="prompt-preset-format"',
        'id="clear-default-prompt-preset-button"',
        'id="current-prompt-preset-label"',
    ]:
        assert marker in index_html
    for endpoint in [
        "/api/prompt-presets",
        "/api/prompt-presets/update",
        "/api/prompt-presets/delete",
        "/api/prompt-presets/default",
    ]:
        assert endpoint in app_js
    assert "promptPresets:" in state_js
    assert "promptPresetTemplates:" in state_js
    assert "selectedPromptPresetId:" in state_js
    assert "renderPromptPresetList" in app_js
    assert "copyPromptPresetTemplate" in app_js
    assert "refreshRetrievalSettings" in app_js
    assert "applyRetrievalSettingsToInputs" in app_js
    assert "saveRagDefaultsButton.addEventListener" in app_js


def test_plain_text_note_import_entrypoint_is_wired():
    index_html = Path("webapp/static/index.html").read_text(encoding="utf-8")
    projects_js = Path("webapp/static/js/projects.js").read_text(encoding="utf-8")
    app_js = Path("webapp/static/js/app.js").read_text(encoding="utf-8")

    assert 'id="note-title"' in index_html
    assert 'id="note-content"' in index_html
    assert 'id="note-import-button"' in index_html
    assert "importPlainTextNote" in projects_js
    assert 'apiPost("/api/import/note"' in projects_js
    assert "noteImportButton.addEventListener" in app_js


def test_clipboard_text_import_uses_existing_note_import_flow():
    index_html = Path("webapp/static/index.html").read_text(encoding="utf-8")
    app_js = Path("webapp/static/js/app.js").read_text(encoding="utf-8")

    assert 'id="clipboard-title"' in index_html
    assert 'id="clipboard-content"' in index_html
    assert 'id="clipboard-import-button"' in index_html
    assert "importPlainTextNote(clipboardTitleInput.value" in app_js
    assert "正在导入剪贴板文本" in app_js
    assert "clipboardContentInput.value = \"\"" in app_js


def test_url_excerpt_import_entrypoint_is_wired_without_auto_crawling():
    index_html = Path("webapp/static/index.html").read_text(encoding="utf-8")
    projects_js = Path("webapp/static/js/projects.js").read_text(encoding="utf-8")
    app_js = Path("webapp/static/js/app.js").read_text(encoding="utf-8")

    assert 'id="url-excerpt-url"' in index_html
    assert 'id="url-excerpt-title"' in index_html
    assert 'id="url-excerpt-content"' in index_html
    assert 'id="url-excerpt-import-button"' in index_html
    assert 'apiPost("/api/import/url"' in projects_js
    assert "importUrlExcerpt" in app_js
    assert "自动抓取" in index_html


def test_import_batch_history_entrypoint_is_wired_without_rollback_actions():
    index_html = Path("webapp/static/index.html").read_text(encoding="utf-8")
    projects_js = Path("webapp/static/js/projects.js").read_text(encoding="utf-8")
    state_js = Path("webapp/static/js/state.js").read_text(encoding="utf-8")
    app_js = Path("webapp/static/js/app.js").read_text(encoding="utf-8")
    ui_js = Path("webapp/static/js/ui.js").read_text(encoding="utf-8")

    assert 'id="import-batches"' in index_html
    assert 'id="import-batch-detail"' in index_html
    assert "importBatches:" in state_js
    assert "selectedImportBatch:" in state_js
    assert "listImportBatches" in projects_js
    assert "getImportBatchDetail" in projects_js
    assert "/api/import/batches" in projects_js
    assert "refreshImportBatches" in app_js
    assert "showImportBatchDetail" in app_js
    assert "renderImportBatches" in ui_js
    assert "renderImportBatchDetail" in ui_js
    import_batch_ui = index_html.split('id="import-batches"', 1)[1].split('id="import-batch-detail"', 1)[0]
    assert "回滚" not in import_batch_ui
    assert "删除批次" not in import_batch_ui
    assert "重试" not in import_batch_ui


def test_retrieval_review_entrypoint_is_wired():
    index_html = Path("webapp/static/index.html").read_text(encoding="utf-8")
    qa_js = Path("webapp/static/js/qa.js").read_text(encoding="utf-8")
    state_js = Path("webapp/static/js/state.js").read_text(encoding="utf-8")
    app_js = Path("webapp/static/js/app.js").read_text(encoding="utf-8")
    ui_js = Path("webapp/static/js/ui.js").read_text(encoding="utf-8")

    assert 'id="retrieval-review-note"' in index_html
    assert 'id="save-retrieval-review-button"' in index_html
    assert 'id="retrieval-reviews"' in index_html
    assert 'apiPost("/api/retrieval/reviews"' in qa_js
    assert 'apiGet(`/api/retrieval/reviews?' in qa_js
    assert "retrievalReviews:" in state_js
    assert "saveRetrievalReviewButton.addEventListener" in app_js
    assert "renderRetrievalReviews" in ui_js


def test_retrieval_review_detail_and_delete_entrypoints_are_wired():
    index_html = Path("webapp/static/index.html").read_text(encoding="utf-8")
    qa_js = Path("webapp/static/js/qa.js").read_text(encoding="utf-8")
    state_js = Path("webapp/static/js/state.js").read_text(encoding="utf-8")
    app_js = Path("webapp/static/js/app.js").read_text(encoding="utf-8")
    ui_js = Path("webapp/static/js/ui.js").read_text(encoding="utf-8")

    assert 'id="retrieval-review-detail"' in index_html
    assert "getRetrievalReviewDetail" in qa_js
    assert "/api/retrieval/reviews/detail?review_id=" in qa_js
    assert "deleteRetrievalReview" in qa_js
    assert 'apiPost("/api/retrieval/reviews/delete"' in qa_js
    assert "selectedRetrievalReview:" in state_js
    assert "retrievalReviewDetailEl" in app_js
    assert "showRetrievalReviewDetail" in app_js
    assert "removeRetrievalReview" in app_js
    assert "confirm(" in app_js
    assert "确认删除这条检索复盘" in app_js
    assert "setInlineErrorStatus(retrievalReviewDetailEl, error)" in app_js
    assert "renderRetrievalReviews(retrievalReviewsEl, state.retrievalReviews, showRetrievalReviewDetail, removeRetrievalReview)" in app_js
    assert "renderRetrievalReviewDetail" in ui_js
    assert "查看详情" in ui_js
    assert "删除" in ui_js
    assert "请选择一条检索复盘查看详情" in ui_js


def test_project_health_summary_panel_is_wired_to_existing_summary_api():
    index_html = Path("webapp/static/index.html").read_text(encoding="utf-8")
    projects_js = Path("webapp/static/js/projects.js").read_text(encoding="utf-8")
    state_js = Path("webapp/static/js/state.js").read_text(encoding="utf-8")
    app_js = Path("webapp/static/js/app.js").read_text(encoding="utf-8")
    ui_js = Path("webapp/static/js/ui.js").read_text(encoding="utf-8")

    assert 'id="project-health-summary"' in index_html
    assert 'id="project-health-status"' in index_html
    assert 'id="project-health-metrics"' in index_html
    assert 'id="retrieval-health-list"' in index_html
    assert "getProjectSummary" in projects_js
    assert 'apiGet(`/api/projects/summary?project_id=${encodeURIComponent(state.selectedProjectId)}`)' in projects_js
    assert "projectSummary:" in state_js
    assert "projectHealthStatusEl" in app_js
    assert "refreshProjectSummary" in app_js
    assert "renderProjectHealthSummary" in ui_js


def test_project_health_summary_does_not_request_without_selected_project():
    projects_js = Path("webapp/static/js/projects.js").read_text(encoding="utf-8")

    summary_block = projects_js.split("export async function getProjectSummary", 1)[1].split("export async function getDocument", 1)[0]
    assert "if (!state.selectedProjectId)" in summary_block
    assert "return { summary: null };" in summary_block
    assert summary_block.index("return { summary: null };") < summary_block.index("apiGet(")


def test_project_health_summary_failure_is_recoverable_and_does_not_block_lists():
    app_js = Path("webapp/static/js/app.js").read_text(encoding="utf-8")
    ui_js = Path("webapp/static/js/ui.js").read_text(encoding="utf-8")

    summary_block = app_js.split("async function refreshProjectSummary", 1)[1].split("function renderLlmSettings", 1)[0]
    assert "try {" in summary_block
    assert "catch (error)" in summary_block
    assert "setInlineErrorStatus(projectHealthStatusEl, error)" in summary_block
    assert "renderProjectHealthSummary(projectHealthMetricsEl, retrievalHealthListEl, null)" in summary_block
    assert "refreshProjectSummary();" in app_js
    assert "await refreshDocuments();" in app_js
    assert "健康概览读取失败" in ui_js


def test_project_health_summary_renders_required_counts_and_recent_activity():
    ui_js = Path("webapp/static/js/ui.js").read_text(encoding="utf-8")

    for label in [
        "文档数",
        "Chunk 数",
        "向量数",
        "聊天数",
        "工具运行数",
        "检索复盘数",
        "最近活动时间",
    ]:
        assert label in ui_js

    for field_name in [
        "document_count",
        "chunk_count",
        "vector_count",
        "chat_message_count",
        "agent_tool_run_count",
        "retrieval_review_count",
        "last_activity_at",
    ]:
        assert field_name in ui_js


def test_retrieval_health_is_derived_from_project_summary_only():
    ui_js = Path("webapp/static/js/ui.js").read_text(encoding="utf-8")

    assert "summary.chunk_count > 0" in ui_js
    assert "summary.vector_count > 0" in ui_js
    assert "summary.retrieval_review_count > 0" in ui_js
    assert "已生成 Chunk" in ui_js
    assert "已有向量" in ui_js
    assert "已有检索复盘" in ui_js
    assert "/api/retrieval/health" not in ui_js


def test_document_collections_panel_and_actions_are_wired():
    index_html = Path("webapp/static/index.html").read_text(encoding="utf-8")
    projects_js = Path("webapp/static/js/projects.js").read_text(encoding="utf-8")
    state_js = Path("webapp/static/js/state.js").read_text(encoding="utf-8")
    app_js = Path("webapp/static/js/app.js").read_text(encoding="utf-8")
    ui_js = Path("webapp/static/js/ui.js").read_text(encoding="utf-8")

    for element_id in [
        'id="document-collection-filter"',
        'id="document-collection-name"',
        'id="document-collection-create-button"',
        'id="document-collections"',
    ]:
        assert element_id in index_html
    for endpoint in [
        "/api/document-collections",
        "/api/document-collections/update",
        "/api/document-collections/delete",
        "/api/document-collections/items/add",
        "/api/document-collections/items/remove",
    ]:
        assert endpoint in projects_js
    assert "documentCollections:" in state_js
    assert "selectedDocumentCollectionId:" in state_js
    assert "refreshDocumentCollections" in app_js
    assert "documentCollectionFilterEl.addEventListener" in app_js
    assert "createDocumentCollectionButton.addEventListener" in app_js
    assert "addDocumentToCollection" in app_js
    assert "removeDocumentFromCollection" in app_js
    assert "renderDocumentCollections" in ui_js
    assert "加入集合" in ui_js
    assert "移出集合" in ui_js

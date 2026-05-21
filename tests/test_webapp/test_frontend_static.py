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
        "暂无跳过文件",
        "请选择左侧文件查看内容",
    ]:
        assert message in ui_js


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
    assert "暂无导入错误" in ui_js
    assert "importErrorsEl" in app_js
    assert "data.result.errors" in app_js


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

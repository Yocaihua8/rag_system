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

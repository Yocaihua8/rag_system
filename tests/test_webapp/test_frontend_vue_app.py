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

    assert 'currentView: "workbench"' in state_js
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


def test_vue_layout_components_define_four_primary_views():
    shell_vue = _read("frontend/src/components/AppShell.vue")
    app_vue = _read("frontend/src/App.vue")

    for view in ["workbench", "library", "assessment", "settings"]:
        assert f'data-view-key="{view}"' in shell_vue
    for label in ["工作台", "资料库", "评估", "设置"]:
        assert label in shell_vue

    for component_name in [
        "WorkbenchView",
        "LibraryView",
        "AssessmentView",
        "SettingsView",
    ]:
        assert component_name in app_vue

    assert "AppShell" in app_vue
    assert "currentViewComponent" in app_vue
    assert "computed" in app_vue


def test_vue_placeholder_views_keep_business_migration_boundary_explicit():
    view_files = {
        "frontend/src/views/WorkbenchView.vue": ["项目问答", "后续迁移问答、来源、Agent 工具和检索调试"],
        "frontend/src/views/AssessmentView.vue": ["评估", "后续迁移出题、作答、结果概览和待复测列表"],
        "frontend/src/views/SettingsView.vue": ["设置", "后续迁移模型设置、模型 Profile 和 Prompt 预设"],
    }

    for path, markers in view_files.items():
        view_text = _read(path)
        for marker in markers:
            assert marker in view_text
        assert "B-141B" in view_text

    library_vue = _read("frontend/src/views/LibraryView.vue")
    assert "资料库" in library_vue
    assert "ProjectSpacePanel" in library_vue
    assert "B-141C" in library_vue


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
    assert 'defineEmits(["refresh-projects", "select-project", "create-project"])' in panel_vue
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

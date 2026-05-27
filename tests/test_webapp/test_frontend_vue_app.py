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
    b141b_view_files = {
        "frontend/src/views/AssessmentView.vue": ["评估", "后续迁移出题、作答、结果概览和待复测列表"],
        "frontend/src/views/SettingsView.vue": ["设置", "后续迁移模型设置、模型 Profile 和 Prompt 预设"],
    }

    for path, markers in b141b_view_files.items():
        view_text = _read(path)
        for marker in markers:
            assert marker in view_text
        assert "B-141B" in view_text

    workbench_vue = _read("frontend/src/views/WorkbenchView.vue")
    assert "项目问答" in workbench_vue
    assert "B-141D 已迁移非流式问答入口" in workbench_vue
    assert "SSE、Agent 工具和检索调试后续迁移" in workbench_vue

    library_vue = _read("frontend/src/views/LibraryView.vue")
    assert "资料库" in library_vue
    assert "ProjectSpacePanel" in library_vue
    assert "B-141C" in library_vue
    assert "B-141C 至 B-141M" in library_vue


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


def test_vue_answer_api_helper_uses_existing_non_streaming_answer_contract():
    answer_js = _read("frontend/src/api/answer.js")

    assert "export async function askQuestion({ projectId, question })" in answer_js
    assert 'apiPost("/api/answer"' in answer_js
    assert "project_id: projectId" in answer_js
    assert "question" in answer_js
    assert "请先创建或选择项目空间" in answer_js
    assert "请输入问题" in answer_js


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
        "来源",
        "来源质量",
        "暂无来源",
        "mode",
        "provider",
    ]:
        assert marker in answer_panel_vue

    assert "QuestionPanel" in workbench_vue
    assert "AnswerPanel" in workbench_vue
    assert "@submit-question" in workbench_vue
    assert ":answer-result=\"answerResult\"" in workbench_vue


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
        'defineEmits(["refresh-documents", "select-document"])',
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
        'defineEmits(["import-note", "import-url", "import-files", "import-folder", "sync-directory", "preview-import"])',
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
        'defineEmits(["import-note", "import-url", "import-files", "import-folder", "sync-directory", "preview-import"])',
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
        'defineEmits(["import-note", "import-url", "import-files", "import-folder", "sync-directory", "preview-import"])',
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
        'defineEmits(["import-note", "import-url", "import-files", "import-folder", "sync-directory", "preview-import"])',
    ]:
        assert marker in panel_vue

    assert "@preview-import" in library_vue
    assert ":import-preview=\"importPreview\"" in library_vue
    assert ":import-preview-loading=\"importPreviewLoading\"" in library_vue
    assert ":import-preview-error=\"importPreviewError\"" in library_vue


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

    for forbidden_action in [
        "/api/document-collections/update",
        "/api/document-collections/items/add",
        "/api/document-collections/items/remove",
    ]:
        assert forbidden_action not in collections_js


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
        "deletingCollectionId",
        'defineEmits(["refresh-collections", "select-collection", "create-collection", "delete-collection"])',
    ]:
        assert marker in panel_vue

    for forbidden_action in ["重命名集合", "加入集合", "移出集合"]:
        assert forbidden_action not in panel_vue

    assert "DocumentCollectionPanel" in library_vue
    assert ":document-collections=\"documentCollections\"" in library_vue
    assert ":selected-document-collection-id=\"selectedDocumentCollectionId\"" in library_vue
    assert ":document-collections-loading=\"documentCollectionsLoading\"" in library_vue
    assert ":document-collections-load-error=\"documentCollectionsLoadError\"" in library_vue
    assert ":collection-form-submitting=\"collectionFormSubmitting\"" in library_vue
    assert ":collection-form-error=\"collectionFormError\"" in library_vue
    assert ":collection-form-status=\"collectionFormStatus\"" in library_vue
    assert ":deleting-collection-id=\"deletingCollectionId\"" in library_vue
    assert "@refresh-collections" in library_vue
    assert "@select-collection" in library_vue
    assert "@create-collection" in library_vue
    assert "@delete-collection" in library_vue


def test_vue_app_loads_document_collections_and_filters_document_list():
    app_vue = _read("frontend/src/App.vue")
    state_js = _read("frontend/src/state/app-state.js")

    assert "listDocumentCollections" in app_vue
    assert "createDocumentCollection" in app_vue
    assert "deleteDocumentCollection" in app_vue
    assert "loadDocumentCollections" in app_vue
    assert "handleSelectDocumentCollection" in app_vue
    assert "handleCreateDocumentCollection" in app_vue
    assert "handleDeleteDocumentCollection" in app_vue
    assert ":document-collections=\"appState.documentCollections\"" in app_vue
    assert ":selected-document-collection-id=\"appState.selectedDocumentCollectionId\"" in app_vue
    assert ":document-collections-loading=\"appState.documentCollectionsLoading\"" in app_vue
    assert ":document-collections-load-error=\"appState.documentCollectionsLoadError\"" in app_vue
    assert ":collection-form-submitting=\"appState.collectionFormSubmitting\"" in app_vue
    assert ":collection-form-error=\"appState.collectionFormError\"" in app_vue
    assert ":collection-form-status=\"appState.collectionFormStatus\"" in app_vue
    assert ":deleting-collection-id=\"appState.deletingCollectionId\"" in app_vue
    assert "@refresh-collections=\"loadDocumentCollections\"" in app_vue
    assert "@select-collection=\"handleSelectDocumentCollection\"" in app_vue
    assert "@create-collection=\"handleCreateDocumentCollection\"" in app_vue
    assert "@delete-collection=\"handleDeleteDocumentCollection\"" in app_vue
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
        "deletingCollectionId",
    ]:
        assert f"{state_field}:" in state_js

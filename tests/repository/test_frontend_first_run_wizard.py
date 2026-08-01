from pathlib import Path


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_first_run_wizard_component_renders_ollama_model_and_project_steps():
    wizard_path = Path("frontend/src/components/FirstRunWizard.vue")
    assert wizard_path.exists(), "B-148 should add a First-Run Wizard component"
    wizard_vue = _read(str(wizard_path))

    for marker in [
        "首次运行",
        "Ollama",
        "本地模型",
        "第一个知识库",
        "qwen2.5:3b",
        "qwen2.5:7b",
        "deepseek-r1:8b",
        "pull-ollama-model",
        "refresh-ollama-status",
        "create-project",
        "dismiss-first-run",
        "progressPercent",
        "projectForm",
    ]:
        assert marker in wizard_vue


def test_vue_app_wires_first_run_wizard_state_and_ollama_api():
    app_vue = _read("frontend/src/App.vue")
    state_js = _read("frontend/src/state/app-state.js")

    for marker in [
        'import { getOllamaStatus, pullOllamaModel } from "./api/ollama.js";',
        ":first-run-visible=\"firstRunWizardVisible\"",
        ":ollama-status=\"appState.ollamaStatus\"",
        ":ollama-status-loading=\"appState.ollamaStatusLoading\"",
        ":ollama-pull-progress=\"appState.ollamaPullProgress\"",
        "@refresh-ollama-status=\"loadOllamaStatus\"",
        "@pull-ollama-model=\"handlePullOllamaModel\"",
        "@dismiss-first-run=\"dismissFirstRunWizard\"",
        "firstRunWizardVisible",
        "loadOllamaStatus",
        "handlePullOllamaModel",
        "dismissFirstRunWizard",
        "formatOllamaPullStatus",
        "onProgress(data)",
        "onDone(data)",
        "onError(data)",
    ]:
        assert marker in app_vue

    for state_field in [
        "firstRunWizardDismissed",
        "ollamaStatus",
        "ollamaStatusLoading",
        "ollamaStatusError",
        "ollamaPullingModel",
        "ollamaPullProgress",
        "ollamaPullStatus",
        "ollamaPullError",
    ]:
        assert f"{state_field}:" in state_js


def test_vue_workbench_renders_first_run_wizard_entrypoint():
    workbench_vue = _read("frontend/src/views/WorkbenchView.vue")

    for marker in [
        "FirstRunWizard",
        "v-if=\"firstRunVisible\"",
        ":ollama-status=\"ollamaStatus\"",
        ":ollama-pull-progress=\"ollamaPullProgress\"",
        "@pull-ollama-model",
        "@create-project",
        "firstRunVisible",
        "ollamaStatus",
        "ollamaPullProgress",
        "dismiss-first-run",
    ]:
        assert marker in workbench_vue

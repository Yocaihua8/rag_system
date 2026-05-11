"""
settings_view.py — 设置面板。

分三个分组：
  1. 知识库  — 根目录路径
  2. LLM 提供商 — Ollama / 云端 API（OpenAI 兼容）
  3. Ollama 本地 — 地址、LLM 模型、Embedding 模型

安全机制：
  - API Key 检测到来自 OS 环境变量时，显示"已从环境变量读取"并禁用输入，
    防止用户在 UI 中意外覆盖更安全的配置。
  - API Key 输入框默认密文，右侧「显示」按钮切换明文。
"""
from __future__ import annotations

import os

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QButtonGroup, QDoubleSpinBox, QFileDialog, QFormLayout, QFrame,
    QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QRadioButton, QSpinBox, QVBoxLayout, QWidget,
)

from src.config.settings import AppSettings
from src.desktop.style import (
    ACCENT, BG_ELEVATED, BG_TERTIARY,
    BORDER, SUCCESS, TEXT_PRIMARY, TEXT_SECONDARY,
)

# OS 环境变量名
_ENV_API_KEY = "RAG_LLM_API_KEY"


def _section_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setStyleSheet(f"""
        font-size: 12px;
        font-weight: 600;
        color: {TEXT_SECONDARY};
        letter-spacing: 0.5px;
        padding: 4px 0 2px 0;
        background: transparent;
    """)
    return label


def _divider() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setStyleSheet(f"background-color: {BORDER}; max-height: 1px; border: none; margin: 6px 0;")
    return line


class SettingsView(QWidget):
    """设置面板：知识库路径、LLM 提供商、Ollama 配置。"""

    save_requested = Signal(dict)   # {field: value}

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._api_key_from_env = False
        self._show_api_key = False
        self._build_ui()

    # ── UI 构建 ───────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 20, 24, 20)
        outer.setSpacing(0)

        title = QLabel("设置")
        title.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {TEXT_PRIMARY}; padding-bottom: 16px; background: transparent;")
        outer.addWidget(title)

        # ── 1. 知识库 ──────────────────────────────────────────────────────
        outer.addWidget(_section_label("知识库"))
        outer.addWidget(_divider())

        form1 = QFormLayout()
        form1.setContentsMargins(0, 4, 0, 12)
        form1.setSpacing(8)
        kb_row = QHBoxLayout()
        self._kb_root = QLineEdit()
        btn_browse = QPushButton("浏览…")
        btn_browse.setFixedWidth(64)
        btn_browse.clicked.connect(self._browse_kb)
        kb_row.addWidget(self._kb_root)
        kb_row.addWidget(btn_browse)
        form1.addRow("根目录：", kb_row)
        outer.addLayout(form1)

        # ── 2. LLM 提供商 ──────────────────────────────────────────────────
        outer.addWidget(_section_label("LLM 提供商"))
        outer.addWidget(_divider())

        provider_row = QHBoxLayout()
        provider_row.setSpacing(16)
        self._radio_ollama = QRadioButton("本地 Ollama")
        self._radio_api = QRadioButton("云端 API（OpenAI 兼容）")
        self._radio_ollama.setStyleSheet(f"color: {TEXT_PRIMARY}; background: transparent;")
        self._radio_api.setStyleSheet(f"color: {TEXT_PRIMARY}; background: transparent;")
        self._llm_provider_group = QButtonGroup(self)
        self._llm_provider_group.addButton(self._radio_ollama, 0)
        self._llm_provider_group.addButton(self._radio_api, 1)
        provider_row.addWidget(self._radio_ollama)
        provider_row.addWidget(self._radio_api)
        provider_row.addStretch()
        outer.addLayout(provider_row)

        # 云端 API 配置面板（选中"云端 API"后展开）
        self._api_panel = QWidget()
        self._api_panel.setStyleSheet(f"""
            QWidget {{
                background-color: {BG_ELEVATED};
                border: 1px solid {BORDER};
                border-radius: 6px;
            }}
        """)
        api_layout = QFormLayout(self._api_panel)
        api_layout.setContentsMargins(14, 12, 14, 12)
        api_layout.setSpacing(10)

        # API 地址
        self._api_base = QLineEdit()
        self._api_base.setPlaceholderText("https://api.deepseek.com/v1")
        api_layout.addRow("API 地址：", self._api_base)

        # 快捷填充按钮
        presets_row = QHBoxLayout()
        presets = [
            ("DeepSeek",  "https://api.deepseek.com/v1"),
            ("OpenAI",    "https://api.openai.com/v1"),
            ("通义千问",   "https://dashscope.aliyuncs.com/compatible-mode/v1"),
            ("Kimi",      "https://api.moonshot.cn/v1"),
        ]
        for name, url in presets:
            btn = QPushButton(name)
            btn.setFixedHeight(24)
            btn.setStyleSheet(f"""
                QPushButton {{
                    font-size: 11px;
                    padding: 2px 8px;
                    background: {BG_TERTIARY};
                    border: 1px solid {BORDER};
                    border-radius: 4px;
                    color: {TEXT_SECONDARY};
                }}
                QPushButton:hover {{
                    color: {TEXT_PRIMARY};
                    border-color: {ACCENT};
                }}
            """)
            btn.clicked.connect(lambda _, u=url: self._api_base.setText(u))
            presets_row.addWidget(btn)
        presets_row.addStretch()
        api_layout.addRow("快捷填充：", presets_row)

        # API Key
        key_row = QHBoxLayout()
        self._api_key = QLineEdit()
        self._api_key.setEchoMode(QLineEdit.Password)
        self._api_key.setPlaceholderText("sk-...")
        self._btn_toggle_key = QPushButton("显示")
        self._btn_toggle_key.setFixedWidth(52)
        self._btn_toggle_key.clicked.connect(self._toggle_api_key_visibility)
        key_row.addWidget(self._api_key)
        key_row.addWidget(self._btn_toggle_key)

        # 环境变量安全提示
        self._env_key_label = QLabel(f"● 已从系统环境变量 {_ENV_API_KEY} 读取（安全）")
        self._env_key_label.setStyleSheet(f"""
            color: {SUCCESS};
            font-size: 12px;
            background: transparent;
            padding: 4px 0;
        """)
        self._env_key_label.setVisible(False)

        api_layout.addRow("API Key：", key_row)
        api_layout.addRow("", self._env_key_label)

        # 环境变量配置提示
        env_hint = QLabel(
            "安全提示：可通过系统环境变量传入 API Key，无需写入任何文件。\n"
            f"Windows：set {_ENV_API_KEY}=sk-xxx    macOS/Linux：export {_ENV_API_KEY}=sk-xxx"
        )
        env_hint.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px; background: transparent; padding-top: 4px;")
        env_hint.setWordWrap(True)
        api_layout.addRow("", env_hint)

        # 模型名称
        self._api_model = QLineEdit()
        self._api_model.setPlaceholderText("deepseek-chat")
        api_layout.addRow("模型名称：", self._api_model)

        outer.addSpacing(8)
        outer.addWidget(self._api_panel)

        # ── 3. 向量索引 ────────────────────────────────────────────────────
        outer.addSpacing(16)
        outer.addWidget(_section_label("向量索引"))
        outer.addWidget(_divider())

        embed_row = QHBoxLayout()
        embed_row.setSpacing(16)
        self._radio_embed_ollama = QRadioButton("本地 Ollama Embedding（向量检索）")
        self._radio_embed_none = QRadioButton("关键词检索（无需 Ollama）")
        self._radio_embed_ollama.setStyleSheet(f"color: {TEXT_PRIMARY}; background: transparent;")
        self._radio_embed_none.setStyleSheet(f"color: {TEXT_PRIMARY}; background: transparent;")
        self._embed_provider_group = QButtonGroup(self)
        self._embed_provider_group.addButton(self._radio_embed_ollama, 0)
        self._embed_provider_group.addButton(self._radio_embed_none, 1)
        embed_row.addWidget(self._radio_embed_ollama)
        embed_row.addWidget(self._radio_embed_none)
        embed_row.addStretch()
        outer.addLayout(embed_row)

        # ── 4. Ollama 本地配置 ─────────────────────────────────────────────
        outer.addSpacing(16)
        outer.addWidget(_section_label("Ollama 本地配置"))
        outer.addWidget(_divider())

        form2 = QFormLayout()
        form2.setContentsMargins(0, 4, 0, 12)
        form2.setSpacing(8)
        self._ollama_host = QLineEdit()
        self._ollama_host.setPlaceholderText("http://localhost:11434")
        form2.addRow("Ollama 地址：", self._ollama_host)
        self._ollama_model = QLineEdit()
        self._ollama_model.setPlaceholderText("qwen2.5:7b")
        form2.addRow("LLM 模型：", self._ollama_model)
        self._embed_model = QLineEdit()
        self._embed_model.setPlaceholderText("nomic-embed-text")
        form2.addRow("Embedding 模型：", self._embed_model)

        # P5: LLM 生成参数
        self._llm_temperature = QDoubleSpinBox()
        self._llm_temperature.setRange(0.0, 2.0)
        self._llm_temperature.setSingleStep(0.1)
        self._llm_temperature.setDecimals(1)
        self._llm_temperature.setToolTip("0.0 = 确定性输出；1.0 = 均衡；2.0 = 最大随机性")
        form2.addRow("温度（Temperature）：", self._llm_temperature)

        self._llm_max_tokens = QSpinBox()
        self._llm_max_tokens.setRange(256, 8192)
        self._llm_max_tokens.setSingleStep(256)
        self._llm_max_tokens.setToolTip("LLM 单次生成最大 Token 数")
        form2.addRow("最大生成 Token：", self._llm_max_tokens)

        outer.addLayout(form2)

        # ── 保存 ───────────────────────────────────────────────────────────
        outer.addSpacing(8)
        self._btn_save = QPushButton("保存设置")
        self._btn_save.setProperty("accent", "true")
        self._btn_save.style().unpolish(self._btn_save)
        self._btn_save.style().polish(self._btn_save)
        self._btn_save.clicked.connect(self._on_save)
        outer.addWidget(self._btn_save)

        restart_hint = QLabel("提示：修改 LLM 提供商或模型后，需重启应用生效。")
        restart_hint.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px; background: transparent; padding-top: 6px;")
        outer.addWidget(restart_hint)
        outer.addStretch()

        # 信号绑定
        self._radio_ollama.toggled.connect(self._on_provider_changed)
        self._radio_api.toggled.connect(self._on_provider_changed)

    # ── 数据加载 ──────────────────────────────────────────────────────────────

    def load_settings(self, s: AppSettings) -> None:
        self._kb_root.setText(str(s.kb_root))
        self._ollama_host.setText(s.ollama_host)
        self._ollama_model.setText(s.ollama_model)
        self._embed_model.setText(s.embedding_model)
        self._llm_temperature.setValue(s.llm_temperature)
        self._llm_max_tokens.setValue(s.llm_max_tokens)

        # LLM 提供商
        if s.llm_provider == "api":
            self._radio_api.setChecked(True)
        else:
            self._radio_ollama.setChecked(True)

        self._api_base.setText(s.llm_api_base)
        self._api_model.setText(s.llm_api_model)

        # 检测 API Key 来源
        self._api_key_from_env = bool(os.environ.get(_ENV_API_KEY))
        if self._api_key_from_env:
            self._api_key.setVisible(False)
            self._btn_toggle_key.setVisible(False)
            self._env_key_label.setVisible(True)
        else:
            self._api_key.setVisible(True)
            self._btn_toggle_key.setVisible(True)
            self._env_key_label.setVisible(False)
            if s.llm_api_key:
                self._api_key.setPlaceholderText("（已设置，留空则保留现有值）")
            else:
                self._api_key.setPlaceholderText("sk-...")

        # Embedding 提供商
        if s.embed_provider == "none":
            self._radio_embed_none.setChecked(True)
        else:
            self._radio_embed_ollama.setChecked(True)

        self._on_provider_changed()

    # ── 内部槽 ────────────────────────────────────────────────────────────────

    def _on_provider_changed(self) -> None:
        self._api_panel.setVisible(self._radio_api.isChecked())

    def _browse_kb(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "选择知识库根目录")
        if path:
            self._kb_root.setText(path)

    def _toggle_api_key_visibility(self) -> None:
        self._show_api_key = not self._show_api_key
        self._api_key.setEchoMode(
            QLineEdit.Normal if self._show_api_key else QLineEdit.Password
        )
        self._btn_toggle_key.setText("隐藏" if self._show_api_key else "显示")

    def _on_save(self) -> None:
        data: dict = {
            "kb_root":           self._kb_root.text().strip(),
            "ollama_host":       self._ollama_host.text().strip(),
            "ollama_model":      self._ollama_model.text().strip(),
            "embedding_model":   self._embed_model.text().strip(),
            "llm_provider":      "api" if self._radio_api.isChecked() else "ollama",
            "llm_api_base":      self._api_base.text().strip(),
            "llm_api_model":     self._api_model.text().strip(),
            "embed_provider":    "none" if self._radio_embed_none.isChecked() else "ollama",
            "llm_temperature":   self._llm_temperature.value(),
            "llm_max_tokens":    self._llm_max_tokens.value(),
        }
        # API Key：仅非环境变量来源且用户有输入时才写入
        if not self._api_key_from_env:
            key_input = self._api_key.text().strip()
            if key_input:
                data["llm_api_key"] = key_input

        self.save_requested.emit(data)

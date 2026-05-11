"""
guide_view.py — 使用指引页。

分步骤说明应用的完整使用流程，配合图标和说明文字。
首次启动时自动跳转到此页面。
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel,
    QScrollArea, QVBoxLayout, QWidget,
)

from src.desktop.style import (
    ACCENT, BG_SECONDARY, BG_ELEVATED,
    BORDER, TEXT_PRIMARY, TEXT_SECONDARY,
    SUCCESS, WARNING,
)


# ── 步骤数据 ─────────────────────────────────────────────────────────────────

_STEPS = [
    {
        "icon": "①",
        "title": "导入项目",
        "tag": "开始",
        "tag_color": ACCENT,
        "desc": (
            "选择一个代码项目目录。系统会读取 README、docs、源码、配置文件和测试文件。\n\n"
            "建议优先选择一个你正在学习或准备复盘的精简项目目录；"
            "自动过滤依赖目录和构建产物会在后续版本完善。"
        ),
    },
    {
        "icon": "②",
        "title": "建立索引",
        "tag": "知识库",
        "tag_color": WARNING,
        "desc": (
            "系统当前会整理项目文件、切分内容并建立检索索引。\n\n"
            "项目知识点提炼会在后续版本接入，届时可在知识库页查看识别结果。"
        ),
    },
    {
        "icon": "③",
        "title": "开始使用",
        "tag": "问答与评估",
        "tag_color": SUCCESS,
        "desc": (
            "你可以围绕当前项目提问，也可以点击开始评估。\n\n"
            "掌握评估目前先提供入口和页面骨架；自动出题、回答评估和建议阅读文件"
            "会在后续版本接入。"
        ),
    },
]


# ── 步骤卡片组件 ─────────────────────────────────────────────────────────────

class _StepCard(QFrame):

    def __init__(self, step: dict, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("stepCard")
        self.setStyleSheet(f"""
            QFrame#stepCard {{
                background-color: {BG_SECONDARY};
                border: 1px solid {BORDER};
                border-radius: 8px;
                padding: 0px;
            }}
        """)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 16, 20, 16)
        outer.setSpacing(10)

        # 标题行
        header = QHBoxLayout()
        icon_label = QLabel(step["icon"])
        icon_label.setStyleSheet(f"""
            font-size: 20px;
            color: {ACCENT};
            font-weight: bold;
            background: transparent;
            min-width: 28px;
        """)

        title_label = QLabel(step["title"])
        title_label.setStyleSheet(f"""
            font-size: 14px;
            font-weight: 600;
            color: {TEXT_PRIMARY};
            background: transparent;
        """)

        tag_label = QLabel(step["tag"])
        tag_color = step.get("tag_color", TEXT_SECONDARY)
        tag_label.setStyleSheet(f"""
            font-size: 11px;
            color: {tag_color};
            border: 1px solid {tag_color};
            border-radius: 10px;
            padding: 1px 8px;
            background: transparent;
        """)

        header.addWidget(icon_label)
        header.addWidget(title_label)
        header.addStretch()
        header.addWidget(tag_label)
        outer.addLayout(header)

        # 分割线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet(f"background-color: {BORDER}; max-height: 1px; border: none;")
        outer.addWidget(line)

        # 内容
        desc_label = QLabel(step["desc"])
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet(f"""
            font-size: 13px;
            color: {TEXT_SECONDARY};
            line-height: 1.7;
            background: transparent;
        """)
        desc_label.setTextFormat(Qt.PlainText)
        outer.addWidget(desc_label)


# ── 使用指引主视图 ────────────────────────────────────────────────────────────

class GuideView(QWidget):
    """使用指引页：分步骤介绍完整使用流程。"""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # 滚动区
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(32, 24, 32, 32)
        layout.setSpacing(16)

        # 页头
        header_widget = QWidget()
        header_widget.setStyleSheet(f"""
            background-color: {BG_ELEVATED};
            border-radius: 10px;
            padding: 4px;
        """)
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(24, 20, 24, 20)
        header_layout.setSpacing(6)

        title = QLabel("欢迎使用项目知识库")
        title.setStyleSheet(f"""
            font-size: 20px;
            font-weight: 700;
            color: {TEXT_PRIMARY};
            background: transparent;
        """)

        subtitle = QLabel(
            "导入你的代码项目后，系统会建立索引，帮助你围绕项目提问，"
            "掌握评估入口会在后续接入自动出题和能力差距报告。"
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet(f"""
            font-size: 13px;
            color: {TEXT_SECONDARY};
            line-height: 1.6;
            background: transparent;
        """)

        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        layout.addWidget(header_widget)

        # 步骤卡片
        for step in _STEPS:
            layout.addWidget(_StepCard(step))

        # 底部提示
        tip = QLabel("提示：随时可通过左侧底部的 ？ 按钮重新打开使用指引。")
        tip.setAlignment(Qt.AlignCenter)
        tip.setStyleSheet(f"""
            color: {TEXT_SECONDARY};
            font-size: 12px;
            padding: 8px 0 4px 0;
            background: transparent;
        """)
        layout.addWidget(tip)
        layout.addStretch()

        scroll.setWidget(container)
        root.addWidget(scroll)

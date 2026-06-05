"""
style.py — 全局 QSS 样式表（深色红系主题）。

设计基准：
  - 主红：#C63B57（hover #D94B68 / active #9E223C）
  - 背景：#111318 / #181C22 / #20252D / #2A303A
  - 文本：#EEF1F5 / #B6BFCA / #8A94A3 / #66707D
  - 边框：#2E3642 / #3A4452 / #272E38
"""
from __future__ import annotations

# ── 背景色板 ──────────────────────────────────────────────────────────────────

BG_PRIMARY = "#111318"      # 页面背景
BG_SECONDARY = "#181C22"    # surface
BG_TERTIARY = "#20252D"     # card
BG_ELEVATED = "#2A303A"     # elevated / hover
BG_SELECTED = "#2B1F25"     # 导航/列表选中背景

# ── 边框 ──────────────────────────────────────────────────────────────────────

BORDER = "#2E3642"
BORDER_FOCUS = "#C63B57"
BORDER_MUTED = "#272E38"
BORDER_SECONDARY = "#3A4452"

# ── 强调色（品牌红）────────────────────────────────────────────────────────────

ACCENT = "#C63B57"
ACCENT_HOVER = "#D94B68"
ACCENT_ACTIVE = "#9E223C"
TEXT_ACCENT = "#D94B68"

# ── 文本色 ────────────────────────────────────────────────────────────────────

TEXT_PRIMARY = "#EEF1F5"
TEXT_SECONDARY = "#B6BFCA"
TEXT_TERTIARY = "#8A94A3"
TEXT_DISABLED = "#66707D"

# ── 语义色 ────────────────────────────────────────────────────────────────────

SUCCESS = "#35B36F"
WARNING = "#E5A63B"
ERROR = "#E35D63"
INFO = "#4A90E2"

# ── 主按钮色（保持旧变量名以兼容其它模块）──────────────────────────────────────

BTN_PRIMARY_BG = ACCENT
BTN_PRIMARY_HOVER = ACCENT_HOVER
BTN_PRIMARY_PRESSED = ACCENT_ACTIVE


# ── 全局 QSS ─────────────────────────────────────────────────────────────────

def get_stylesheet() -> str:
    return f"""
/* ── 基础 ── */
QMainWindow, QDialog {{
    background-color: {BG_PRIMARY};
    color: {TEXT_PRIMARY};
}}

QWidget {{
    background-color: transparent;
    color: {TEXT_PRIMARY};
    font-family: "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
    font-size: 13px;
}}

/* ── 滚动区 ── */
QScrollArea {{
    border: none;
    background-color: transparent;
}}
QScrollBar:vertical {{
    background: {BG_SECONDARY};
    width: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: {BORDER_SECONDARY};
    border-radius: 4px;
    min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{
    background: {ACCENT};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{
    background: {BG_SECONDARY};
    height: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:horizontal {{
    background: {BORDER_SECONDARY};
    border-radius: 4px;
    min-width: 24px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {ACCENT};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}

/* ── 分割器 ── */
QSplitter::handle {{
    background: {BORDER_MUTED};
}}
QSplitter::handle:horizontal {{ width: 1px; }}
QSplitter::handle:vertical {{ height: 1px; }}

/* ── 标签页 ── */
QTabWidget::pane {{
    border: 1px solid {BORDER};
    border-radius: 8px;
    background-color: {BG_SECONDARY};
    top: -1px;
}}
QTabBar::tab {{
    background: {BG_TERTIARY};
    color: {TEXT_SECONDARY};
    padding: 7px 16px;
    border: 1px solid {BORDER};
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
}}
QTabBar::tab:selected {{
    background: {BG_SECONDARY};
    color: {TEXT_PRIMARY};
    border-bottom: 2px solid {ACCENT};
}}
QTabBar::tab:hover:!selected {{
    background: {BG_ELEVATED};
    color: {TEXT_PRIMARY};
}}

/* ── 列表 / 树 / 表格 ── */
QListWidget, QTreeWidget, QTableView {{
    background-color: {BG_TERTIARY};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 2px;
    outline: none;
    color: {TEXT_PRIMARY};
    gridline-color: {BORDER_MUTED};
}}
QListWidget::item, QTreeWidget::item, QTableView::item {{
    padding: 7px 10px;
    border-radius: 4px;
}}
QListWidget::item:hover, QTreeWidget::item:hover, QTableView::item:hover {{
    background-color: {BG_ELEVATED};
}}
QListWidget::item:selected, QTreeWidget::item:selected, QTableView::item:selected {{
    background-color: {BG_SELECTED};
    color: {TEXT_PRIMARY};
    border-left: 2px solid {ACCENT};
}}
QHeaderView::section {{
    background-color: {BG_SECONDARY};
    color: {TEXT_SECONDARY};
    border: none;
    border-bottom: 1px solid {BORDER};
    padding: 6px 8px;
    font-weight: 600;
}}

/* ── 按钮（次要） ── */
QPushButton {{
    background-color: {BG_TERTIARY};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_SECONDARY};
    border-radius: 8px;
    padding: 6px 14px;
    min-height: 28px;
}}
QPushButton:hover {{
    background-color: {BG_ELEVATED};
    border-color: {ACCENT};
}}
QPushButton:pressed {{
    background-color: {BG_SECONDARY};
}}
QPushButton:disabled {{
    color: {TEXT_DISABLED};
    border-color: {BORDER_MUTED};
}}

/* 主按钮 */
QPushButton[primary="true"] {{
    background-color: {BTN_PRIMARY_BG};
    border-color: {BTN_PRIMARY_BG};
    color: #FFFFFF;
    font-weight: 600;
}}
QPushButton[primary="true"]:hover {{
    background-color: {BTN_PRIMARY_HOVER};
    border-color: {BTN_PRIMARY_HOVER};
}}
QPushButton[primary="true"]:pressed {{
    background-color: {BTN_PRIMARY_PRESSED};
    border-color: {BTN_PRIMARY_PRESSED};
}}

/* 文字按钮 / 细强调 */
QPushButton[accent="true"] {{
    background-color: transparent;
    border: 1px solid {ACCENT};
    color: {TEXT_ACCENT};
}}
QPushButton[accent="true"]:hover {{
    background-color: rgba(198, 59, 87, 0.12);
    border-color: {ACCENT_HOVER};
    color: {ACCENT_HOVER};
}}

/* ── 导航按钮（左侧栏） ── */
QPushButton[nav="true"] {{
    background-color: transparent;
    border: none;
    border-radius: 8px;
    padding: 8px 12px;
    text-align: left;
    color: {TEXT_SECONDARY};
}}
QPushButton[nav="true"]:hover {{
    background-color: {BG_ELEVATED};
    color: {TEXT_PRIMARY};
}}
QPushButton[nav="true"]:checked {{
    background-color: {BG_SELECTED};
    color: #FFFFFF;
    border-left: 2px solid {ACCENT};
    padding-left: 10px;
}}

/* ── 输入框 ── */
QLineEdit {{
    background-color: {BG_SECONDARY};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 6px 10px;
    color: {TEXT_PRIMARY};
    selection-background-color: rgba(198, 59, 87, 0.25);
}}
QLineEdit:focus {{
    border-color: {BORDER_FOCUS};
    background-color: {BG_SECONDARY};
}}
QLineEdit:disabled {{
    color: {TEXT_DISABLED};
    background-color: {BG_PRIMARY};
}}
QLineEdit[readOnly="true"] {{
    background-color: {BG_PRIMARY};
    color: {TEXT_SECONDARY};
}}

/* ── 文本编辑框 ── */
QTextEdit {{
    background-color: {BG_TERTIARY};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 8px;
    color: {TEXT_PRIMARY};
    selection-background-color: rgba(198, 59, 87, 0.25);
    line-height: 1.5;
}}
QTextEdit:focus {{
    border-color: {BORDER_FOCUS};
}}

/* ── 标签 ── */
QLabel {{
    color: {TEXT_PRIMARY};
    background: transparent;
}}
QLabel[secondary="true"] {{
    color: {TEXT_SECONDARY};
    font-size: 12px;
}}
QLabel[title="true"] {{
    font-size: 17px;
    font-weight: 700;
    color: {TEXT_PRIMARY};
    padding: 4px 0 8px 0;
}}
QLabel[section="true"] {{
    font-size: 12px;
    font-weight: 600;
    color: {TEXT_TERTIARY};
    letter-spacing: 0.4px;
}}

/* ── 进度条 ── */
QProgressBar {{
    background-color: {BG_SECONDARY};
    border: 1px solid {BORDER};
    border-radius: 4px;
    height: 6px;
    text-align: center;
    color: transparent;
}}
QProgressBar::chunk {{
    background-color: {ACCENT};
    border-radius: 3px;
}}

/* ── 状态栏 ── */
QStatusBar {{
    background-color: {BG_SECONDARY};
    border-top: 1px solid {BORDER};
    color: {TEXT_SECONDARY};
    font-size: 12px;
    padding: 2px 8px;
}}
QStatusBar QLabel {{
    color: {TEXT_SECONDARY};
    font-size: 12px;
}}

/* ── 对话框 / 消息框 ── */
QDialog, QMessageBox {{
    background-color: {BG_SECONDARY};
    border: 1px solid {BORDER};
    border-radius: 8px;
}}
QDialogButtonBox QPushButton {{
    min-width: 80px;
}}
QMessageBox QLabel {{
    color: {TEXT_PRIMARY};
}}

/* ── 下拉框 ── */
QComboBox {{
    background-color: {BG_SECONDARY};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 5px 10px;
    color: {TEXT_PRIMARY};
}}
QComboBox:focus {{
    border-color: {BORDER_FOCUS};
}}
QComboBox::drop-down {{
    border: none;
    width: 20px;
}}
QComboBox QAbstractItemView {{
    background-color: {BG_TERTIARY};
    border: 1px solid {BORDER};
    border-radius: 8px;
    selection-background-color: {BG_ELEVATED};
    color: {TEXT_PRIMARY};
    outline: none;
}}

/* ── 单选按钮 ── */
QRadioButton {{
    color: {TEXT_PRIMARY};
    background: transparent;
    spacing: 6px;
}}
QRadioButton::indicator {{
    width: 14px;
    height: 14px;
    border-radius: 7px;
    border: 2px solid {BORDER};
    background: {BG_SECONDARY};
}}
QRadioButton::indicator:checked {{
    border-color: {ACCENT};
    background: {ACCENT};
}}
QRadioButton::indicator:hover {{
    border-color: {ACCENT_HOVER};
}}

/* ── 侧边栏：深色背景渐变 ── */
QWidget#sidebar {{
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #15181E,
        stop:1 {BG_PRIMARY}
    );
    border-right: 1px solid {BORDER};
}}

/* ── 内容区 ── */
QWidget#content {{
    background-color: {BG_PRIMARY};
}}

/* ── 分割线 ── */
QFrame[frameShape="4"],
QFrame[frameShape="5"] {{
    color: {BORDER_MUTED};
    background-color: {BORDER_MUTED};
    border: none;
    max-height: 1px;
}}
"""

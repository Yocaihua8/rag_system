"""
bootstrap.py — 应用启动序列。

顺序：
  1. load_settings()           加载配置（消灭硬编码路径）
  2. ensure_runtime_dirs()     创建运行时目录
  3. 首次运行检测               kb_root 不存在则提示
  4. AppContainer.build()      组装所有依赖
  5. MainWindow(container)     启动 UI
"""
from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from src.config.paths import ensure_runtime_dirs
from src.config.settings import load_settings
from src.application.container import AppContainer
from src.desktop.views.main_window import MainWindow


def run() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("Career Assistant")
    app.setOrganizationName("CareerAssistant")

    # ① 加载配置
    settings = load_settings()
    ensure_runtime_dirs(settings)

    # ② 首次运行检测（kb_root 不存在）
    if not settings.kb_root.exists():
        reply = QMessageBox.question(
            None,
            "首次运行",
            f"知识库目录不存在：\n{settings.kb_root}\n\n是否自动创建？",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            settings.kb_root.mkdir(parents=True, exist_ok=True)
        else:
            QMessageBox.information(
                None, "提示",
                "请在设置页面配置正确的知识库目录路径，然后重启应用。"
            )

    # ③ 构建容器（keyword 模式跳过 Ollama 检查）
    try:
        container = AppContainer.build(settings)
    except Exception as exc:
        QMessageBox.critical(None, "启动失败", f"初始化失败：{exc}\n\n请检查配置后重试。")
        return 1

    # ④ Ollama 可用性提示（非阻断）
    if not container.llm_client.is_available():
        QMessageBox.warning(
            None, "Ollama 未运行",
            "未检测到 Ollama 服务。\n\n"
            "问答和生成功能将不可用，但知识库索引仍可正常使用。\n\n"
            "请运行：ollama serve"
        )

    # ⑤ 启动主窗口
    window = MainWindow(container)
    window.show()
    return app.exec()

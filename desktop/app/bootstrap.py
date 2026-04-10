from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from desktop.app.startup_checks import run_startup_checks
from desktop.ui.main_window import MainWindow


def run() -> int:
    run_startup_checks()
    app = QApplication.instance() or QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


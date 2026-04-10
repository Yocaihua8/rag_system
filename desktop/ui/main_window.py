from __future__ import annotations

from PySide6.QtWidgets import QLabel, QMainWindow, QVBoxLayout, QWidget


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("RAG System Desktop")
        self.resize(1000, 680)

        container = QWidget(self)
        layout = QVBoxLayout(container)
        layout.addWidget(QLabel("Desktop Shell Ready"))
        self.setCentralWidget(container)


from __future__ import annotations

from PySide6.QtWidgets import QDialog, QLabel, QVBoxLayout


class OnboardingWizard(QDialog):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Onboarding")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Welcome to RAG System Desktop"))


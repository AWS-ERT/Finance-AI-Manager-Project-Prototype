from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QTextEdit,
    QPushButton,
    QMessageBox,
)

from backend.ai_service import ask_claude


class ClaudeWorker(QThread):
    finished = Signal(str)
    failed = Signal(str)

    def __init__(self, question: str):
        super().__init__()
        self.question = question

    def run(self):
        try:
            answer = ask_claude(self.question)
            self.finished.emit(answer)
        except Exception as error:
            self.failed.emit(str(error))


class AssistantTab(QWidget):
    def __init__(self):
        super().__init__()

        self.worker = None

        layout = QVBoxLayout()

        title = QLabel("Claude Financial Assistant")
        title.setStyleSheet(
            "font-size: 22px; font-weight: bold; margin-bottom: 8px;"
        )

        instructions = QLabel(
            "Ask Claude questions about the financial data stored in your app."
        )

        self.question_box = QTextEdit()
        self.question_box.setPlaceholderText(
            "Example: Where am I spending the most money?"
        )
        self.question_box.setMaximumHeight(120)

        self.ask_button = QPushButton("Ask Claude")
        self.ask_button.clicked.connect(self.ask_question)

        self.response_box = QTextEdit()
        self.response_box.setReadOnly(True)
        self.response_box.setPlaceholderText(
            "Claude's response will appear here."
        )

        layout.addWidget(title)
        layout.addWidget(instructions)
        layout.addWidget(self.question_box)
        layout.addWidget(self.ask_button)
        layout.addWidget(self.response_box)

        self.setLayout(layout)

    def ask_question(self):
        question = self.question_box.toPlainText().strip()

        if not question:
            QMessageBox.warning(
                self,
                "Missing Question",
                "Please enter a question first.",
            )
            return

        self.ask_button.setEnabled(False)
        self.ask_button.setText("Claude is thinking...")
        self.response_box.setPlainText("Analyzing your financial data...")

        self.worker = ClaudeWorker(question)
        self.worker.finished.connect(self.show_answer)
        self.worker.failed.connect(self.show_error)
        self.worker.start()

    def show_answer(self, answer: str):
        self.response_box.setPlainText(answer)
        self.ask_button.setEnabled(True)
        self.ask_button.setText("Ask Claude")
        self.worker = None

    def show_error(self, error_message: str):
        self.response_box.clear()

        QMessageBox.critical(
            self,
            "Claude Error",
            error_message,
        )

        self.ask_button.setEnabled(True)
        self.ask_button.setText("Ask Claude")
        self.worker = None
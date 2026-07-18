from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QTextEdit,
    QPushButton,
    QMessageBox,
)

from backend.ai_service import ask_budget_claude


class BudgetWorker(QThread):
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, question):
        super().__init__()
        self.question = question

    def run(self):
        try:
            answer = ask_budget_claude(self.question)
            self.finished.emit(answer)
        except Exception as e:
            self.error.emit(str(e))


class BudgetAssistantTab(QWidget):
    def __init__(self):
        super().__init__()

        self.worker = None

        layout = QVBoxLayout()

        title = QLabel("Budget AI Assistant")
        title.setStyleSheet(
            "font-size:22px; font-weight:bold;"
        )

        instructions = QLabel(
            "Ask questions about your income, expenses, savings, and budget."
        )

        self.question_box = QTextEdit()
        self.question_box.setPlaceholderText(
            "Example: How can I reduce my monthly spending?"
        )
        self.question_box.setMaximumHeight(120)

        self.ask_button = QPushButton("Ask Claude")
        self.ask_button.clicked.connect(self.ask_question)

        self.response_box = QTextEdit()
        self.response_box.setReadOnly(True)

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
                "Please enter a question first."
            )
            return

        self.ask_button.setEnabled(False)
        self.ask_button.setText("Thinking...")

        self.worker = BudgetWorker(question)
        self.worker.finished.connect(self.show_answer)
        self.worker.error.connect(self.show_error)
        self.worker.start()

    def show_answer(self, answer):
        self.response_box.setPlainText(answer)
        self.ask_button.setEnabled(True)
        self.ask_button.setText("Ask Claude")

    def show_error(self, message):
        QMessageBox.critical(
            self,
            "Claude Error",
            message
        )
        self.ask_button.setEnabled(True)
        self.ask_button.setText("Ask Claude")
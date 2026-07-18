from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QLabel,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from backend.ai_service import ask_investment_claude


class InvestmentWorker(QThread):
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, question: str):
        super().__init__()
        self.question = question

    def run(self) -> None:
        try:
            answer = ask_investment_claude(self.question)
            self.finished.emit(answer)
        except Exception as error:
            self.error.emit(str(error))


class InvestmentAssistantTab(QWidget):
    def __init__(self):
        super().__init__()

        self.worker = None

        layout = QVBoxLayout()

        title = QLabel("Investment AI Assistant")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")

        instructions = QLabel(
            "Ask questions about investing, diversification, risk, "
            "portfolio planning, and long-term goals."
        )
        instructions.setWordWrap(True)

        self.question_box = QTextEdit()
        self.question_box.setPlaceholderText(
            "Example: How can I make my portfolio more diversified?"
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

    def ask_question(self) -> None:
        question = self.question_box.toPlainText().strip()

        if not question:
            QMessageBox.warning(
                self,
                "Missing Question",
                "Please enter an investment question first.",
            )
            return

        self.ask_button.setEnabled(False)
        self.ask_button.setText("Thinking...")
        self.response_box.setPlainText("Claude is analyzing your question...")

        self.worker = InvestmentWorker(question)
        self.worker.finished.connect(self.show_answer)
        self.worker.error.connect(self.show_error)
        self.worker.start()

    def show_answer(self, answer: str) -> None:
        self.response_box.setPlainText(answer)
        self.ask_button.setEnabled(True)
        self.ask_button.setText("Ask Claude")

    def show_error(self, message: str) -> None:
        self.response_box.clear()

        print(message)

        QMessageBox.critical(self,"Claude Error", message,)

        self.ask_button.setEnabled(True)
        self.ask_button.setText("Ask Claude")
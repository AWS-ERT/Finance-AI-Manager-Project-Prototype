from PySide6.QtWidgets import QHBoxLayout, QWidget

from ui.investment_assistant import InvestmentAssistantTab
from ui.investments import InvestmentsTab


class InvestmentsWithAITab(QWidget):
    def __init__(self):
        super().__init__()

        layout = QHBoxLayout()

        investments = InvestmentsTab()
        investment_ai = InvestmentAssistantTab()

        layout.addWidget(investments, 3)
        layout.addWidget(investment_ai, 1)

        self.setLayout(layout)
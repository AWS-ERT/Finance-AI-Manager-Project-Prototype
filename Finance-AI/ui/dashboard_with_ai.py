from PySide6.QtWidgets import QHBoxLayout, QWidget

from ui.budget_assistant import BudgetAssistantTab
from ui.dashboard import DashboardTab


class DashboardWithAITab(QWidget):
    def __init__(self):
        super().__init__()

        layout = QHBoxLayout()

        dashboard = DashboardTab()
        budget_ai = BudgetAssistantTab()

        layout.addWidget(dashboard, 3)
        layout.addWidget(budget_ai, 1)

        self.setLayout(layout)

import sys

from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from backend.database import create_tables
from ui.analytics import AnalyticsTab
from ui.dashboard_with_ai import DashboardWithAITab
from ui.investments_with_ai import InvestmentsWithAITab


def main() -> None:
    create_tables()

    app = QApplication(sys.argv)

    window = QWidget()
    window.setWindowTitle("AI Financial Manager")
    window.resize(1200, 750)

    title = QLabel("AI Financial Manager")
    title.setStyleSheet(
        "font-size: 28px; "
        "font-weight: bold; "
        "margin-bottom: 8px;"
    )

    tabs = QTabWidget()

    tabs.addTab(
        DashboardWithAITab(),
        "Dashboard & Transactions",
    )

    tabs.addTab(
        InvestmentsWithAITab(),
        "Investments",
    )

    tabs.addTab(
        AnalyticsTab(),
        "Analytics",
    )

    layout = QVBoxLayout()
    layout.addWidget(title)
    layout.addWidget(tabs)

    window.setLayout(layout)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
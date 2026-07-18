from PySide6.QtCharts import (
    QChart,
    QChartView,
    QPieSeries,
)

from PySide6.QtGui import QPainter

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QListWidget,
)

from backend.database import get_spending_by_category


class AnalyticsTab(QWidget):
    def __init__(self):
        super().__init__()

        title = QLabel("Spending Analytics")
        title.setStyleSheet(
            "font-size: 22px; font-weight: bold;"
        )

        self.total_expenses_label = QLabel(
            "Total categorized expenses: $0.00"
        )

        self.category_list = QListWidget()

        self.chart = QChart()
        self.chart.setTitle("Expenses by Category")
        self.chart.legend().setVisible(True)

        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.Antialiasing)

        refresh_button = QPushButton("Refresh Analytics")
        refresh_button.clicked.connect(self.refresh)

        layout = QVBoxLayout()
        layout.addWidget(title)
        layout.addWidget(self.total_expenses_label)
        layout.addWidget(self.chart_view)
        layout.addWidget(self.category_list)
        layout.addWidget(refresh_button)

        self.setLayout(layout)

        self.refresh()

    def refresh(self):
        category_data = get_spending_by_category()

        self.category_list.clear()
        self.chart.removeAllSeries()

        pie_series = QPieSeries()
        total_expenses = 0

        for item in category_data:
            category = item["category"]
            total = item["total"]

            total_expenses += total

            pie_slice = pie_series.append(
                category,
                total
            )

            pie_slice.setLabel(
                f"{category}: ${total:,.2f}"
            )

            pie_slice.setLabelVisible(True)

            self.category_list.addItem(
                f"{category}: ${total:,.2f}"
            )

        self.total_expenses_label.setText(
            f"Total categorized expenses: "
            f"${total_expenses:,.2f}"
        )

        if category_data:
            self.chart.addSeries(pie_series)
            self.chart.setTitle("Expenses by Category")
        else:
            self.chart.setTitle(
                "Add expense transactions to see analytics"
            )
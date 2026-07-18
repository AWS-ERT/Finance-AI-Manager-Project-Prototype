from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QListWidget,
    QLineEdit,
    QMessageBox,
    QFrame,
)

from backend.database import (
    add_investment as db_add_investment,
    get_investments,
    delete_investment as db_delete_investment,
    get_investment_summary,
)


def create_summary_card(title_text):
    card = QFrame()
    card.setStyleSheet(
        """
        QFrame {
            border: 1px solid #999999;
            border-radius: 8px;
            padding: 12px;
        }
        """
    )

    title = QLabel(title_text)
    value = QLabel("$0.00")
    value.setStyleSheet("font-size: 22px; font-weight: bold;")

    layout = QVBoxLayout()
    layout.addWidget(title)
    layout.addWidget(value)
    card.setLayout(layout)

    return card, value


class InvestmentsTab(QWidget):
    def __init__(self):
        super().__init__()

        self.displayed_investments = []

        portfolio_card, self.portfolio_value_label = create_summary_card(
            "Portfolio Value"
        )
        invested_card, self.invested_amount_label = create_summary_card(
            "Amount Invested"
        )
        profit_card, self.profit_label = create_summary_card(
            "Total Profit/Loss"
        )

        cards_layout = QHBoxLayout()
        cards_layout.addWidget(portfolio_card)
        cards_layout.addWidget(invested_card)
        cards_layout.addWidget(profit_card)

        heading = QLabel("Investment Holdings")
        heading.setStyleSheet("font-size: 20px; font-weight: bold;")

        self.investment_list = QListWidget()

        self.symbol_input = QLineEdit()
        self.symbol_input.setPlaceholderText("Symbol, such as VOO")

        self.shares_input = QLineEdit()
        self.shares_input.setPlaceholderText("Shares")

        self.purchase_price_input = QLineEdit()
        self.purchase_price_input.setPlaceholderText(
            "Purchase price per share"
        )

        self.current_price_input = QLineEdit()
        self.current_price_input.setPlaceholderText(
            "Current price per share"
        )

        form = QFormLayout()
        form.addRow("Symbol:", self.symbol_input)
        form.addRow("Shares:", self.shares_input)
        form.addRow("Purchase price:", self.purchase_price_input)
        form.addRow("Current price:", self.current_price_input)

        add_button = QPushButton("Add Investment")
        add_button.clicked.connect(self.add_investment)

        remove_button = QPushButton("Remove Selected Investment")
        remove_button.clicked.connect(self.remove_investment)

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(add_button)
        buttons_layout.addWidget(remove_button)

        layout = QVBoxLayout()
        layout.addLayout(cards_layout)
        layout.addWidget(heading)
        layout.addWidget(self.investment_list)
        layout.addLayout(form)
        layout.addLayout(buttons_layout)

        self.setLayout(layout)

        self.refresh()

    def refresh(self):
        self.display_investments()
        self.update_summary()

    def display_investments(self):
        self.investment_list.clear()
        self.displayed_investments = get_investments()

        for investment in self.displayed_investments:
            shares = float(investment["shares"])
            purchase_price = float(investment["purchase_price"])
            current_price = float(investment["current_price"])

            current_value = shares * current_price
            total_cost = shares * purchase_price
            profit_loss = current_value - total_cost

            if profit_loss >= 0:
                profit_text = f"+${profit_loss:,.2f}"
            else:
                profit_text = f"-${abs(profit_loss):,.2f}"

            self.investment_list.addItem(
                f"{investment['symbol']} | "
                f"{shares:g} shares | "
                f"Value: ${current_value:,.2f} | "
                f"Profit/Loss: {profit_text}"
            )

    def update_summary(self):
        summary = get_investment_summary()

        self.portfolio_value_label.setText(
            f"${summary['portfolio_value']:,.2f}"
        )
        self.invested_amount_label.setText(
            f"${summary['cost_basis']:,.2f}"
        )

        profit_loss = summary["profit_loss"]

        if profit_loss >= 0:
            self.profit_label.setText(f"+${profit_loss:,.2f}")
        else:
            self.profit_label.setText(f"-${abs(profit_loss):,.2f}")

    def add_investment(self):
        symbol = self.symbol_input.text().strip().upper()
        shares_text = self.shares_input.text().strip()
        purchase_price_text = self.purchase_price_input.text().strip()
        current_price_text = self.current_price_input.text().strip()

        if (
            not symbol
            or not shares_text
            or not purchase_price_text
            or not current_price_text
        ):
            QMessageBox.warning(
                self,
                "Missing Information",
                "Complete every investment field.",
            )
            return

        try:
            db_add_investment(
                symbol=symbol,
                shares=float(shares_text),
                purchase_price=float(purchase_price_text),
                current_price=float(current_price_text),
            )

        except ValueError as error:
            QMessageBox.warning(self, "Invalid Investment", str(error))
            return

        except Exception as error:
            QMessageBox.critical(
                self,
                "Database Error",
                f"The investment could not be saved.\n\n{error}",
            )
            return

        self.symbol_input.clear()
        self.shares_input.clear()
        self.purchase_price_input.clear()
        self.current_price_input.clear()

        self.refresh()

    def remove_investment(self):
        selected_row = self.investment_list.currentRow()

        if selected_row == -1:
            QMessageBox.warning(
                self,
                "No Selection",
                "Select an investment before removing it.",
            )
            return

        selected_investment = self.displayed_investments[selected_row]

        confirmation = QMessageBox.question(
            self,
            "Remove Investment",
            f"Remove {selected_investment['symbol']}?",
            QMessageBox.Yes | QMessageBox.No,
        )

        if confirmation != QMessageBox.Yes:
            return

        try:
            db_delete_investment(selected_investment["id"])

        except Exception as error:
            QMessageBox.critical(
                self,
                "Database Error",
                f"The investment could not be removed.\n\n{error}",
            )
            return

        self.refresh()

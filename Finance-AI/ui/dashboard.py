from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from backend.csv_importer import (
    BankCSVImportError,
    import_bank_csv,
)
from backend.database import (
    add_transaction,
    delete_transaction,
    get_financial_summary,
    get_transactions,
)


class DashboardTab(QWidget):
    def __init__(self):
        super().__init__()

        self.setup_ui()
        self.refresh_dashboard()

    def setup_ui(self) -> None:
        """Create the complete dashboard interface."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(14)

        summary_layout = QHBoxLayout()
        summary_layout.setSpacing(10)

        self.balance_value = QLabel("$0.00")
        self.income_value = QLabel("$0.00")
        self.expenses_value = QLabel("$0.00")

        balance_card = self.create_summary_card(
            "Current Balance",
            self.balance_value,
        )

        income_card = self.create_summary_card(
            "Total Income",
            self.income_value,
        )

        expenses_card = self.create_summary_card(
            "Total Expenses",
            self.expenses_value,
        )

        summary_layout.addWidget(balance_card)
        summary_layout.addWidget(income_card)
        summary_layout.addWidget(expenses_card)

        main_layout.addLayout(summary_layout)

        transactions_title = QLabel("Transactions")
        transactions_title.setStyleSheet(
            """
            QLabel {
                font-size: 24px;
                font-weight: bold;
            }
            """
        )

        main_layout.addWidget(transactions_title)

        self.transaction_list = QListWidget()
        self.transaction_list.setAlternatingRowColors(True)

        main_layout.addWidget(self.transaction_list, 1)

        input_layout = QHBoxLayout()
        input_layout.setSpacing(8)

        self.description_input = QLineEdit()
        self.description_input.setPlaceholderText("Transaction name")

        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("Amount")

        self.type_combo = QComboBox()
        self.type_combo.addItems(
            [
                "Expense",
                "Income",
            ]
        )

        self.category_combo = QComboBox()
        self.category_combo.addItems(
            [
                "Food",
                "Groceries",
                "Transportation",
                "Entertainment",
                "Bills",
                "Shopping",
                "Healthcare",
                "Housing",
                "Education",
                "Income",
                "Other",
            ]
        )

        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDisplayFormat("yyyy-MM-dd")
        self.date_input.setDate(QDate.currentDate())

        self.add_button = QPushButton("Add Transaction")
        self.add_button.clicked.connect(
            self.save_transaction
        )

        self.import_csv_button = QPushButton(
            "Import Bank CSV"
        )
        self.import_csv_button.clicked.connect(
            self.import_bank_history
        )

        input_layout.addWidget(self.description_input, 2)
        input_layout.addWidget(self.amount_input, 1)
        input_layout.addWidget(self.type_combo, 1)
        input_layout.addWidget(self.category_combo, 1)
        input_layout.addWidget(self.date_input, 1)
        input_layout.addWidget(self.add_button)
        input_layout.addWidget(self.import_csv_button)

        main_layout.addLayout(input_layout)

        self.remove_button = QPushButton(
            "Remove Selected Transaction"
        )
        self.remove_button.clicked.connect(
            self.remove_selected_transaction
        )

        main_layout.addWidget(self.remove_button)

    def create_summary_card(
        self,
        title: str,
        value_label: QLabel,
    ) -> QFrame:
        """Create one dashboard summary card."""
        card = QFrame()
        card.setFrameShape(QFrame.Shape.StyledPanel)

        card.setStyleSheet(
            """
            QFrame {
                border: 1px solid #777777;
                border-radius: 10px;
                padding: 10px;
            }

            QLabel {
                border: none;
            }
            """
        )

        card_layout = QVBoxLayout(card)

        title_label = QLabel(title)
        title_label.setStyleSheet(
            """
            QLabel {
                font-size: 15px;
            }
            """
        )

        value_label.setStyleSheet(
            """
            QLabel {
                font-size: 28px;
                font-weight: bold;
            }
            """
        )

        card_layout.addWidget(title_label)
        card_layout.addWidget(value_label)

        return card

    def save_transaction(self) -> None:
        """Validate and save one manually entered transaction."""
        description = self.description_input.text().strip()
        amount_text = self.amount_input.text().strip()
        transaction_type = self.type_combo.currentText()
        category = self.category_combo.currentText()

        transaction_date = (
            self.date_input.date().toString("yyyy-MM-dd")
        )

        if not description:
            QMessageBox.warning(
                self,
                "Missing Description",
                "Please enter a transaction name.",
            )
            return

        if not amount_text:
            QMessageBox.warning(
                self,
                "Missing Amount",
                "Please enter a transaction amount.",
            )
            return

        try:
            cleaned_amount = (
                amount_text
                .replace("$", "")
                .replace(",", "")
                .strip()
            )

            amount = float(cleaned_amount)

        except ValueError:
            QMessageBox.warning(
                self,
                "Invalid Amount",
                "Enter a valid number, such as 25.50.",
            )
            return

        if amount == 0:
            QMessageBox.warning(
                self,
                "Invalid Amount",
                "The transaction amount cannot be zero.",
            )
            return

        if transaction_type == "Expense":
            amount = -abs(amount)
        else:
            amount = abs(amount)
            category = "Income"

        try:
            add_transaction(
                description=description,
                amount=amount,
                category=category,
                transaction_date=transaction_date,
            )

            self.description_input.clear()
            self.amount_input.clear()

            self.refresh_dashboard()

        except Exception as error:
            QMessageBox.critical(
                self,
                "Database Error",
                (
                    "The transaction could not be saved.\n\n"
                    f"{error}"
                ),
            )

    def display_transactions(self) -> None:
        """Load and display transactions from the database."""
        self.transaction_list.clear()

        try:
            transactions = get_transactions()

            for transaction in transactions:
                amount = float(transaction["amount"])

                if amount >= 0:
                    amount_text = f"+${amount:,.2f}"
                    transaction_type = "Income"
                else:
                    amount_text = f"-${abs(amount):,.2f}"
                    transaction_type = "Expense"

                text = (
                    f"{transaction['description']}  |  "
                    f"{amount_text}  |  "
                    f"{transaction_type}  |  "
                    f"{transaction['category']}  |  "
                    f"{transaction['transaction_date']}"
                )

                item = QListWidgetItem(text)

                item.setData(
                    Qt.ItemDataRole.UserRole,
                    int(transaction["id"]),
                )

                self.transaction_list.addItem(item)

        except Exception as error:
            QMessageBox.critical(
                self,
                "Database Error",
                (
                    "The transactions could not be loaded.\n\n"
                    f"{error}"
                ),
            )

    def update_summary(self) -> None:
        """Update balance, income, and expense cards."""
        try:
            summary = get_financial_summary()

            income = float(summary.get("income", 0))
            expenses = float(summary.get("expenses", 0))
            balance = float(summary.get("balance", 0))

            self.balance_value.setText(
                f"${balance:,.2f}"
            )

            self.income_value.setText(
                f"${income:,.2f}"
            )

            self.expenses_value.setText(
                f"${expenses:,.2f}"
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Database Error",
                (
                    "The financial summary could not be loaded.\n\n"
                    f"{error}"
                ),
            )

    def refresh_dashboard(self) -> None:
        """Refresh all financial information shown on screen."""
        self.update_summary()
        self.display_transactions()

    def remove_selected_transaction(self) -> None:
        """Delete the currently selected transaction."""
        selected_item = self.transaction_list.currentItem()

        if selected_item is None:
            QMessageBox.warning(
                self,
                "No Transaction Selected",
                "Select a transaction before removing it.",
            )
            return

        transaction_id = selected_item.data(
            Qt.ItemDataRole.UserRole
        )

        confirmation = QMessageBox.question(
            self,
            "Remove Transaction",
            "Are you sure you want to remove this transaction?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
        )

        if confirmation != QMessageBox.StandardButton.Yes:
            return

        try:
            deleted = delete_transaction(transaction_id)

            if deleted:
                self.refresh_dashboard()
            else:
                QMessageBox.warning(
                    self,
                    "Transaction Not Found",
                    "That transaction was not found in the database.",
                )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Database Error",
                (
                    "The transaction could not be removed.\n\n"
                    f"{error}"
                ),
            )

    def import_bank_history(self) -> None:
        """Open a CSV file and import its transactions."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Bank Transaction CSV",
            "",
            "CSV Files (*.csv);;All Files (*)",
        )

        if not file_path:
            return

        try:
            result = import_bank_csv(file_path)

            self.refresh_dashboard()

            imported = result.get("imported", 0)
            skipped = result.get("skipped", 0)
            failed = result.get("failed", 0)

            QMessageBox.information(
                self,
                "Import Complete",
                (
                    f"Imported transactions: {imported}\n"
                    f"Duplicates skipped: {skipped}\n"
                    f"Failed rows: {failed}"
                ),
            )

        except BankCSVImportError as error:
            QMessageBox.critical(
                self,
                "CSV Import Error",
                str(error),
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Import Error",
                (
                    "The bank CSV could not be imported.\n\n"
                    f"{error}"
                ),
            )
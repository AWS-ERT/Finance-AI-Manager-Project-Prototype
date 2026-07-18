import sqlite3
from datetime import date
from pathlib import Path
from typing import Optional


# Finance-AI/
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Finance-AI/finance.db
DATABASE_PATH = PROJECT_ROOT / "finance.db"


def get_connection() -> sqlite3.Connection:
    """
    Open a connection to the SQLite database.

    sqlite3.Row lets the rest of the app access columns by name:

        row["description"]
        row["amount"]
    """
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


def create_tables() -> None:
    """
    Create all database tables if they do not already exist.

    This does not delete existing information.
    """
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL DEFAULT 'Other',
                transaction_date TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS investments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                shares REAL NOT NULL,
                purchase_price REAL NOT NULL,
                current_price REAL NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        connection.commit()


# =========================================================
# TRANSACTIONS
# =========================================================

def add_transaction(
    description: str,
    amount: float,
    category: str = "Other",
    transaction_date: Optional[str] = None,
) -> int:
    """
    Add one transaction.

    Income should use a positive amount:
        2500

    Expenses should use a negative amount:
        -45.75

    Returns the ID of the new transaction.
    """
    description = str(description).strip()
    category = str(category).strip() or "Other"

    if not description:
        raise ValueError("A transaction description is required.")

    try:
        amount = float(amount)
    except (TypeError, ValueError) as error:
        raise ValueError("The transaction amount must be a number.") from error

    if transaction_date is None or not str(transaction_date).strip():
        transaction_date = date.today().isoformat()
    else:
        transaction_date = str(transaction_date).strip()

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO transactions (
                description,
                amount,
                category,
                transaction_date
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                description,
                amount,
                category,
                transaction_date,
            ),
        )

        connection.commit()

        return int(cursor.lastrowid)

def transaction_exists(
    description: str,
    amount: float,
    transaction_date: str,
) -> bool:
    """
    Check whether an identical transaction is already stored.

    This helps prevent duplicate transactions when the same CSV
    is imported more than once.
    """
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id
            FROM transactions
            WHERE description = ?
              AND amount = ?
              AND transaction_date = ?
            LIMIT 1
            """,
            (
                description,
                float(amount),
                transaction_date,
            ),
        ).fetchone()

    return row is not None
def get_transactions() -> list[sqlite3.Row]:
    """
    Return all transactions, with the newest transactions first.
    """
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                id,
                description,
                amount,
                category,
                transaction_date,
                created_at
            FROM transactions
            ORDER BY transaction_date DESC, id DESC
            """
        ).fetchall()

    return rows


def delete_transaction(transaction_id: int) -> bool:
    """
    Delete one transaction.

    Returns True if a transaction was deleted.
    Returns False if the ID was not found.
    """
    try:
        transaction_id = int(transaction_id)
    except (TypeError, ValueError) as error:
        raise ValueError("The transaction ID must be a number.") from error

    with get_connection() as connection:
        cursor = connection.execute(
            """
            DELETE FROM transactions
            WHERE id = ?
            """,
            (transaction_id,),
        )

        connection.commit()

        return cursor.rowcount > 0


def get_financial_summary() -> dict:
    """
    Return total income, expenses, and balance.

    Expenses are returned as a positive total even though they are stored
    as negative transaction amounts.
    """
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
                COALESCE(
                    SUM(
                        CASE
                            WHEN amount > 0 THEN amount
                            ELSE 0
                        END
                    ),
                    0
                ) AS income,

                COALESCE(
                    SUM(
                        CASE
                            WHEN amount < 0 THEN ABS(amount)
                            ELSE 0
                        END
                    ),
                    0
                ) AS expenses,

                COALESCE(SUM(amount), 0) AS balance
            FROM transactions
            """
        ).fetchone()

    return {
        "income": float(row["income"]),
        "expenses": float(row["expenses"]),
        "balance": float(row["balance"]),
    }


def get_spending_by_category() -> list[dict]:
    """
    Return expense totals grouped by category.

    Only negative transaction amounts count as spending.
    """
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                CASE
                    WHEN category IS NULL OR TRIM(category) = ''
                    THEN 'Uncategorized'
                    ELSE category
                END AS category,

                SUM(ABS(amount)) AS total

            FROM transactions

            WHERE amount < 0

            GROUP BY
                CASE
                    WHEN category IS NULL OR TRIM(category) = ''
                    THEN 'Uncategorized'
                    ELSE category
                END

            ORDER BY total DESC
            """
        ).fetchall()

    spending = []

    for row in rows:
        spending.append(
            {
                "category": row["category"],
                "total": float(row["total"]),
            }
        )

    return spending


# =========================================================
# INVESTMENTS
# =========================================================

def add_investment(
    symbol: str,
    shares: float,
    purchase_price: float,
    current_price: float,
) -> int:
    """
    Add one investment.

    Returns the ID of the new investment.
    """
    symbol = str(symbol).strip().upper()

    if not symbol:
        raise ValueError("An investment symbol is required.")

    try:
        shares = float(shares)
        purchase_price = float(purchase_price)
        current_price = float(current_price)
    except (TypeError, ValueError) as error:
        raise ValueError(
            "Shares and prices must be valid numbers."
        ) from error

    if shares <= 0:
        raise ValueError("Shares must be greater than zero.")

    if purchase_price < 0 or current_price < 0:
        raise ValueError("Investment prices cannot be negative.")

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO investments (
                symbol,
                shares,
                purchase_price,
                current_price
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                symbol,
                shares,
                purchase_price,
                current_price,
            ),
        )

        connection.commit()

        return int(cursor.lastrowid)


def get_investments() -> list[sqlite3.Row]:
    """
    Return all investments.

    This also calculates cost basis, current value, and profit/loss
    for each investment.
    """
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                id,
                symbol,
                shares,
                purchase_price,
                current_price,
                shares * purchase_price AS cost_basis,
                shares * current_price AS current_value,
                shares * (current_price - purchase_price) AS profit_loss,
                created_at
            FROM investments
            ORDER BY symbol ASC, id DESC
            """
        ).fetchall()

    return rows


def delete_investment(investment_id: int) -> bool:
    """
    Delete one investment.

    Returns True if an investment was deleted.
    Returns False if the ID was not found.
    """
    try:
        investment_id = int(investment_id)
    except (TypeError, ValueError) as error:
        raise ValueError("The investment ID must be a number.") from error

    with get_connection() as connection:
        cursor = connection.execute(
            """
            DELETE FROM investments
            WHERE id = ?
            """,
            (investment_id,),
        )

        connection.commit()

        return cursor.rowcount > 0


def get_investment_summary() -> dict:
    """
    Return total portfolio value, cost basis, and profit/loss.
    """
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
                COALESCE(
                    SUM(shares * purchase_price),
                    0
                ) AS cost_basis,

                COALESCE(
                    SUM(shares * current_price),
                    0
                ) AS portfolio_value

            FROM investments
            """
        ).fetchone()

    cost_basis = float(row["cost_basis"])
    portfolio_value = float(row["portfolio_value"])

    return {
        "cost_basis": cost_basis,
        "portfolio_value": portfolio_value,
        "profit_loss": portfolio_value - cost_basis,
    }


# Create the tables whenever this file is imported.
create_tables()


if __name__ == "__main__":
    print(f"Database initialized at: {DATABASE_PATH}")

    print("\nFinancial summary:")
    print(get_financial_summary())

    print("\nSpending by category:")
    print(get_spending_by_category())

    print("\nInvestment summary:")
    print(get_investment_summary())
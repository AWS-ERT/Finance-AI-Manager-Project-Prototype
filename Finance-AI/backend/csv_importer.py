import csv
from datetime import datetime
from pathlib import Path

from backend.database import add_transaction


class BankCSVImportError(Exception):
    """Raised when a bank CSV cannot be imported."""


def _get_value(row: dict, possible_names: list[str]) -> str:
    normalized = {
        str(key).strip().lower(): value
        for key, value in row.items()
        if key is not None
    }

    for name in possible_names:
        value = normalized.get(name.lower())

        if value is not None and str(value).strip():
            return str(value).strip()

    return ""


def _parse_date(value: str) -> str:
    formats = [
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%m/%d/%y",
        "%m-%d-%Y",
        "%m-%d-%y",
    ]

    for date_format in formats:
        try:
            return datetime.strptime(
                value.strip(),
                date_format,
            ).date().isoformat()
        except ValueError:
            continue

    raise BankCSVImportError(
        f"Unsupported date format: {value}"
    )


def _clean_number(value: str) -> float:
    cleaned = (
        value.replace("$", "")
        .replace(",", "")
        .replace("(", "-")
        .replace(")", "")
        .strip()
    )

    return float(cleaned)


def _parse_amount(row: dict) -> float:
    amount = _get_value(
        row,
        [
            "amount",
            "transaction amount",
        ],
    )

    if amount:
        return _clean_number(amount)

    debit = _get_value(
        row,
        [
            "debit",
            "withdrawal",
            "withdrawals",
        ],
    )

    credit = _get_value(
        row,
        [
            "credit",
            "deposit",
            "deposits",
        ],
    )

    if debit:
        return -abs(_clean_number(debit))

    if credit:
        return abs(_clean_number(credit))

    raise BankCSVImportError(
        "No Amount, Debit, or Credit column was found."
    )


def _guess_category(description: str, amount: float) -> str:
    if amount > 0:
        return "Income"

    text = description.lower()

    categories = {
        "Food": [
            "restaurant",
            "mcdonald",
            "starbucks",
            "doordash",
            "uber eats",
        ],
        "Groceries": [
            "walmart",
            "kroger",
            "publix",
            "aldi",
            "costco",
        ],
        "Transportation": [
            "shell",
            "chevron",
            "exxon",
            "uber",
            "lyft",
        ],
        "Entertainment": [
            "netflix",
            "spotify",
            "steam",
            "playstation",
            "xbox",
        ],
        "Bills": [
            "electric",
            "water",
            "internet",
            "phone",
            "insurance",
        ],
    }

    for category, keywords in categories.items():
        for keyword in keywords:
            if keyword in text:
                return category

    return "Other"


def import_bank_csv(file_path: str) -> dict:
    path = Path(file_path)

    if not path.exists():
        raise BankCSVImportError(
            "The selected CSV file does not exist."
        )

    imported = 0
    failed = 0

    try:
        with path.open(
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as csv_file:
            reader = csv.DictReader(csv_file)

            if not reader.fieldnames:
                raise BankCSVImportError(
                    "The CSV has no column headings."
                )

            for row in reader:
                try:
                    description = _get_value(
                        row,
                        [
                            "description",
                            "merchant",
                            "merchant name",
                            "details",
                            "memo",
                            "name",
                        ],
                    )

                    date_text = _get_value(
                        row,
                        [
                            "date",
                            "transaction date",
                            "posting date",
                            "posted date",
                        ],
                    )

                    if not description or not date_text:
                        failed += 1
                        continue

                    transaction_date = _parse_date(date_text)
                    amount = _parse_amount(row)
                    category = _guess_category(
                        description,
                        amount,
                    )

                    add_transaction(
                        description=description,
                        amount=amount,
                        category=category,
                        transaction_date=transaction_date,
                    )

                    imported += 1

                except Exception:
                    failed += 1

    except UnicodeDecodeError as error:
        raise BankCSVImportError(
            "The CSV could not be read. Export it as a UTF-8 CSV."
        ) from error

    return {
        "imported": imported,
        "failed": failed,
    }
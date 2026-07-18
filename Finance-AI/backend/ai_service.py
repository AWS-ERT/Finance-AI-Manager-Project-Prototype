import os
from typing import Callable

import anthropic

from backend.database import (
    get_financial_summary,
    get_spending_by_category,
    get_investments,
    get_investment_summary,
)


class ClaudeServiceError(Exception):
    pass


def _money(value):
    try:
        return f"${float(value):,.2f}"
    except Exception:
        return "$0.00"


def build_budget_context():
    summary = get_financial_summary()
    spending = get_spending_by_category()

    category_lines = []

    for item in spending:
        category = item.get("category") or "Uncategorized"
        total = item.get("total", 0)
        category_lines.append(f"- {category}: {_money(total)}")

    if not category_lines:
        category_lines.append("- No expense records.")

    return f"""
FINANCIAL RECORDS

Total income: {_money(summary.get("income",0))}
Total expenses: {_money(summary.get("expenses",0))}
Current balance: {_money(summary.get("balance",0))}

SPENDING BY CATEGORY
{chr(10).join(category_lines)}
""".strip()


def build_investment_context():
    summary = get_investment_summary()
    investments = get_investments()

    lines = []

    for investment in investments:
        lines.append(
            f"- {investment['symbol']}: "
            f"{investment['shares']} shares "
            f"value {_money(investment['current_value'])}"
        )

    if not lines:
        lines.append("- No investments recorded.")

    return f"""
INVESTMENT SUMMARY

Cost basis: {_money(summary.get("cost_basis",0))}
Portfolio value: {_money(summary.get("portfolio_value",0))}
Profit/Loss: {_money(summary.get("profit_loss",0))}

HOLDINGS
{chr(10).join(lines)}
""".strip()


def _ask_claude(question, context_builder, system_prompt):
    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        raise ClaudeServiceError(
            "ANTHROPIC_API_KEY not found."
        )

    client = anthropic.Anthropic(api_key=api_key)

    context = context_builder()

    try:
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=900,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content":
                        f"{context}\n\n"
                        f"Question:\n{question}"
                }
            ],
        )

        answer = ""

        for block in response.content:
            if block.type == "text":
                answer += block.text

        return answer

    except Exception as e:
        print(e)
        raise ClaudeServiceError(str(e))


def ask_budget_claude(question):
    return _ask_claude(
        question,
        build_budget_context,
        """
You are a budgeting assistant.
Use ONLY the financial records provided.
Do not invent information.
""",
    )


def ask_investment_claude(question):
    return _ask_claude(
        question,
        build_investment_context,
        """
You are an investment education assistant.
Use ONLY the supplied portfolio information.
Do not invent prices.
Do not guarantee returns.
""",
    )
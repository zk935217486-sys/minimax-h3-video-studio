from __future__ import annotations

from datetime import datetime
from typing import Any


class AccountManager:
    """Manage operator-provided free-plan accounts and their daily quota."""

    def __init__(self):
        self.accounts: list[dict[str, Any]] = []

    def add_account(self, account: dict[str, Any]) -> dict[str, Any]:
        record = {**account, "used_today": account.get("used_today", 0), "last_used_date": account.get("last_used_date")}
        self.accounts.append(record)
        return record

    def list_accounts(self) -> list[dict[str, Any]]:
        return [{key: value for key, value in account.items() if key != "cookies"} for account in self.accounts]

    def get_available_account(self) -> dict[str, Any] | None:
        today = datetime.now().strftime("%Y-%m-%d")
        for account in self.accounts:
            if account.get("last_used_date") != today:
                account["used_today"] = 0
                account["last_used_date"] = today
            if account.get("used_today", 0) < account.get("daily_quota", 10):
                return account
        return None

    def record_use(self, account: dict[str, Any]) -> None:
        account["used_today"] = account.get("used_today", 0) + 1

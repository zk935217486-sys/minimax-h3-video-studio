from __future__ import annotations

from typing import Any


class AccountFactory:
    """Store explicitly supplied accounts; automated third-party registration is disabled."""

    def create_manual_account(self, email: str, cookies: str, daily_quota: int = 10) -> dict[str, Any]:
        if not email or not cookies:
            raise ValueError("邮箱和 cookies 都不能为空")
        if daily_quota <= 0:
            raise ValueError("daily_quota 必须大于 0")
        return {"email": email, "cookies": cookies, "daily_quota": daily_quota, "used_today": 0}

    def auto_register(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError("自动接码注册未启用，请使用合规的人工账号导入流程")

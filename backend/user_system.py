from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
import uuid
from datetime import datetime
from typing import Any

from .errors import AuthenticationError, ConflictError


class UserSystem:
    """Reference-compatible user service with register/login/verify_token APIs."""

    def __init__(self, secret_key: str | None = None) -> None:
        self.users: dict[str, dict[str, Any]] = {}
        self.secret_key = secret_key or os.getenv("JWT_SECRET", "development-only-change-this-secret").encode()
        if isinstance(self.secret_key, str):
            self.secret_key = self.secret_key.encode()

    @staticmethod
    def _hash_password(password: str, salt: bytes | None = None) -> str:
        salt = salt or os.urandom(16)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 120_000)
        return f"pbkdf2_sha256$120000${base64.urlsafe_b64encode(salt).decode()}${base64.urlsafe_b64encode(digest).decode()}"

    @staticmethod
    def _check_password(password: str, encoded: str) -> bool:
        try:
            algorithm, rounds, salt_value, digest_value = encoded.split("$")
            if algorithm != "pbkdf2_sha256":
                return False
            salt = base64.urlsafe_b64decode(salt_value.encode())
            digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, int(rounds))
            return hmac.compare_digest(base64.urlsafe_b64encode(digest).decode(), digest_value)
        except (ValueError, TypeError):
            return False

    def register(self, email: str, password: str, phone: str | None = None) -> dict[str, Any]:
        email = email.strip().lower()
        if email in self.users:
            raise ConflictError("邮箱已注册")
        if len(password) < 6:
            raise ValueError("密码至少需要 6 位")
        user = {"id": str(uuid.uuid4()), "email": email, "phone": phone, "password_hash": self._hash_password(password), "plan": "free", "credits": 100, "created_at": datetime.now().isoformat(), "videos_generated": 0}
        self.users[email] = user
        return self.public_user(user)

    def login(self, account: str, password: str) -> dict[str, Any]:
        user = self.users.get(account.strip().lower())
        if not user or not self._check_password(password, user["password_hash"]):
            raise AuthenticationError("账号或密码错误")
        token = self._encode_token({"user_id": user["id"], "email": user["email"], "exp": int(time.time()) + 30 * 24 * 60 * 60})
        return {"token": token, "user": self.public_user(user)}

    def verify_token(self, token: str) -> dict[str, Any] | None:
        try:
            payload = self._decode_token(token)
            return self.users.get(payload.get("email"))
        except (ValueError, KeyError, TypeError):
            return None

    def consume_credits(self, email: str, amount: int = 10) -> dict[str, Any]:
        user = self.users[email]
        if amount <= 0 or user["credits"] < amount:
            raise ValueError("积分不足")
        user["credits"] -= amount
        user["videos_generated"] += 1
        return self.public_user(user)

    @staticmethod
    def public_user(user: dict[str, Any]) -> dict[str, Any]:
        return {key: value for key, value in user.items() if key != "password_hash"}

    def _encode_token(self, payload: dict[str, Any]) -> str:
        header = {"alg": "HS256", "typ": "JWT"}
        def encode(value: dict[str, Any]) -> str:
            return base64.urlsafe_b64encode(json.dumps(value, separators=(",", ":")).encode()).decode().rstrip("=")
        body = f"{encode(header)}.{encode(payload)}"
        signature = hmac.new(self.secret_key, body.encode(), hashlib.sha256).digest()
        return f"{body}.{base64.urlsafe_b64encode(signature).decode().rstrip('=')}"

    def _decode_token(self, token: str) -> dict[str, Any]:
        header, body, signature = token.split(".")
        signing_input = f"{header}.{body}"
        expected = base64.urlsafe_b64encode(hmac.new(self.secret_key, signing_input.encode(), hashlib.sha256).digest()).decode().rstrip("=")
        if not hmac.compare_digest(expected, signature):
            raise ValueError("token signature invalid")
        padding = "=" * (-len(body) % 4)
        payload = json.loads(base64.urlsafe_b64decode(f"{body}{padding}"))
        if payload.get("exp", 0) < time.time():
            raise ValueError("token expired")
        return payload

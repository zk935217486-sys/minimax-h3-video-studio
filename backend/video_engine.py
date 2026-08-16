from __future__ import annotations

from datetime import datetime
from typing import Any


class VideoEngine:
    """MiniMax H3 video engine with official, free-ComfyUI, and automatic modes."""

    def __init__(self, comfyui_url: str = "http://localhost:8188") -> None:
        self.mode = "auto"
        self.official_api_key: str | None = None
        self.comfyui_url = comfyui_url
        self.free_accounts: list[dict[str, Any]] = []
        self.current_account_index = 0

    def set_mode(self, mode: str) -> None:
        if mode not in {"auto", "official", "free"}:
            raise ValueError("模式必须是 auto、official 或 free")
        self.mode = mode

    def set_official_api(self, api_key: str) -> None:
        self.official_api_key = api_key

    def set_free_accounts(self, accounts: list[dict[str, Any]]) -> None:
        self.free_accounts = accounts

    async def generate_text_to_video(self, request: Any) -> dict[str, Any]:
        if self.mode == "official":
            return await self._official_t2v(request.prompt, request.duration, request.resolution)
        if self.mode == "free":
            return await self._free_t2v(request.prompt, request.duration, request.resolution)
        return await self._auto_t2v(request.prompt, request.duration, request.resolution, request.priority)

    async def generate_image_to_video(self, request: Any) -> dict[str, Any]:
        image_path = getattr(request, "image_path", None)
        if not image_path:
            raise ValueError("图片路径不存在")
        if self.mode == "official":
            return await self._official_i2v(image_path, request.prompt, request.effect, request.duration)
        if self.mode == "free":
            return await self._free_i2v(image_path, request.prompt, request.effect, request.duration)
        return await self._auto_i2v(image_path, request.prompt, request.effect, request.duration)

    async def _official_t2v(self, prompt: str, duration: int, resolution: str) -> dict[str, Any]:
        if not self.official_api_key:
            raise RuntimeError("官方API未配置")
        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.post("https://api.minimax.chat/v1/video/generation", headers={"Authorization": f"Bearer {self.official_api_key}", "Content-Type": "application/json"}, json={"model": "H3", "prompt": prompt, "duration": duration, "resolution": resolution, "type": "text_to_video"}, timeout=60)
            response.raise_for_status()
            result = response.json()
        return {"mode": "official", "task_id": result.get("task_id")}

    async def _official_i2v(self, image_path: str, prompt: str, effect: str, duration: int) -> dict[str, Any]:
        if not self.official_api_key:
            raise RuntimeError("官方API未配置")
        import httpx

        with open(image_path, "rb") as image_file:
            image_data = image_file.read()
        async with httpx.AsyncClient() as client:
            response = await client.post("https://api.minimax.chat/v1/video/generation", headers={"Authorization": f"Bearer {self.official_api_key}"}, files={"image": image_data}, data={"model": "H3", "prompt": prompt, "effect": effect, "duration": duration, "type": "image_to_video"}, timeout=60)
            response.raise_for_status()
            result = response.json()
        return {"mode": "official", "task_id": result.get("task_id")}

    async def _free_t2v(self, prompt: str, duration: int, resolution: str) -> dict[str, Any]:
        account = self._get_available_account()
        if not account:
            raise RuntimeError("没有可用账号")
        result = await self._comfyui_prompt({"class_type": "MiniMaxT2V", "inputs": {"prompt": prompt, "duration": duration, "resolution": resolution, "cookies": account.get("cookies")}})
        account["used_today"] = account.get("used_today", 0) + 1
        return {"mode": "free", "task_id": result.get("prompt_id")}

    async def _free_i2v(self, image_path: str, prompt: str, effect: str, duration: int) -> dict[str, Any]:
        account = self._get_available_account()
        if not account:
            raise RuntimeError("没有可用账号")
        result = await self._comfyui_prompt({"class_type": "MiniMaxI2V", "inputs": {"image": image_path, "prompt": prompt, "effect": effect, "duration": duration, "cookies": account.get("cookies")}})
        account["used_today"] = account.get("used_today", 0) + 1
        return {"mode": "free", "task_id": result.get("prompt_id")}

    async def _comfyui_prompt(self, node: dict[str, Any]) -> dict[str, Any]:
        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.comfyui_url}/prompt", json={"prompt": {"1": node}}, timeout=30)
            response.raise_for_status()
            return response.json()

    async def _auto_t2v(self, prompt: str, duration: int, resolution: str, priority: int) -> dict[str, Any]:
        if priority >= 8 and self.official_api_key:
            return await self._official_t2v(prompt, duration, resolution)
        if self.free_accounts and self._get_available_account():
            return await self._free_t2v(prompt, duration, resolution)
        if self.official_api_key:
            return await self._official_t2v(prompt, duration, resolution)
        raise RuntimeError("没有可用的生成方式")

    async def _auto_i2v(self, image_path: str, prompt: str, effect: str, duration: int) -> dict[str, Any]:
        if self.free_accounts and self._get_available_account():
            return await self._free_i2v(image_path, prompt, effect, duration)
        if self.official_api_key:
            return await self._official_i2v(image_path, prompt, effect, duration)
        raise RuntimeError("没有可用的生成方式")

    def _get_available_account(self) -> dict[str, Any] | None:
        today = datetime.now().strftime("%Y-%m-%d")
        for account in self.free_accounts:
            if account.get("last_used_date") != today:
                account["used_today"] = 0
                account["last_used_date"] = today
            if account.get("used_today", 0) < account.get("daily_quota", 10):
                return account
        return None

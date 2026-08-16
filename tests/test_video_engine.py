import asyncio
import unittest
from types import SimpleNamespace

from backend.video_engine import VideoEngine


class FakeEngine(VideoEngine):
    async def _official_t2v(self, prompt, duration, resolution):
        return {"mode": "official", "task_id": "official-1"}

    async def _free_t2v(self, prompt, duration, resolution):
        account = self._get_available_account()
        account["used_today"] = account.get("used_today", 0) + 1
        return {"mode": "free", "task_id": "free-1"}


class VideoEngineTests(unittest.TestCase):
    def request(self, priority=5):
        return SimpleNamespace(prompt="海边日出", duration=6, resolution="1080p", priority=priority)

    def test_auto_uses_free_account_before_official_for_normal_priority(self):
        engine = FakeEngine()
        engine.set_official_api("key")
        engine.set_free_accounts([{"cookies": "cookie", "daily_quota": 2}])
        result = asyncio.run(engine.generate_text_to_video(self.request()))
        self.assertEqual(result["mode"], "free")
        self.assertEqual(engine.free_accounts[0]["used_today"], 1)

    def test_auto_uses_official_for_high_priority(self):
        engine = FakeEngine()
        engine.set_official_api("key")
        engine.set_free_accounts([{"cookies": "cookie", "daily_quota": 2}])
        result = asyncio.run(engine.generate_text_to_video(self.request(priority=8)))
        self.assertEqual(result["mode"], "official")

    def test_auto_without_any_backend_fails_clearly(self):
        with self.assertRaisesRegex(RuntimeError, "没有可用的生成方式"):
            asyncio.run(VideoEngine().generate_text_to_video(self.request()))

    def test_invalid_mode_is_rejected(self):
        with self.assertRaises(ValueError):
            VideoEngine().set_mode("unknown")


if __name__ == "__main__":
    unittest.main()

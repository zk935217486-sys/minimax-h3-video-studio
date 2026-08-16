import unittest

from backend.account_factory import AccountFactory
from backend.account_manager import AccountManager
from backend.proxy_manager import ProxyManager
from backend.user_system import UserSystem


class UserAndAccountTests(unittest.TestCase):
    def test_register_login_verify_and_consume_credits(self):
        users = UserSystem("test-secret")
        user = users.register("CREATOR@example.com", "secret123")
        self.assertEqual(user["credits"], 100)
        result = users.login("creator@example.com", "secret123")
        verified = users.verify_token(result["token"])
        self.assertEqual(verified["email"], "creator@example.com")
        self.assertEqual(users.consume_credits("creator@example.com", 10)["credits"], 90)

    def test_duplicate_registration_and_bad_login_fail(self):
        users = UserSystem("test-secret")
        users.register("creator@example.com", "secret123")
        with self.assertRaises(Exception):
            users.register("creator@example.com", "secret123")
        with self.assertRaises(Exception):
            users.login("creator@example.com", "bad-password")

    def test_account_quota_and_proxy_rotation(self):
        manager = AccountManager()
        account = manager.add_account({"email": "a@example.com", "cookies": "secret", "daily_quota": 1})
        self.assertIs(manager.get_available_account(), account)
        manager.record_use(account)
        self.assertIsNone(manager.get_available_account())
        proxy = ProxyManager(["http://127.0.0.1:8080", "socks5://127.0.0.1:1080"])
        self.assertEqual(proxy.get_next_proxy(), "http://127.0.0.1:8080")
        self.assertEqual(proxy.get_next_proxy(), "socks5://127.0.0.1:1080")

    def test_factory_refuses_automated_registration(self):
        with self.assertRaises(NotImplementedError):
            AccountFactory().auto_register()


if __name__ == "__main__":
    unittest.main()

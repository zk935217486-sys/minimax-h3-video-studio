import os
import tempfile
import unittest
from pathlib import Path

from backend.config import ConfigError, Settings
from backend.db import Database, row_to_dict


class BackendFoundationTests(unittest.TestCase):
    def test_database_initializes_users_and_tasks(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Database(Path(directory) / "studio.sqlite3")
            database.initialize()
            database.execute(
                "INSERT INTO users (id, email, password_hash, credits, created_at) VALUES (?, ?, ?, ?, ?)",
                ("u1", "creator@example.com", "hash", 100, "2026-01-01T00:00:00Z"),
            )
            user = row_to_dict(database.fetch_one("SELECT email, credits FROM users WHERE id = ?", ("u1",)))
            self.assertEqual(user, {"email": "creator@example.com", "credits": 100})

    def test_production_requires_long_jwt_secret(self):
        original_environment = os.environ.copy()
        try:
            os.environ["APP_ENV"] = "production"
            os.environ["JWT_SECRET"] = "short"
            with self.assertRaisesRegex(ConfigError, "32 characters"):
                Settings.from_env()
        finally:
            os.environ.clear()
            os.environ.update(original_environment)


if __name__ == "__main__":
    unittest.main()

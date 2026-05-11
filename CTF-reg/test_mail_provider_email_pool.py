import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import Config
from mail_provider import MailProvider


class MailProviderEmailPoolTest(unittest.TestCase):
    def test_config_resolves_pool_paths_relative_to_config_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_dir = Path(tmp) / "cfg"
            config_dir.mkdir()
            config_path = config_dir / "config.json"
            config_path.write_text(
                json.dumps({
                    "mail": {
                        "email": "inbox@example.com",
                        "email_pool_file": "../output/aliases.txt",
                        "email_pool_state_path": "../output/state.json",
                    }
                }),
                encoding="utf-8",
            )

            cfg = Config.from_file(str(config_path))

            self.assertEqual(cfg.mail.email_pool_file, str(Path(tmp) / "output" / "aliases.txt"))
            self.assertEqual(cfg.mail.email_pool_state_path, str(Path(tmp) / "output" / "state.json"))

    def test_inline_pool_is_used_before_catch_all_without_imap_connect(self):
        provider = MailProvider(
            "imap.example.com",
            993,
            "inbox@example.com",
            "auth",
            "catchall.example.com",
            email_pool=["first@example.com", "second@example.com"],
        )

        def fail_connect():
            raise AssertionError("email pool should not connect during create_mailbox")

        provider._connect = fail_connect

        self.assertEqual(provider.create_mailbox(), "first@example.com")
        self.assertEqual(provider.create_mailbox(), "second@example.com")
        with self.assertRaisesRegex(RuntimeError, "邮箱池已耗尽"):
            provider.create_mailbox()

    def test_pool_file_state_persists_next_index_across_instances(self):
        with tempfile.TemporaryDirectory() as tmp:
            pool_path = Path(tmp) / "aliases.txt"
            state_path = Path(tmp) / "state.json"
            pool_path.write_text(
                "\n".join([
                    "# comments are ignored",
                    "first@example.com",
                    "second@example.com",
                    "FIRST@example.com",
                ]),
                encoding="utf-8",
            )

            first = MailProvider(
                "imap.example.com",
                993,
                "inbox@example.com",
                "auth",
                "",
                email_pool_file=str(pool_path),
                email_pool_state_path=str(state_path),
            )
            second = MailProvider(
                "imap.example.com",
                993,
                "inbox@example.com",
                "auth",
                "",
                email_pool_file=str(pool_path),
                email_pool_state_path=str(state_path),
            )

            self.assertEqual(first.create_mailbox(), "first@example.com")
            self.assertEqual(second.create_mailbox(), "second@example.com")
            with self.assertRaisesRegex(RuntimeError, "邮箱池已耗尽"):
                second.create_mailbox()

            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(state["next_index"], 2)
            self.assertEqual(state["pool_size"], 2)
            self.assertEqual(state["last_email"], "second@example.com")

    def test_pool_can_reuse_when_enabled(self):
        provider = MailProvider(
            "imap.example.com",
            993,
            "inbox@example.com",
            "auth",
            "",
            email_pool=["only@example.com"],
            email_pool_reuse=True,
        )

        self.assertEqual(provider.create_mailbox(), "only@example.com")
        self.assertEqual(provider.create_mailbox(), "only@example.com")


if __name__ == "__main__":
    unittest.main()

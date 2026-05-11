import importlib.util
import re
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("browser_register.py")


def _load_module():
    spec = importlib.util.spec_from_file_location("browser_register_for_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BrowserRegisterScreenshotNamingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load_module()

    def test_beijing_timestamp_format_is_filename_safe(self):
        stamp = self.mod._beijing_timestamp()
        self.assertRegex(stamp, r"^\d{8}_\d{6}_BJT$")

    def test_safe_filename_part_strips_unsafe_characters(self):
        value = self.mod._safe_filename_part("OTP: email-verification重试 / bad:name?*")
        self.assertEqual(value, "otp_email-verification_bad_name")
        self.assertIsNotNone(re.fullmatch(r"[A-Za-z0-9._-]+", value))

    def test_safe_filename_part_uses_fallback_for_empty_input(self):
        self.assertEqual(self.mod._safe_filename_part("????", fallback="stage"), "stage")


if __name__ == "__main__":
    unittest.main()

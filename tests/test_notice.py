from pathlib import Path
import unittest

from cishen_clicker.notice import NOTICE_TEXT


REQUIRED_PHRASES = ("开发所属工会", "太虚殿", "完全免费", "仅供学习", "禁止售卖")
PROJECT_ROOT = Path(__file__).resolve().parents[1]


class NoticeTests(unittest.TestCase):
    def test_notice_text_contains_required_phrases(self):
        for phrase in REQUIRED_PHRASES:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, NOTICE_TEXT)

    def test_readme_contains_notice(self):
        readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")

        for phrase in REQUIRED_PHRASES:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, readme)

    def test_packaged_notice_file_contains_notice(self):
        notice = (PROJECT_ROOT / "NOTICE.txt").read_text(encoding="utf-8")

        for phrase in REQUIRED_PHRASES:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, notice)

    def test_pack_script_includes_notice_file(self):
        pack_script = (PROJECT_ROOT / "pack.ps1").read_text(encoding="utf-8")

        self.assertIn("NOTICE.txt;.", pack_script)


if __name__ == "__main__":
    unittest.main()

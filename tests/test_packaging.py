from pathlib import Path
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class PackagingTests(unittest.TestCase):
    def test_pack_script_uses_legacy_windows_compatible_python(self):
        script = (PROJECT_ROOT / "pack.ps1").read_text(encoding="utf-8")

        self.assertIn("-3.7", script)
        self.assertIn("requirements-pack-win7.txt", script)
        self.assertIn("pyinstaller==5.13.2", script)
        self.assertIn("NOTICE.txt;.", script)
        self.assertIn('"cishen assistant"', script)
        self.assertIn("次神助手.zip", script)
        self.assertNotIn("--contents-directory", script)

    def test_pack_requirements_pin_python37_compatible_dependencies(self):
        requirements = (PROJECT_ROOT / "requirements-pack-win7.txt").read_text(encoding="utf-8")

        self.assertIn("numpy==1.21.6", requirements)
        self.assertIn("opencv-python==4.5.5.64", requirements)
        self.assertIn("pyautogui==0.9.54", requirements)

    def test_readme_mentions_old_windows_packaging_error(self):
        readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("api-ms-win-core-path-l1-1-0.dll", readme)
        self.assertIn(".\\pack.ps1", readme)
        self.assertIn("Python 3.7", readme)

    def test_readme_has_release_download_guidance(self):
        readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")

        self.assertTrue(readme.startswith("# 次神：光之觉醒PC端助手"))
        self.assertIn("次神助手.zip", readme)
        self.assertIn("cishen assistant.exe", readme)
        self.assertIn("Source code (zip)", readme)
        self.assertIn("Source code (tar.gz)", readme)
        self.assertIn("当前版本仅实现了挖矿模块", readme)

    def test_default_config_starts_on_mining_module(self):
        import json

        raw = json.loads((PROJECT_ROOT / "config.json").read_text(encoding="utf-8"))

        self.assertEqual(raw["active_module"], "mining")


if __name__ == "__main__":
    unittest.main()

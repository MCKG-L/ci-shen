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


if __name__ == "__main__":
    unittest.main()

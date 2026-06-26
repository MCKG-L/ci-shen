from pathlib import Path
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class PackagingTests(unittest.TestCase):
    def test_pack_script_builds_legacy_zip_package(self):
        script = (PROJECT_ROOT / "pack.ps1").read_text(encoding="utf-8")

        self.assertIn("-3.7", script)
        self.assertIn("requirements-pack-win7.txt", script)
        self.assertIn("pyinstaller==5.13.2", script)
        self.assertIn("cishen-assistant.spec", script)
        self.assertIn("Compress-Archive", script)
        self.assertIn("cishen-assistant.zip", script)
        self.assertNotIn("installer.iss", script)
        self.assertNotIn("ISCC", script)
        self.assertNotIn("dist-installer", script)
        self.assertNotIn("--contents-directory", script)

    def test_pack_setup_script_builds_setup_installer(self):
        script = (PROJECT_ROOT / "pack-setup.ps1").read_text(encoding="utf-8")

        self.assertIn("-3.7", script)
        self.assertIn("requirements-pack-win7.txt", script)
        self.assertIn("pyinstaller==5.13.2", script)
        self.assertIn("cishen-assistant.spec", script)
        self.assertIn("installer.iss", script)
        self.assertIn("ISCC", script)
        self.assertIn("InstallLocation", script)
        self.assertIn("dist-installer", script)
        self.assertNotIn("Compress-Archive", script)
        self.assertNotIn("--contents-directory", script)

    def test_pack_setup_script_uses_ascii_only_runtime_text(self):
        script = (PROJECT_ROOT / "pack-setup.ps1").read_text(encoding="utf-8")

        self.assertTrue(script.isascii())

    def test_pyinstaller_spec_includes_runtime_files(self):
        spec = (PROJECT_ROOT / "cishen-assistant.spec").read_text(encoding="utf-8")

        self.assertIn("('config.json', '.')", spec)
        self.assertIn("('NOTICE.txt', '.')", spec)
        self.assertIn("('resources', 'resources')", spec)
        self.assertIn("name='cishen-assistant'", spec)
        self.assertIn("icon='resources\\\\avatar.ico'", spec)

    def test_installer_script_installs_collected_app(self):
        installer = (PROJECT_ROOT / "installer.iss").read_text(encoding="utf-8")

        self.assertIn("#define AppVersion", installer)
        self.assertIn("AppName=次神助手", installer)
        self.assertIn("DisableDirPage=no", installer)
        self.assertIn("PrivilegesRequired=lowest", installer)
        self.assertIn("DefaultDirName={localappdata}\\Programs\\cishen-assistant", installer)
        self.assertIn("OutputDir=dist-installer", installer)
        self.assertIn("OutputBaseFilename=cishen-assistant-setup-{#AppVersion}", installer)
        self.assertIn('Source: "dist\\cishen-assistant\\*"; DestDir: "{app}"', installer)
        self.assertIn('Filename: "{app}\\cishen-assistant.exe"', installer)
        self.assertIn('Name: "{autodesktop}\\次神助手"', installer)

    def test_installer_wizard_uses_simplified_chinese(self):
        installer = (PROJECT_ROOT / "installer.iss").read_text(encoding="utf-8")
        language_file = PROJECT_ROOT / "installer" / "ChineseSimplified.isl"

        self.assertIn('MessagesFile: ".\\installer\\ChineseSimplified.isl"', installer)
        self.assertNotIn("compiler:Default.isl", installer)
        self.assertNotIn("LicenseFile=LICENSE", installer)
        self.assertIn("InfoBeforeFile=NOTICE.txt", installer)
        self.assertTrue(language_file.exists())
        self.assertIn("ButtonNext=下一步", language_file.read_text(encoding="utf-8"))

    def test_pack_requirements_pin_python37_compatible_dependencies(self):
        requirements = (PROJECT_ROOT / "requirements-pack-win7.txt").read_text(encoding="utf-8")

        self.assertIn("numpy==1.21.6", requirements)
        self.assertIn("opencv-python==4.5.5.64", requirements)
        self.assertIn("pyautogui==0.9.54", requirements)

    def test_readme_mentions_old_windows_packaging_error(self):
        readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("api-ms-win-core-path-l1-1-0.dll", readme)
        self.assertIn(".\\pack-setup.ps1", readme)
        self.assertIn("Python 3.7", readme)

    def test_readme_has_release_download_guidance(self):
        readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")

        self.assertTrue(readme.startswith("# 次神：光之觉醒PC端助手"))
        self.assertIn("cishen-assistant-setup", readme)
        self.assertIn("运行安装器", readme)
        self.assertIn("开始菜单", readme)
        self.assertIn("Source code (zip)", readme)
        self.assertIn("Source code (tar.gz)", readme)
        self.assertIn("当前版本仅实现了挖矿模块", readme)

    def test_default_config_starts_on_mining_module(self):
        import json

        raw = json.loads((PROJECT_ROOT / "config.json").read_text(encoding="utf-8"))

        self.assertEqual(raw["active_module"], "mining")


if __name__ == "__main__":
    unittest.main()

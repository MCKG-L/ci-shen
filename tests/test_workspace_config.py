import json
import unittest

from cishen_clicker.workspace_config import WorkspaceConfig, load_workspace_config, save_workspace_config


class WorkspaceConfigTests(unittest.TestCase):
    def test_load_workspace_config_migrates_legacy_flat_mining_config(self):
        with self.subTest("legacy flat config"):
            from tempfile import TemporaryDirectory
            from pathlib import Path

            with TemporaryDirectory() as tmp:
                path = Path(tmp) / "config.json"
                path.write_text(
                    json.dumps(
                        {
                            "window_title": "game",
                            "mine_area": {"x": 1, "y": 2, "width": 3, "height": 4},
                            "rows": 7,
                            "cols": 6,
                        },
                        ensure_ascii=False,
                    ),
                    encoding="utf-8",
                )

                config = load_workspace_config(path)

        self.assertEqual(config.active_module, "mining")
        self.assertEqual(config.modules["mining"]["window_title"], "game")
        self.assertEqual(config.modules["mining"]["rows"], 7)

    def test_load_workspace_config_reads_modular_config(self):
        from tempfile import TemporaryDirectory
        from pathlib import Path

        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            path.write_text(
                json.dumps(
                    {
                        "active_module": "dungeon",
                        "modules": {
                            "mining": {"window_title": "mine"},
                            "dungeon": {"window_title": "dungeon"},
                        },
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            config = load_workspace_config(path)

        self.assertEqual(config.active_module, "dungeon")
        self.assertEqual(config.modules["dungeon"]["window_title"], "dungeon")
        self.assertEqual(config.modules["mining"]["window_title"], "mine")

    def test_save_workspace_config_writes_modular_config(self):
        from tempfile import TemporaryDirectory
        from pathlib import Path

        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"

            save_workspace_config(
                path,
                WorkspaceConfig(
                    active_module="dungeon",
                    modules={
                        "mining": {"window_title": "mine"},
                        "dungeon": {"window_title": "dungeon"},
                    },
                ),
            )

            raw = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(raw["active_module"], "dungeon")
        self.assertEqual(raw["modules"]["mining"]["window_title"], "mine")
        self.assertEqual(raw["modules"]["dungeon"]["window_title"], "dungeon")


if __name__ == "__main__":
    unittest.main()

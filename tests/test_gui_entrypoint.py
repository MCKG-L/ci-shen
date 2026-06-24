from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


class GuiEntrypointTests(unittest.TestCase):
    def test_gui_module_can_be_loaded_as_standalone_script(self) -> None:
        gui_path = Path(__file__).resolve().parents[1] / "cishen_clicker" / "gui.py"
        spec = importlib.util.spec_from_file_location("standalone_gui", gui_path)
        self.assertIsNotNone(spec)
        module = importlib.util.module_from_spec(spec)

        assert spec.loader is not None
        spec.loader.exec_module(module)

        self.assertTrue(hasattr(module, "MiningGui"))


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest
from unittest import mock


class GuiEntrypointTests(unittest.TestCase):
    def test_gui_module_can_be_loaded_as_standalone_script(self) -> None:
        gui_path = Path(__file__).resolve().parents[1] / "cishen_clicker" / "gui.py"
        spec = importlib.util.spec_from_file_location("standalone_gui", gui_path)
        self.assertIsNotNone(spec)
        module = importlib.util.module_from_spec(spec)

        assert spec.loader is not None
        spec.loader.exec_module(module)

        self.assertTrue(hasattr(module, "MiningGui"))

    def test_gui_main_sets_dpi_awareness_before_creating_tk_root(self) -> None:
        from cishen_clicker import gui

        events = []

        class FakeRoot:
            def __init__(self):
                events.append("tk")

            def mainloop(self):
                events.append("mainloop")

        with mock.patch("cishen_clicker.gui.set_process_dpi_awareness", create=True) as set_dpi, \
             mock.patch("cishen_clicker.gui.tk.Tk", FakeRoot), \
             mock.patch("cishen_clicker.gui.MiningGui", side_effect=lambda _root: events.append("gui")):
            set_dpi.side_effect = lambda: events.append("dpi")

            gui.main()

        self.assertEqual(events[:2], ["dpi", "tk"])


if __name__ == "__main__":
    unittest.main()

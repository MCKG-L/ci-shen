import unittest
from unittest import mock

from cishen_clicker.control import ControlState
from cishen_clicker.gui import MiningGui


class DummyRoot:
    def after(self, delay, callback):
        return None

    def title(self, text):
        return None

    def geometry(self, value):
        return None

    def resizable(self, width, height):
        return None

    def minsize(self, width, height):
        return None

    def maxsize(self, width, height):
        return None

    def protocol(self, name, callback):
        return None


class FakeStringVar:
    def __init__(self, value=""):
        self.value = value

    def set(self, value):
        self.value = value

    def get(self):
        return self.value


class GuiStartTests(unittest.TestCase):
    @mock.patch("cishen_clicker.gui.install_gui_hotkeys")
    @mock.patch("cishen_clicker.gui.load_raw_config", return_value={
        "click_delay_seconds": 0.03,
        "loop_interval_seconds": 0.3,
        "max_targets_per_round": 8,
    })
    @mock.patch("cishen_clicker.gui.extract_gui_values", return_value={
        "click_delay_seconds": "0.03",
        "loop_interval_seconds": "0.3",
        "max_targets_per_round": "8",
    })
    @mock.patch("cishen_clicker.gui.load_config")
    @mock.patch("cishen_clicker.gui.load_templates", return_value=[])
    @mock.patch("cishen_clicker.gui.MiningStrategy", return_value=object())
    @mock.patch("cishen_clicker.gui.run_once")
    def test_worker_loop_defaults_to_live_clicking(
        self,
        run_once,
        _strategy,
        _load_templates,
        _load_config,
        _extract_gui_values,
        _load_raw_config,
        _install_hotkeys,
    ):
        control = ControlState()
        control.start()

        class Config:
            window_title = "game"
            templates_dir = "templates"
            loop_interval_seconds = 0
            tool_interval_loops = 4
            debug_dir = None

        _load_config.return_value = Config()

        def fake_run_once(*args, **kwargs):
            self.assertTrue(kwargs["live"])
            self.assertFalse(kwargs["debug"])
            kwargs["control"].stop()
            return []

        run_once.side_effect = fake_run_once

        with mock.patch("cishen_clicker.gui.tk.StringVar", FakeStringVar), \
             mock.patch("cishen_clicker.gui.ttk.Frame"), \
             mock.patch("cishen_clicker.gui.ttk.LabelFrame"), \
             mock.patch("cishen_clicker.gui.ttk.Label"), \
             mock.patch("cishen_clicker.gui.ttk.Entry"), \
             mock.patch("cishen_clicker.gui.ttk.Button"), \
             mock.patch("cishen_clicker.gui.ScrolledText"):
            gui = MiningGui(DummyRoot())

        gui._worker_loop("config.json", control)

        self.assertTrue(control.should_stop())

    @mock.patch("cishen_clicker.gui.install_gui_hotkeys")
    @mock.patch("cishen_clicker.gui.load_raw_config", return_value={
        "click_delay_seconds": 0.03,
        "loop_interval_seconds": 0.3,
        "max_targets_per_round": 8,
    })
    @mock.patch("cishen_clicker.gui.extract_gui_values", return_value={
        "click_delay_seconds": "0.03",
        "loop_interval_seconds": "0.3",
        "max_targets_per_round": "8",
    })
    @mock.patch("cishen_clicker.gui.load_config")
    @mock.patch("cishen_clicker.gui.load_templates", return_value=[])
    @mock.patch("cishen_clicker.gui.MiningStrategy", return_value=object())
    @mock.patch("cishen_clicker.gui.run_once")
    def test_worker_loop_stops_when_run_once_reports_login_conflict(
        self,
        run_once,
        _strategy,
        _load_templates,
        _load_config,
        _extract_gui_values,
        _load_raw_config,
        _install_hotkeys,
    ):
        control = ControlState()
        control.start()

        class Config:
            window_title = "game"
            templates_dir = "templates"
            loop_interval_seconds = 0
            tool_interval_loops = 4
            debug_dir = None

        _load_config.return_value = Config()

        def fake_run_once(*args, **kwargs):
            kwargs["control"].stop()
            return []

        run_once.side_effect = fake_run_once

        with mock.patch("cishen_clicker.gui.tk.StringVar", FakeStringVar), \
             mock.patch("cishen_clicker.gui.ttk.Frame"), \
             mock.patch("cishen_clicker.gui.ttk.LabelFrame"), \
             mock.patch("cishen_clicker.gui.ttk.Label"), \
             mock.patch("cishen_clicker.gui.ttk.Entry"), \
             mock.patch("cishen_clicker.gui.ttk.Button"), \
             mock.patch("cishen_clicker.gui.ScrolledText"):
            gui = MiningGui(DummyRoot())

        gui._worker_loop("config.json", control)

        self.assertTrue(control.should_stop())


if __name__ == "__main__":
    unittest.main()

import unittest
from unittest import mock

import tkinter as tk

from cishen_clicker.gui import MiningGui
from cishen_clicker.notice import NOTICE_TEXT, NOTICE_TITLE


created_labels = []
created_label_frames = []


class FakeEntry:
    def __init__(self, *args, **kwargs):
        pass

    def pack(self, *args, **kwargs):
        return None

    def grid(self, *args, **kwargs):
        return None


class FakeLabel:
    def __init__(self, *args, **kwargs):
        self.text = kwargs.get("text", "")
        created_labels.append(self)

    def pack(self, *args, **kwargs):
        return None

    def grid(self, *args, **kwargs):
        return None


class FakeButton(FakeLabel):
    pass


class FakeFrame:
    def __init__(self, *args, **kwargs):
        self.configured = []

    def pack(self, *args, **kwargs):
        return None

    def columnconfigure(self, *args, **kwargs):
        self.configured.append((args, kwargs))


class FakeLabelFrame(FakeFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.text = kwargs.get("text", "")
        created_label_frames.append(self)


class FakeScrolledText:
    def __init__(self, *args, **kwargs):
        pass

    def pack(self, *args, **kwargs):
        return None

    def configure(self, *args, **kwargs):
        return None

    def insert(self, *args, **kwargs):
        return None

    def see(self, *args, **kwargs):
        return None


class FakeStringVar:
    def __init__(self, value=""):
        self._value = value

    def set(self, value):
        self._value = value

    def get(self):
        return self._value


class FakeTk:
    def __init__(self):
        self.geometry_calls = []
        self.resizable_calls = []
        self.minsize_calls = []
        self.maxsize_calls = []
        self.after_calls = []
        self.protocol_calls = []

    def title(self, text):
        self.title_text = text

    def geometry(self, value):
        self.geometry_calls.append(value)

    def resizable(self, width, height):
        self.resizable_calls.append((width, height))

    def minsize(self, width, height):
        self.minsize_calls.append((width, height))

    def maxsize(self, width, height):
        self.maxsize_calls.append((width, height))

    def after(self, delay, callback):
        self.after_calls.append((delay, callback))

    def protocol(self, name, callback):
        self.protocol_calls.append((name, callback))


class MiningGuiWindowTests(unittest.TestCase):
    def setUp(self):
        created_labels.clear()
        created_label_frames.clear()

    @mock.patch("cishen_clicker.gui.ttk.Frame", FakeFrame)
    @mock.patch("cishen_clicker.gui.ttk.LabelFrame", FakeLabelFrame)
    @mock.patch("cishen_clicker.gui.ttk.Label", FakeLabel)
    @mock.patch("cishen_clicker.gui.ttk.Entry", FakeEntry)
    @mock.patch("cishen_clicker.gui.ttk.Button", FakeButton)
    @mock.patch("cishen_clicker.gui.ScrolledText", FakeScrolledText)
    @mock.patch("cishen_clicker.gui.tk.StringVar", FakeStringVar)
    @mock.patch("cishen_clicker.gui.load_raw_config", return_value={
        "click_delay_seconds": 0.03,
        "click_hold_seconds": 0.08,
        "loop_interval_seconds": 0.3,
        "max_targets_per_round": 8,
    })
    @mock.patch("cishen_clicker.gui.extract_gui_values", return_value={
        "click_delay_seconds": "0.03",
        "click_hold_seconds": "0.08",
        "loop_interval_seconds": "0.3",
        "max_targets_per_round": "8",
    })
    @mock.patch("cishen_clicker.gui.install_gui_hotkeys")
    def test_window_is_fixed_size_and_uses_three_fields(
        self,
        _install_hotkeys,
        _extract_gui_values,
        _load_raw_config,
    ):
        root = FakeTk()

        gui = MiningGui(root)

        self.assertEqual(root.geometry_calls, ["760x620"])
        self.assertEqual(root.resizable_calls, [(False, False)])
        self.assertEqual(root.minsize_calls, [(760, 620)])
        self.assertEqual(root.maxsize_calls, [(760, 620)])
        self.assertEqual(list(gui.field_vars.keys()), [
            "click_delay_seconds",
            "click_hold_seconds",
            "loop_interval_seconds",
            "max_targets_per_round",
        ])

    @mock.patch("cishen_clicker.gui.ttk.Frame", FakeFrame)
    @mock.patch("cishen_clicker.gui.ttk.LabelFrame", FakeLabelFrame)
    @mock.patch("cishen_clicker.gui.ttk.Label", FakeLabel)
    @mock.patch("cishen_clicker.gui.ttk.Entry", FakeEntry)
    @mock.patch("cishen_clicker.gui.ttk.Button", FakeButton)
    @mock.patch("cishen_clicker.gui.ScrolledText", FakeScrolledText)
    @mock.patch("cishen_clicker.gui.tk.StringVar", FakeStringVar)
    @mock.patch("cishen_clicker.gui.load_raw_config", return_value={
        "click_delay_seconds": 0.03,
        "click_hold_seconds": 0.08,
        "loop_interval_seconds": 0.3,
        "max_targets_per_round": 8,
    })
    @mock.patch("cishen_clicker.gui.extract_gui_values", return_value={
        "click_delay_seconds": "0.03",
        "click_hold_seconds": "0.08",
        "loop_interval_seconds": "0.3",
        "max_targets_per_round": "8",
    })
    @mock.patch("cishen_clicker.gui.install_gui_hotkeys")
    def test_window_shows_free_learning_only_notice(
        self,
        _install_hotkeys,
        _extract_gui_values,
        _load_raw_config,
    ):
        MiningGui(FakeTk())

        self.assertIn(NOTICE_TITLE, [frame.text for frame in created_label_frames])
        self.assertIn(NOTICE_TEXT, [label.text for label in created_labels])


if __name__ == "__main__":
    unittest.main()

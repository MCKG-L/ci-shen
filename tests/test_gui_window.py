import unittest
from unittest import mock

import tkinter as tk

from cishen_clicker.gui import MiningGui
from cishen_clicker.notice import (
    MODULE_SWITCH_TEXT,
    NOTICE_TEXT,
    NOTICE_TITLE,
    PROJECT_INFO_PREFIX,
    PROJECT_INFO_SUFFIX,
    PROJECT_REPOSITORY_LABEL,
    PROJECT_REPOSITORY_URL,
    PROJECT_INFO_TEXT,
    PROJECT_INFO_TITLE,
    USAGE_TEXT,
    USAGE_TITLE,
)
from cishen_clicker.workspace_config import WorkspaceConfig


created_labels = []
created_label_frames = []
created_buttons = []
created_checkbuttons = []


class FakeEntry:
    def __init__(self, *args, **kwargs):
        pass

    def pack(self, *args, **kwargs):
        return None

    def grid(self, *args, **kwargs):
        return None


class FakeCheckbutton:
    def __init__(self, *args, **kwargs):
        self.parent = args[0] if args else None
        self.text = kwargs.get("text", "")
        self.grid_calls = []
        created_checkbuttons.append(self)

    def grid(self, *args, **kwargs):
        self.grid_calls.append((args, kwargs))
        return None


class FakeCombobox:
    def __init__(self, *args, **kwargs):
        self.values = kwargs.get("values", ())

    def pack(self, *args, **kwargs):
        return None

    def bind(self, *args, **kwargs):
        return None


class FakeLabel:
    def __init__(self, *args, **kwargs):
        self.parent = args[0] if args else None
        self.text = kwargs.get("text", "")
        self.foreground = kwargs.get("foreground")
        self.cursor = kwargs.get("cursor")
        self.font = kwargs.get("font")
        self.bind_calls = []
        created_labels.append(self)

    def pack(self, *args, **kwargs):
        return None

    def grid(self, *args, **kwargs):
        return None

    def bind(self, *args, **kwargs):
        self.bind_calls.append((args, kwargs))
        return None


class FakeButton(FakeLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.command = kwargs.get("command")
        created_buttons.append(self)


class FakeFrame:
    def __init__(self, *args, **kwargs):
        self.parent = args[0] if args else None
        self.configured = []
        self.grid_calls = []

    def pack(self, *args, **kwargs):
        return None

    def columnconfigure(self, *args, **kwargs):
        self.configured.append((args, kwargs))

    def grid(self, *args, **kwargs):
        self.grid_calls.append((args, kwargs))
        return None

    def winfo_children(self):
        return []

    def destroy(self):
        return None


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


class FakeWorker:
    def __init__(self):
        self.join_calls = []
        self.alive = True

    def is_alive(self):
        return self.alive

    def join(self, timeout=None):
        self.join_calls.append(timeout)
        self.alive = False


class FakeControl:
    def __init__(self):
        self.stop_calls = 0

    def stop(self):
        self.stop_calls += 1

    def is_running(self):
        return False


class FakeActiveWorker(FakeWorker):
    pass


class MiningGuiWindowTests(unittest.TestCase):
    def setUp(self):
        created_labels.clear()
        created_label_frames.clear()
        created_buttons.clear()
        created_checkbuttons.clear()

    @mock.patch("cishen_clicker.gui.ttk.Frame", FakeFrame)
    @mock.patch("cishen_clicker.gui.ttk.LabelFrame", FakeLabelFrame)
    @mock.patch("cishen_clicker.gui.ttk.Label", FakeLabel)
    @mock.patch("cishen_clicker.gui.ttk.Entry", FakeEntry)
    @mock.patch("cishen_clicker.gui.ttk.Button", FakeButton)
    @mock.patch("cishen_clicker.gui.ttk.Combobox", FakeCombobox)
    @mock.patch("cishen_clicker.gui.ScrolledText", FakeScrolledText)
    @mock.patch("cishen_clicker.gui.tk.StringVar", FakeStringVar)
    @mock.patch("cishen_clicker.gui.load_workspace_config", return_value=WorkspaceConfig(
        active_module="mining",
        modules={
            "mining": {
                "click_delay_seconds": 0.03,
                "click_hold_seconds": 0.08,
                "loop_interval_seconds": 0.3,
                "max_targets_per_round": 8,
                "max_runtime_minutes": 30,
                "max_pickaxe_clicks": 500,
                "tool_interval_loops": 3,
                "use_drill": True,
                "use_bomb": False,
            },
            "dungeon": {"window_title": "副本"},
        },
    ))
    @mock.patch("cishen_clicker.gui.ttk.Checkbutton", FakeCheckbutton)
    def test_window_opens_home_page_with_module_buttons(
        self,
        _load_workspace_config,
    ):
        root = FakeTk()

        gui = MiningGui(root)

        self.assertEqual(root.geometry_calls, ["760x700"])
        self.assertEqual(root.resizable_calls, [(False, False)])
        self.assertEqual(root.minsize_calls, [(760, 700)])
        self.assertEqual(root.maxsize_calls, [(760, 700)])
        self.assertEqual(gui.current_page, "home")
        self.assertEqual(gui.module_var.get(), "mining")
        self.assertEqual(gui.module_options, ["mining", "dungeon", "summon", "garden"])
        self.assertEqual(gui.field_vars, {})
        button_texts = [button.text for button in created_buttons]
        self.assertIn("挖矿", button_texts)
        self.assertIn("副本", button_texts)
        self.assertIn("召唤", button_texts)
        self.assertIn("菜园管理", button_texts)

    @mock.patch("cishen_clicker.gui.ttk.Frame", FakeFrame)
    @mock.patch("cishen_clicker.gui.ttk.LabelFrame", FakeLabelFrame)
    @mock.patch("cishen_clicker.gui.ttk.Label", FakeLabel)
    @mock.patch("cishen_clicker.gui.ttk.Entry", FakeEntry)
    @mock.patch("cishen_clicker.gui.ttk.Button", FakeButton)
    @mock.patch("cishen_clicker.gui.ttk.Combobox", FakeCombobox)
    @mock.patch("cishen_clicker.gui.ScrolledText", FakeScrolledText)
    @mock.patch("cishen_clicker.gui.tk.StringVar", FakeStringVar)
    @mock.patch("cishen_clicker.gui.load_workspace_config", return_value=WorkspaceConfig(
        active_module="mining",
        modules={
            "mining": {
                "click_delay_seconds": 0.03,
                "click_hold_seconds": 0.08,
                "loop_interval_seconds": 0.3,
                "max_targets_per_round": 8,
                "max_runtime_minutes": 30,
                "max_pickaxe_clicks": 500,
                "tool_interval_loops": 3,
                "use_drill": True,
                "use_bomb": False,
            },
            "dungeon": {"window_title": "副本"},
        },
    ))
    @mock.patch("cishen_clicker.gui.ttk.Checkbutton", FakeCheckbutton)
    def test_open_mining_module_page_uses_mining_fields_and_return_button(
        self,
        _load_workspace_config,
    ):
        gui = MiningGui(FakeTk())

        gui._open_module("mining")

        self.assertEqual(gui.current_page, "module")
        self.assertEqual(gui.module_var.get(), "mining")
        self.assertEqual(list(gui.field_vars.keys()), [
            "click_delay_seconds",
            "click_hold_seconds",
            "loop_interval_seconds",
            "max_targets_per_round",
            "max_runtime_minutes",
            "max_pickaxe_clicks",
            "tool_interval_loops",
            "use_drill",
            "use_bomb",
        ])
        self.assertIn("返回首页", [button.text for button in created_buttons])
        self.assertIn(MODULE_SWITCH_TEXT, [label.text for label in created_labels])

        gui._show_home_page()

        self.assertEqual(gui.current_page, "home")
        self.assertEqual(gui.field_vars, {})

    @mock.patch("cishen_clicker.gui.ttk.Frame", FakeFrame)
    @mock.patch("cishen_clicker.gui.ttk.LabelFrame", FakeLabelFrame)
    @mock.patch("cishen_clicker.gui.ttk.Label", FakeLabel)
    @mock.patch("cishen_clicker.gui.ttk.Entry", FakeEntry)
    @mock.patch("cishen_clicker.gui.ttk.Button", FakeButton)
    @mock.patch("cishen_clicker.gui.ttk.Combobox", FakeCombobox)
    @mock.patch("cishen_clicker.gui.ScrolledText", FakeScrolledText)
    @mock.patch("cishen_clicker.gui.tk.StringVar", FakeStringVar)
    @mock.patch("cishen_clicker.gui.load_workspace_config", return_value=WorkspaceConfig(
        active_module="mining",
        modules={
            "mining": {
                "click_delay_seconds": 0.03,
                "click_hold_seconds": 0.08,
                "loop_interval_seconds": 0.3,
                "max_targets_per_round": 8,
                "max_runtime_minutes": 30,
                "max_pickaxe_clicks": 500,
                "tool_interval_loops": 3,
                "use_drill": True,
                "use_bomb": False,
            },
            "dungeon": {"window_title": "副本"},
        },
    ))
    @mock.patch("cishen_clicker.gui.ttk.Checkbutton", FakeCheckbutton)
    def test_tool_checkboxes_share_one_grid_cell_with_left_alignment_and_gap(
        self,
        _load_workspace_config,
    ):
        gui = MiningGui(FakeTk())

        gui._open_module("mining")

        checkbuttons = {checkbutton.text: checkbutton for checkbutton in created_checkbuttons}
        drill = checkbuttons["使用钻头"]
        bomb = checkbuttons["使用炸药"]
        tool_frame = drill.parent
        self.assertIs(tool_frame, bomb.parent)
        self.assertIsNot(tool_frame, gui.params_frame)
        self.assertEqual(tool_frame.grid_calls[0][1]["column"], 2)
        self.assertEqual(tool_frame.grid_calls[0][1]["columnspan"], 2)
        self.assertEqual(tool_frame.configured, [])
        self.assertEqual(drill.grid_calls[0][1]["column"], 0)
        self.assertEqual(drill.grid_calls[0][1]["sticky"], tk.W)
        self.assertEqual(bomb.grid_calls[0][1]["column"], 1)
        self.assertEqual(bomb.grid_calls[0][1]["sticky"], tk.W)
        self.assertEqual(bomb.grid_calls[0][1]["padx"], (24, 0))

    @mock.patch("cishen_clicker.gui.ttk.Frame", FakeFrame)
    @mock.patch("cishen_clicker.gui.ttk.LabelFrame", FakeLabelFrame)
    @mock.patch("cishen_clicker.gui.ttk.Label", FakeLabel)
    @mock.patch("cishen_clicker.gui.ttk.Entry", FakeEntry)
    @mock.patch("cishen_clicker.gui.ttk.Button", FakeButton)
    @mock.patch("cishen_clicker.gui.ttk.Combobox", FakeCombobox)
    @mock.patch("cishen_clicker.gui.ScrolledText", FakeScrolledText)
    @mock.patch("cishen_clicker.gui.tk.StringVar", FakeStringVar)
    @mock.patch("cishen_clicker.gui.load_workspace_config", return_value=WorkspaceConfig(
        active_module="mining",
        modules={"mining": {}, "dungeon": {}, "summon": {}, "garden": {}},
    ))
    @mock.patch("cishen_clicker.gui.ttk.Checkbutton", FakeCheckbutton)
    def test_window_shows_free_learning_only_notice(
        self,
        _load_workspace_config,
    ):
        MiningGui(FakeTk())

        self.assertIn(NOTICE_TITLE, [frame.text for frame in created_label_frames])
        self.assertIn(NOTICE_TEXT, [label.text for label in created_labels])

    @mock.patch("cishen_clicker.gui.ttk.Frame", FakeFrame)
    @mock.patch("cishen_clicker.gui.ttk.LabelFrame", FakeLabelFrame)
    @mock.patch("cishen_clicker.gui.ttk.Label", FakeLabel)
    @mock.patch("cishen_clicker.gui.ttk.Entry", FakeEntry)
    @mock.patch("cishen_clicker.gui.ttk.Button", FakeButton)
    @mock.patch("cishen_clicker.gui.ttk.Combobox", FakeCombobox)
    @mock.patch("cishen_clicker.gui.ScrolledText", FakeScrolledText)
    @mock.patch("cishen_clicker.gui.tk.StringVar", FakeStringVar)
    @mock.patch("cishen_clicker.gui.load_workspace_config", return_value=WorkspaceConfig(
        active_module="mining",
        modules={"mining": {}, "dungeon": {}, "summon": {}, "garden": {}},
    ))
    @mock.patch("cishen_clicker.gui.ttk.Checkbutton", FakeCheckbutton)
    def test_home_page_shows_usage_notice_and_project_info_in_requested_order(
        self,
        _load_workspace_config,
    ):
        MiningGui(FakeTk())

        frame_titles = [frame.text for frame in created_label_frames]
        self.assertLess(frame_titles.index(USAGE_TITLE), frame_titles.index(NOTICE_TITLE))
        self.assertLess(frame_titles.index(NOTICE_TITLE), frame_titles.index(PROJECT_INFO_TITLE))
        self.assertIn(USAGE_TEXT, [label.text for label in created_labels])
        self.assertIn(NOTICE_TEXT, [label.text for label in created_labels])
        self.assertIn(PROJECT_INFO_PREFIX, [label.text for label in created_labels])
        self.assertIn(PROJECT_REPOSITORY_LABEL, [label.text for label in created_labels])
        self.assertIn(PROJECT_INFO_SUFFIX, [label.text for label in created_labels])

    @mock.patch("cishen_clicker.gui.ttk.Frame", FakeFrame)
    @mock.patch("cishen_clicker.gui.ttk.LabelFrame", FakeLabelFrame)
    @mock.patch("cishen_clicker.gui.ttk.Label", FakeLabel)
    @mock.patch("cishen_clicker.gui.ttk.Entry", FakeEntry)
    @mock.patch("cishen_clicker.gui.ttk.Button", FakeButton)
    @mock.patch("cishen_clicker.gui.ttk.Combobox", FakeCombobox)
    @mock.patch("cishen_clicker.gui.ScrolledText", FakeScrolledText)
    @mock.patch("cishen_clicker.gui.tk.StringVar", FakeStringVar)
    @mock.patch("cishen_clicker.gui.load_workspace_config", return_value=WorkspaceConfig(
        active_module="mining",
        modules={"mining": {}, "dungeon": {}, "summon": {}, "garden": {}},
    ))
    @mock.patch("cishen_clicker.gui.ttk.Checkbutton", FakeCheckbutton)
    def test_project_repository_is_clickable_link(
        self,
        _load_workspace_config,
    ):
        gui = MiningGui(FakeTk())

        link_label = next(label for label in created_labels if label.text == PROJECT_REPOSITORY_LABEL)
        self.assertEqual(link_label.foreground, "#0563c1")
        self.assertEqual(link_label.cursor, "hand2")
        self.assertTrue(link_label.bind_calls)

        with mock.patch("cishen_clicker.gui.webbrowser.open") as open_browser:
            callback = link_label.bind_calls[0][0][1]
            callback(None)

        open_browser.assert_called_once_with(PROJECT_REPOSITORY_URL)

    @mock.patch("cishen_clicker.gui.ttk.Frame", FakeFrame)
    @mock.patch("cishen_clicker.gui.ttk.LabelFrame", FakeLabelFrame)
    @mock.patch("cishen_clicker.gui.ttk.Label", FakeLabel)
    @mock.patch("cishen_clicker.gui.ttk.Entry", FakeEntry)
    @mock.patch("cishen_clicker.gui.ttk.Button", FakeButton)
    @mock.patch("cishen_clicker.gui.ttk.Combobox", FakeCombobox)
    @mock.patch("cishen_clicker.gui.ScrolledText", FakeScrolledText)
    @mock.patch("cishen_clicker.gui.tk.StringVar", FakeStringVar)
    @mock.patch("cishen_clicker.gui.load_workspace_config", return_value=WorkspaceConfig(
        active_module="mining",
        modules={
            "mining": {"click_delay_seconds": 0.03},
            "dungeon": {},
            "summon": {},
            "garden": {},
        },
    ))
    @mock.patch("cishen_clicker.gui.ttk.Checkbutton", FakeCheckbutton)
    def test_switching_modules_stops_paused_worker_before_opening_new_module(
        self,
        _load_workspace_config,
    ):
        gui = MiningGui(FakeTk())
        gui.current_page = "module"
        gui.workspace_config = WorkspaceConfig(
            active_module="mining",
            modules={
                "mining": {"click_delay_seconds": 0.03},
                "dungeon": {},
                "summon": {},
                "garden": {},
            },
        )
        gui.module_var = FakeStringVar("mining")
        gui.field_vars = {"click_delay_seconds": FakeStringVar("0.05")}
        control = FakeControl()
        worker = FakeWorker()
        gui.control = control
        gui.worker = worker

        gui._open_module("dungeon")

        self.assertEqual(control.stop_calls, 1)
        self.assertEqual(worker.join_calls, [1.0])
        self.assertIsNone(gui.control)
        self.assertIsNone(gui.worker)
        self.assertEqual(gui.current_page, "module")
        self.assertEqual(gui.module_var.get(), "dungeon")

    def test_sync_current_fields_preserves_inactive_module_data(self):
        gui = MiningGui.__new__(MiningGui)
        gui.module_var = FakeStringVar("mining")
        gui.field_vars = {
            "click_delay_seconds": FakeStringVar("0.05"),
            "click_hold_seconds": FakeStringVar("0.08"),
            "loop_interval_seconds": FakeStringVar("0.3"),
            "max_targets_per_round": FakeStringVar("8"),
            "max_runtime_minutes": FakeStringVar(""),
            "max_pickaxe_clicks": FakeStringVar(""),
            "tool_interval_loops": FakeStringVar("4"),
            "use_drill": FakeStringVar("false"),
            "use_bomb": FakeStringVar("false"),
        }
        gui.workspace_config = WorkspaceConfig(
            active_module="mining",
            modules={
                "mining": {"click_delay_seconds": 0.03},
                "dungeon": {"window_title": "副本", "loop_interval_seconds": 0.5},
                "summon": {"window_title": "召唤"},
                "garden": {"window_title": "菜园"},
            },
        )

        gui._sync_current_fields_to_workspace()

        self.assertEqual(gui.workspace_config.modules["mining"]["click_delay_seconds"], 0.05)
        self.assertEqual(gui.workspace_config.modules["dungeon"]["window_title"], "副本")
        self.assertEqual(gui.workspace_config.modules["dungeon"]["loop_interval_seconds"], 0.5)
        self.assertEqual(gui.workspace_config.modules["summon"]["window_title"], "召唤")
        self.assertEqual(gui.workspace_config.modules["garden"]["window_title"], "菜园")

if __name__ == "__main__":
    unittest.main()

import queue
import unittest
from pathlib import Path
from unittest import mock

from cishen_clicker.control import ControlState
from cishen_clicker.gui import MiningGui
from cishen_clicker.workspace_config import WorkspaceConfig


class FakeModuleSpec:
    label = "测试模块"

    def __init__(self):
        self.runtime = type("Runtime", (), {"config": type("Config", (), {"loop_interval_seconds": 0})()})()
        self.run_calls = []

    def create_runtime(self, raw_config, config_dir):
        self.raw_config = raw_config
        self.config_dir = config_dir
        return self.runtime

    def run_cycle(self, runtime, **kwargs):
        self.run_calls.append((runtime, kwargs))
        kwargs["control"].stop()
        return []


class FakeStatusVar:
    def __init__(self) -> None:
        self.values = []

    def set(self, value):
        self.values.append(value)


class FakeStoppedControl:
    def __init__(self) -> None:
        self.start_calls = 0

    def start(self) -> None:
        self.start_calls += 1

    def should_stop(self) -> bool:
        return True


class FakeAliveWorker:
    def is_alive(self) -> bool:
        return True


class GuiStartTests(unittest.TestCase):
    @mock.patch("cishen_clicker.gui.load_workspace_config", return_value=WorkspaceConfig(
        active_module="mining",
        modules={"mining": {"window_title": "game"}, "dungeon": {}},
    ))
    def test_worker_loop_dispatches_to_active_module(self, _load_workspace_config):
        control = ControlState()
        control.start()
        module_spec = FakeModuleSpec()
        gui = MiningGui.__new__(MiningGui)
        gui.module_options = ["mining", "dungeon"]
        gui.log_queue = queue.Queue()
        gui._log = lambda message: gui.log_queue.put(message)

        with mock.patch("cishen_clicker.gui.get_module_spec", return_value=module_spec):
            gui._worker_loop(Path("D:/fake/config.json"), control)

        self.assertEqual(module_spec.raw_config, {"window_title": "game"})
        self.assertEqual(module_spec.config_dir, Path("D:/fake"))
        self.assertEqual(len(module_spec.run_calls), 1)
        _runtime, kwargs = module_spec.run_calls[0]
        self.assertTrue(kwargs["live"])
        self.assertFalse(kwargs["debug"])
        self.assertIs(kwargs["control"], control)
        self.assertTrue(control.should_stop())

    def test_start_does_not_resume_worker_that_is_already_stopping(self):
        gui = MiningGui.__new__(MiningGui)
        gui.worker = FakeAliveWorker()
        gui.control = FakeStoppedControl()
        gui.status_var = FakeStatusVar()
        logs = []
        gui._log = logs.append
        gui._save_form = mock.Mock(return_value=Path("D:/fake/config.json"))

        gui._start()

        self.assertEqual(gui.control.start_calls, 0)
        self.assertFalse(gui._save_form.called)
        self.assertIn("正在结束旧任务，请稍后再开始", logs)


if __name__ == "__main__":
    unittest.main()

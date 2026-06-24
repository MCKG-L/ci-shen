import unittest
from pathlib import Path
from unittest import mock

from cishen_clicker.__main__ import main
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
        return ["ok"]


class ModuleDispatchTests(unittest.TestCase):
    @mock.patch("cishen_clicker.__main__.load_workspace_config", return_value=WorkspaceConfig(
        active_module="dungeon",
        modules={"mining": {}, "dungeon": {"window_title": "副本"}},
    ))
    def test_main_dispatches_to_active_module_runner(self, _load_workspace_config):
        module_spec = FakeModuleSpec()

        with mock.patch("cishen_clicker.__main__.get_module_spec", return_value=module_spec), \
             mock.patch("sys.argv", ["cishen", "--config", "D:/fake/config.json", "--once", "--live"]), \
             mock.patch("builtins.print"):
            result = main()

        self.assertEqual(result, 0)
        self.assertEqual(module_spec.raw_config, {"window_title": "副本"})
        self.assertEqual(module_spec.config_dir, Path("D:/fake"))
        self.assertEqual(len(module_spec.run_calls), 1)
        _runtime, kwargs = module_spec.run_calls[0]
        self.assertTrue(kwargs["live"])
        self.assertFalse(kwargs["debug"])


if __name__ == "__main__":
    unittest.main()

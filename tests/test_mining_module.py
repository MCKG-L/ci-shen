import unittest
from pathlib import Path
from unittest import mock

from cishen_clicker.modules import mining
from cishen_clicker.config import AppConfig, Thresholds
from cishen_clicker.control import ControlState
from cishen_clicker.model import Candidate, Cell, GridConfig, Rect
from cishen_clicker.strategy import MiningStrategy
from cishen_clicker.tool_usage import ToolUsageState
from cishen_clicker.windows import WindowRect


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class MiningModuleTests(unittest.TestCase):
    def test_create_runtime_builds_mining_config_and_state(self):
        runtime = mining.create_runtime(
            {
                "window_title": "game",
                "mine_area": {"x": 1, "y": 2, "width": 300, "height": 400},
                "rows": 7,
                "cols": 6,
                "tool_interval_loops": 3,
                "max_runtime_minutes": 2,
                "max_pickaxe_clicks": 50,
                "templates_dir": "templates",
                "debug_dir": "debug",
            },
            Path("D:/fake/project"),
        )

        self.assertEqual(runtime.config.window_title, "game")
        self.assertEqual(runtime.config.tool_interval_loops, 3)
        self.assertEqual(runtime.config.max_runtime_minutes, 2.0)
        self.assertEqual(runtime.config.max_pickaxe_clicks, 50)
        self.assertIsInstance(runtime.strategy, MiningStrategy)
        self.assertIsInstance(runtime.tool_state, ToolUsageState)
        self.assertEqual(runtime.limit_state.pickaxe_clicks, 0)
        self.assertEqual(runtime.templates, [])

    def test_create_runtime_treats_negative_limits_as_unlimited(self):
        runtime = mining.create_runtime(
            {
                "window_title": "game",
                "mine_area": {"x": 1, "y": 2, "width": 300, "height": 400},
                "max_runtime_minutes": -1,
                "max_pickaxe_clicks": -1,
                "templates_dir": "templates",
                "debug_dir": "debug",
            },
            Path("D:/fake/project"),
        )

        self.assertIsNone(runtime.config.max_runtime_minutes)

    def test_create_runtime_converts_legacy_seconds_limit_to_minutes(self):
        runtime = mining.create_runtime(
            {
                "window_title": "game",
                "mine_area": {"x": 1, "y": 2, "width": 300, "height": 400},
                "max_runtime_seconds": 120,
                "templates_dir": "templates",
                "debug_dir": "debug",
            },
            Path("D:/fake/project"),
        )

        self.assertEqual(runtime.config.max_runtime_minutes, 2.0)
        self.assertIsNone(runtime.config.max_pickaxe_clicks)

    @mock.patch("cishen_clicker.modules.mining.locate_window")
    def test_run_cycle_stops_before_screenshot_after_active_time_limit(self, locate_window):
        clock = FakeClock()
        control = ControlState(clock=clock)
        control.start()
        runtime = mining.MiningRuntime(
            config=_config(max_runtime_minutes=0.1),
            templates=[],
            strategy=MiningStrategy(),
            tool_state=ToolUsageState(interval_loops=4),
            limit_state=mining.MiningLimitState(clock=clock),
        )
        logs = []

        clock.advance(3)
        control.pause()
        clock.advance(100)
        control.start()
        clock.advance(3)
        result = mining.run_cycle(runtime, live=True, debug=False, control=control, logger=logs.append)

        self.assertEqual(result, [])
        self.assertTrue(control.should_stop())
        self.assertFalse(locate_window.called)
        self.assertTrue(any("达到最大运行时间" in log for log in logs))

    @mock.patch("cishen_clicker.modules.mining.time.sleep")
    @mock.patch("cishen_clicker.modules.mining.click_window_point")
    def test_click_targets_stops_at_pickaxe_click_limit(self, click_window_point, _sleep):
        window = WindowRect(hwnd=1234, left=100, top=200, width=400, height=800)
        target = Candidate(
            cell=Cell(row=6, col=1, rect=Rect(x=50, y=60, width=20, height=30)),
            score=0.9,
            clickable=True,
            reachable=True,
        )
        control = ControlState()
        control.start()
        limit_state = mining.MiningLimitState()
        logs = []

        clicked_targets = mining._click_targets(
            window,
            [target, target, target],
            _config(max_pickaxe_clicks=2),
            live=True,
            control=control,
            label="target",
            logger=logs.append,
            limit_state=limit_state,
        )

        self.assertEqual(len(clicked_targets), 2)
        self.assertEqual(limit_state.pickaxe_clicks, 2)
        self.assertTrue(control.should_stop())
        self.assertEqual(click_window_point.call_count, 2)
        self.assertTrue(any("达到镐头消耗限制" in log for log in logs))


def _config(
    max_runtime_minutes=None,
    max_pickaxe_clicks=None,
):
    return AppConfig(
        window_title="game",
        grid=GridConfig(mine_area=Rect(0, 0, 600, 700), rows=7, cols=6),
        base_window_size=None,
        thresholds=Thresholds(),
        templates_dir=Path("templates"),
        debug_dir=Path("debug"),
        loop_interval_seconds=0.5,
        click_delay_seconds=0.12,
        click_hold_seconds=0.08,
        max_targets_per_round=5,
        use_drill=False,
        use_bomb=False,
        tool_interval_loops=4,
        drill_button_ratio=(0.28, 0.84),
        bomb_button_ratio=(0.74, 0.84),
        max_runtime_minutes=max_runtime_minutes,
        max_pickaxe_clicks=max_pickaxe_clicks,
    )


if __name__ == "__main__":
    unittest.main()

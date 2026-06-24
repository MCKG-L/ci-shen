import unittest
from unittest import mock

import numpy as np

from cishen_clicker.__main__ import run_once
from cishen_clicker.config import AppConfig, Thresholds
from cishen_clicker.control import ControlState
from cishen_clicker.model import GridConfig, Rect
from cishen_clicker.windows import WindowRect


class LoginConflictTests(unittest.TestCase):
    @mock.patch("cishen_clicker.__main__.analyze_grid")
    @mock.patch("cishen_clicker.__main__.detect_login_conflict_dialog", return_value=True)
    @mock.patch("cishen_clicker.__main__.capture_window")
    @mock.patch("cishen_clicker.__main__.locate_window")
    def test_run_once_stops_before_analysis_when_login_conflict_is_detected(
        self,
        locate_window,
        capture_window,
        _detect_login_conflict_dialog,
        analyze_grid,
    ):
        config = AppConfig(
            window_title="game",
            grid=GridConfig(mine_area=Rect(0, 0, 600, 700), rows=7, cols=6),
            base_window_size=None,
            thresholds=Thresholds(),
            templates_dir=None,
            debug_dir=None,
            loop_interval_seconds=0.5,
            click_delay_seconds=0.2,
            max_targets_per_round=5,
        )
        control = ControlState()
        control.start()
        logs = []
        locate_window.return_value = WindowRect(left=0, top=0, width=600, height=1200)
        capture_window.return_value = np.zeros((1200, 600, 3), dtype=np.uint8)

        targets = run_once(
            config,
            templates=[],
            live=True,
            debug=False,
            control=control,
            logger=logs.append,
        )

        self.assertEqual(targets, [])
        self.assertTrue(control.should_stop())
        self.assertFalse(analyze_grid.called)
        self.assertTrue(any("账号在他处登录" in log for log in logs))


if __name__ == "__main__":
    unittest.main()

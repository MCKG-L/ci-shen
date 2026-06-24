import unittest
from unittest import mock

from cishen_clicker.__main__ import _click_targets
from cishen_clicker.config import AppConfig, Thresholds
from cishen_clicker.model import Candidate, Cell, GridConfig, Rect
from cishen_clicker.windows import WindowRect


class ClickTimingTests(unittest.TestCase):
    @mock.patch("cishen_clicker.__main__.time.sleep")
    @mock.patch("cishen_clicker.__main__.click_window_point")
    def test_click_targets_uses_configured_hold_and_delay(self, click_window_point, sleep):
        window = WindowRect(hwnd=1234, left=100, top=200, width=400, height=800)
        target = Candidate(
            cell=Cell(row=6, col=1, rect=Rect(x=50, y=60, width=20, height=30)),
            score=0.9,
            clickable=True,
            reachable=True,
        )
        config = AppConfig(
            window_title="game",
            grid=GridConfig(mine_area=Rect(0, 0, 600, 700), rows=7, cols=6),
            base_window_size=None,
            thresholds=Thresholds(),
            templates_dir=None,
            debug_dir=None,
            loop_interval_seconds=0.5,
            click_delay_seconds=0.12,
            click_hold_seconds=0.08,
            max_targets_per_round=5,
            use_drill=False,
            use_bomb=False,
            tool_interval_loops=4,
            drill_button_ratio=(0.28, 0.84),
            bomb_button_ratio=(0.74, 0.84),
        )

        _click_targets(window, [target], config, live=True, control=None, label="target", logger=lambda _msg: None)

        click_window_point.assert_called_once_with(window, (160, 275), hold_seconds=0.08)
        sleep.assert_called_once_with(0.12)


if __name__ == "__main__":
    unittest.main()

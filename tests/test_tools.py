import unittest
from unittest import mock

from cishen_clicker.__main__ import _click_targets
from cishen_clicker.config import AppConfig, Thresholds
from cishen_clicker.model import Candidate, Cell, GridConfig, Rect
from cishen_clicker.tool_usage import ToolUsageState, tool_drop_point
from cishen_clicker.windows import WindowRect


class ToolUsageTests(unittest.TestCase):
    def test_tool_drop_point_uses_cell_above_bottom_target(self):
        grid = GridConfig(mine_area=Rect(x=0, y=0, width=600, height=700), rows=7, cols=6)
        bottom_cell = Cell(row=6, col=2, rect=Rect(x=200, y=600, width=100, height=100))

        self.assertEqual(tool_drop_point(grid, bottom_cell), (250, 550))

    def test_tool_usage_state_triggers_on_fourth_bottom_loop(self):
        state = ToolUsageState(interval_loops=4)

        self.assertFalse(state.should_use_tools())
        self.assertFalse(state.should_use_tools())
        self.assertFalse(state.should_use_tools())
        self.assertTrue(state.should_use_tools())

    def test_tool_usage_state_alternates_enabled_tools(self):
        state = ToolUsageState(interval_loops=1)
        tools = [("drill", (0.25, 0.80)), ("bomb", (0.75, 0.80))]

        self.assertEqual(state.next_tool(tools), ("drill", (0.25, 0.80)))
        self.assertEqual(state.next_tool(tools), ("bomb", (0.75, 0.80)))
        self.assertEqual(state.next_tool(tools), ("drill", (0.25, 0.80)))

    @mock.patch("cishen_clicker.__main__.time.sleep")
    @mock.patch("cishen_clicker.__main__.click_window_point")
    def test_click_targets_alternates_enabled_tools_before_bottom_clicks(self, click_window_point, _sleep):
        window = WindowRect(hwnd=1234, left=100, top=200, width=600, height=1200)
        grid = GridConfig(mine_area=Rect(x=0, y=0, width=600, height=700), rows=7, cols=6)
        target = Candidate(
            cell=Cell(row=6, col=2, rect=Rect(x=200, y=600, width=100, height=100)),
            score=0.2,
            clickable=False,
            reachable=True,
        )
        config = AppConfig(
            window_title="game",
            grid=grid,
            base_window_size=None,
            thresholds=Thresholds(),
            templates_dir=None,
            debug_dir=None,
            loop_interval_seconds=0.5,
            click_delay_seconds=0.12,
            click_hold_seconds=0.08,
            max_targets_per_round=5,
            use_drill=True,
            use_bomb=True,
            tool_interval_loops=4,
            drill_button_ratio=(0.25, 0.80),
            bomb_button_ratio=(0.75, 0.80),
        )
        tool_state = ToolUsageState(interval_loops=1)

        _click_targets(
            window,
            [target],
            config,
            live=True,
            control=None,
            label="bottom",
            logger=lambda _msg: None,
            tool_state=tool_state,
            grid=grid,
        )
        _click_targets(
            window,
            [target],
            config,
            live=True,
            control=None,
            label="bottom",
            logger=lambda _msg: None,
            tool_state=tool_state,
            grid=grid,
        )

        self.assertEqual(
            click_window_point.call_args_list,
            [
                mock.call(window, (250, 1160), hold_seconds=0.08),
                mock.call(window, (350, 750), hold_seconds=0.08),
                mock.call(window, (350, 850), hold_seconds=0.08),
                mock.call(window, (350, 850), hold_seconds=0.08),
                mock.call(window, (350, 850), hold_seconds=0.08),
                mock.call(window, (350, 850), hold_seconds=0.08),
                mock.call(window, (350, 850), hold_seconds=0.08),
                mock.call(window, (350, 850), hold_seconds=0.08),
                mock.call(window, (550, 1160), hold_seconds=0.08),
                mock.call(window, (350, 750), hold_seconds=0.08),
                mock.call(window, (350, 850), hold_seconds=0.08),
                mock.call(window, (350, 850), hold_seconds=0.08),
                mock.call(window, (350, 850), hold_seconds=0.08),
                mock.call(window, (350, 850), hold_seconds=0.08),
                mock.call(window, (350, 850), hold_seconds=0.08),
                mock.call(window, (350, 850), hold_seconds=0.08),
            ],
        )


if __name__ == "__main__":
    unittest.main()

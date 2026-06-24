from __future__ import annotations

from dataclasses import dataclass

from .model import Cell, GridConfig


@dataclass
class ToolUsageState:
    interval_loops: int = 4
    bottom_loops_seen: int = 0
    next_tool_index: int = 0

    def should_use_tools(self) -> bool:
        self.bottom_loops_seen += 1
        interval = max(1, self.interval_loops)
        if self.bottom_loops_seen < interval:
            return False
        self.bottom_loops_seen = 0
        return True

    def reset(self) -> None:
        self.bottom_loops_seen = 0
        self.next_tool_index = 0

    def next_tool(self, tools):
        if not tools:
            return None
        tool = tools[self.next_tool_index % len(tools)]
        self.next_tool_index += 1
        return tool


def tool_drop_point(grid: GridConfig, bottom_cell: Cell) -> tuple[int, int]:
    cell_height = grid.mine_area.height / grid.rows
    return (
        round(bottom_cell.center[0]),
        round(bottom_cell.center[1] - cell_height),
    )


def tool_button_point(window_size: tuple[int, int], ratio: tuple[float, float]) -> tuple[int, int]:
    width, height = window_size
    return (round(width * ratio[0]), round(height * ratio[1]))

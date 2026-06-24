from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable

from ..config import AppConfig, load_config_from_raw
from ..control import ControlState
from ..gui_config import CONFIG_FIELDS
from ..model import scale_grid_to_window, to_screen_point
from ..strategy import MiningStrategy
from ..tool_usage import ToolUsageState, tool_button_point, tool_drop_point
from ..vision import (
    analyze_grid,
    annotate_candidates,
    annotate_dialog_detection_regions,
    detect_login_conflict_dialog,
    detect_treasure_map_dialog,
    load_templates,
)
from ..windows import capture_window, click_window_point, locate_window
from .base import ModuleSpec


TOOL_POST_CLICK_COUNT = 5


@dataclass
class MiningLimitState:
    clock: Callable[[], float] = time.monotonic
    started_at: float | None = None
    pickaxe_clicks: int = 0
    stop_reason: str | None = None

    def elapsed_seconds(self) -> float:
        now = self.clock()
        if self.started_at is None:
            self.started_at = now
            return 0.0
        return max(0.0, now - self.started_at)

    def record_pickaxe_click(self) -> None:
        self.pickaxe_clicks += 1


@dataclass
class TreasureMapState:
    confirmed_count: int = 0
    confirmed_date: date | None = None

    def refresh_for_today(self, today: date | None = None) -> None:
        today = today or date.today()
        if self.confirmed_date is None:
            self.confirmed_date = today
            return
        if self.confirmed_date != today:
            self.confirmed_date = today
            self.confirmed_count = 0

    def record_confirmed(self, today: date | None = None) -> int:
        self.refresh_for_today(today)
        self.confirmed_count += 1
        return self.confirmed_count


@dataclass
class MiningRuntime:
    config: AppConfig
    templates: list
    strategy: MiningStrategy
    tool_state: ToolUsageState
    limit_state: MiningLimitState
    treasure_state: TreasureMapState


def create_runtime(raw_config: dict[str, Any], config_dir: Path) -> MiningRuntime:
    config = load_config_from_raw(raw_config, config_dir)
    return MiningRuntime(
        config=config,
        templates=load_templates(config.templates_dir),
        strategy=MiningStrategy(),
        tool_state=ToolUsageState(interval_loops=config.tool_interval_loops),
        limit_state=MiningLimitState(),
        treasure_state=TreasureMapState(),
    )


def run_cycle(
    runtime: MiningRuntime,
    live: bool,
    debug: bool,
    control: ControlState | None = None,
    logger=print,
):
    if _stop_if_limits_reached(runtime.config, runtime.limit_state, control, logger):
        return []

    return run_once(
        runtime.config,
        runtime.templates,
        live=live,
        debug=debug,
        control=control,
        strategy=runtime.strategy,
        tool_state=runtime.tool_state,
        limit_state=runtime.limit_state,
        treasure_state=runtime.treasure_state,
        logger=logger,
    )


def run_once(
    config,
    templates: list,
    live: bool,
    debug: bool,
    control: ControlState | None = None,
    strategy: MiningStrategy | None = None,
    tool_state: ToolUsageState | None = None,
    limit_state: MiningLimitState | None = None,
    treasure_state: TreasureMapState | None = None,
    logger=print,
):
    if _stop_if_limits_reached(config, limit_state, control, logger):
        return []

    window = locate_window(config.window_title)
    image = capture_window(window)
    if detect_login_conflict_dialog(image):
        if debug:
            _save_debug_image(config, image, [])
        logger("检测到账户在他处登录提示，已强制结束程序。")
        if control:
            control.stop()
        return []

    treasure_confirm_point = detect_treasure_map_dialog(image)
    if treasure_confirm_point is not None:
        if debug:
            _save_debug_image(config, image, [])
        _handle_treasure_map_dialog(
            window,
            treasure_confirm_point,
            config,
            live,
            control,
            treasure_state,
            logger,
        )
        return []

    grid = _grid_for_image(config, image)
    candidates = analyze_grid(image, grid, config.thresholds, templates)
    bottom_row = grid.rows - 1
    strategy = strategy or MiningStrategy()
    targets = strategy.select_targets(
        candidates,
        config.thresholds.min_score,
        bottom_row=bottom_row,
        max_value_targets=config.max_targets_per_round,
    )

    if debug:
        _save_debug_image(config, image, candidates)

    if not targets:
        logger("no target")
        return []

    label = _target_label(targets, bottom_row)
    logger(f"{label}s={len(targets)}")
    return _click_targets(
        window,
        targets,
        config,
        live,
        control,
        label=label,
        logger=logger,
        tool_state=tool_state,
        grid=grid,
        limit_state=limit_state,
    )


def _click_targets(
    window,
    targets,
    config,
    live: bool,
    control: ControlState | None,
    label: str,
    logger=print,
    tool_state: ToolUsageState | None = None,
    grid=None,
    limit_state: MiningLimitState | None = None,
):
    if _stop_if_limits_reached(config, limit_state, control, logger):
        return []

    if live and label == "bottom" and targets and tool_state and grid and tool_state.should_use_tools():
        if _use_enabled_tools(window, targets[0], config, grid, tool_state, control, logger):
            _click_target_multiple_times(
                window,
                targets[0],
                config,
                control,
                TOOL_POST_CLICK_COUNT,
                limit_state=limit_state,
                logger=logger,
            )
            if _stop_if_limits_reached(config, limit_state, control, logger):
                return []

    clicked_targets = []
    for index, target in enumerate(targets, start=1):
        screen_point = to_screen_point((window.left, window.top), target.cell.center)
        logger(
            f"{label} {index}/{len(targets)} row={target.cell.row} col={target.cell.col} "
            f"score={target.score:.2f} reason={target.reason} screen={screen_point}"
        )

        if live:
            if control and not control.is_running():
                return clicked_targets
            if not _click_mining_target(window, screen_point, config, control, limit_state, logger):
                return clicked_targets
            clicked_targets.append(target)
            if _stop_if_limits_reached(config, limit_state, control, logger):
                return clicked_targets
            time.sleep(config.click_delay_seconds)
    return clicked_targets if live else targets


def _handle_treasure_map_dialog(
    window,
    confirm_point: tuple[int, int],
    config,
    live: bool,
    control: ControlState | None,
    treasure_state: TreasureMapState | None,
    logger=print,
) -> None:
    treasure_state = treasure_state or TreasureMapState()
    next_count = treasure_state.confirmed_count + 1
    logger(f"检测到藏宝图弹窗：准备第 {next_count} 次点击确定")
    if not live:
        return
    if control and not control.is_running():
        return

    screen_point = to_screen_point((window.left, window.top), confirm_point)
    click_window_point(window, screen_point, hold_seconds=config.click_hold_seconds)
    confirmed_count = treasure_state.record_confirmed()
    logger(f"已点击藏宝图确定：第 {confirmed_count} 次")
    time.sleep(config.click_delay_seconds)


def _use_enabled_tools(
    window,
    target,
    config,
    grid,
    tool_state: ToolUsageState,
    control: ControlState | None,
    logger=print,
) -> bool:
    drop_relative = tool_drop_point(grid, target.cell)
    drop_screen = to_screen_point((window.left, window.top), drop_relative)
    window_size = (window.width, window.height)
    tools = []
    if config.use_drill:
        tools.append(("drill", config.drill_button_ratio))
    if config.use_bomb:
        tools.append(("bomb", config.bomb_button_ratio))

    selected = tool_state.next_tool(tools)
    if not selected:
        return False

    name, ratio = selected
    if control and not control.is_running():
        return False
    button_relative = tool_button_point(window_size, ratio)
    button_screen = to_screen_point((window.left, window.top), button_relative)
    logger(f"use {name} drop={drop_screen}")
    click_window_point(window, button_screen, hold_seconds=config.click_hold_seconds)
    time.sleep(config.click_delay_seconds)
    click_window_point(window, drop_screen, hold_seconds=config.click_hold_seconds)
    time.sleep(config.click_delay_seconds)
    return True


def _click_target_multiple_times(
    window,
    target,
    config,
    control: ControlState | None,
    repeat_count: int,
    limit_state: MiningLimitState | None = None,
    logger=print,
) -> int:
    if repeat_count <= 0:
        return 0

    screen_point = to_screen_point((window.left, window.top), target.cell.center)
    clicked = 0
    for _index in range(repeat_count):
        if control and not control.is_running():
            return clicked
        if not _click_mining_target(window, screen_point, config, control, limit_state, logger):
            return clicked
        clicked += 1
        if _stop_if_limits_reached(config, limit_state, control, logger):
            return clicked
        time.sleep(config.click_delay_seconds)
    return clicked


def _click_mining_target(
    window,
    screen_point: tuple[int, int],
    config,
    control: ControlState | None,
    limit_state: MiningLimitState | None,
    logger=print,
) -> bool:
    if control and not control.is_running():
        return False
    if _stop_if_limits_reached(config, limit_state, control, logger):
        return False

    click_window_point(window, screen_point, hold_seconds=config.click_hold_seconds)
    if limit_state is not None:
        limit_state.record_pickaxe_click()
        _stop_if_limits_reached(config, limit_state, control, logger)
    return True


def _stop_if_limits_reached(
    config,
    limit_state: MiningLimitState | None,
    control: ControlState | None,
    logger=print,
) -> bool:
    if limit_state is None:
        return False
    if limit_state.stop_reason is not None:
        if control:
            control.stop()
        return True

    max_runtime_minutes = getattr(config, "max_runtime_minutes", None)
    if max_runtime_minutes is not None:
        elapsed = _active_elapsed_seconds(control, limit_state)
        max_runtime_seconds = max_runtime_minutes * 60.0
        if elapsed >= max_runtime_seconds:
            return _stop_for_limit(
                limit_state,
                control,
                logger,
                f"达到最大运行时间：{elapsed / 60.0:.1f}/{max_runtime_minutes:.1f} 分钟",
            )

    max_pickaxe_clicks = getattr(config, "max_pickaxe_clicks", None)
    if max_pickaxe_clicks is not None and limit_state.pickaxe_clicks >= max_pickaxe_clicks:
        return _stop_for_limit(
            limit_state,
            control,
            logger,
            f"达到镐头消耗限制：{limit_state.pickaxe_clicks}/{max_pickaxe_clicks}",
        )
    return False


def _active_elapsed_seconds(control: ControlState | None, limit_state: MiningLimitState) -> float:
    if control is not None:
        return control.active_elapsed_seconds()
    return limit_state.elapsed_seconds()


def _stop_for_limit(
    limit_state: MiningLimitState,
    control: ControlState | None,
    logger,
    message: str,
) -> bool:
    limit_state.stop_reason = message
    logger(message)
    if control:
        control.stop()
    return True


def _target_label(targets, bottom_row: int) -> str:
    if targets and all(target.cell.row == bottom_row for target in targets):
        return "bottom"
    return "target"


def _grid_for_image(config, image):
    if config.base_window_size is None:
        return config.grid
    height, width = image.shape[:2]
    return scale_grid_to_window(config.grid, config.base_window_size, (width, height))


def _save_debug_image(config, image, candidates) -> None:
    cv2, _np = _cv()
    annotated = annotate_dialog_detection_regions(image)
    annotated = annotate_candidates(annotated, candidates, config.thresholds.min_score)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    cv2.imwrite(str(config.debug_dir / f"{stamp}-annotated.png"), annotated)


def _cv():
    try:
        import cv2
        import numpy as np
    except ModuleNotFoundError as exc:
        raise RuntimeError("Missing OpenCV. Install with: python -m pip install -r requirements.txt") from exc
    return cv2, np


SPEC = ModuleSpec(
    key="mining",
    label="挖矿",
    fields=CONFIG_FIELDS,
    create_runtime=create_runtime,
    run_cycle=run_cycle,
)

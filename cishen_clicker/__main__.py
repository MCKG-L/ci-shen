from __future__ import annotations

import argparse
import time
from datetime import datetime
from pathlib import Path

from .config import load_config
from .control import ControlState
from .model import scale_grid_to_window, to_screen_point
from .modules import get_module_spec
from .strategy import MiningStrategy
from .tool_usage import ToolUsageState, tool_button_point, tool_drop_point
from .vision import analyze_grid, annotate_candidates, detect_login_conflict_dialog, load_templates
from .windows import capture_window, click_window_point, locate_window
from .workspace_config import load_workspace_config


TOOL_POST_CLICK_COUNT = 5


def _runtime_loop_interval(runtime) -> float:
    config = getattr(runtime, "config", None)
    if config is not None:
        return float(getattr(config, "loop_interval_seconds", 0.5))
    if isinstance(runtime, dict):
        raw_config = runtime.get("raw_config", {})
        return float(raw_config.get("loop_interval_seconds", 0.5))
    return 0.5


def _runtime_debug_dir(runtime) -> Path:
    config = getattr(runtime, "config", None)
    if config is not None:
        return Path(getattr(config, "debug_dir", "debug"))
    if isinstance(runtime, dict):
        raw_config = runtime.get("raw_config", {})
        return Path(str(raw_config.get("debug_dir", "debug")))
    return Path("debug")


def main() -> int:
    parser = argparse.ArgumentParser(description="Authorized Windows click helper for CISHEN mining.")
    parser.add_argument("--config", default="config.json", help="Path to config.json.")
    parser.add_argument("--live", action="store_true", help="Actually click. Default is dry-run.")
    parser.add_argument("--once", action="store_true", help="Run one screenshot/decision cycle and exit.")
    parser.add_argument("--debug", action="store_true", help="Save annotated screenshots.")
    args = parser.parse_args()

    config_path = Path(args.config)
    workspace_config = load_workspace_config(config_path)
    module_spec = get_module_spec(workspace_config.active_module)
    module_config = workspace_config.modules[workspace_config.active_module]
    runtime = module_spec.create_runtime(module_config, config_path.parent)
    if args.debug:
        _runtime_debug_dir(runtime).mkdir(parents=True, exist_ok=True)

    print(f"module={module_spec.label} live={args.live}")
    control = _setup_control(args.live, args.once)

    while True:
        if control and not control.wait_until_running():
            return 0
        targets = module_spec.run_cycle(
            runtime,
            live=args.live,
            debug=args.debug,
            control=control,
        )
        if args.once:
            return 0 if targets else 2
        if control and control.should_stop():
            return 0
        time.sleep(_runtime_loop_interval(runtime))


def run_once(
    config,
    templates: list,
    live: bool,
    debug: bool,
    control: ControlState | None = None,
    strategy: MiningStrategy | None = None,
    tool_state: ToolUsageState | None = None,
    logger=print,
):
    window = locate_window(config.window_title)
    image = capture_window(window)
    if detect_login_conflict_dialog(image):
        logger("检测到账号在他处登录提示，已强制结束程序。")
        if control:
            control.stop()
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
):
    if live and label == "bottom" and targets and tool_state and grid and tool_state.should_use_tools():
        if _use_enabled_tools(window, targets[0], config, grid, tool_state, control, logger):
            _click_target_multiple_times(
                window,
                targets[0],
                config,
                control,
                TOOL_POST_CLICK_COUNT,
            )

    for index, target in enumerate(targets, start=1):
        screen_point = to_screen_point((window.left, window.top), target.cell.center)
        logger(
            f"{label} {index}/{len(targets)} row={target.cell.row} col={target.cell.col} "
            f"score={target.score:.2f} reason={target.reason} screen={screen_point}"
        )

        if live:
            if control and not control.is_running():
                return targets[: index - 1]
            click_window_point(window, screen_point, hold_seconds=config.click_hold_seconds)
            time.sleep(config.click_delay_seconds)
    return targets


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


def _click_target_multiple_times(window, target, config, control: ControlState | None, repeat_count: int) -> None:
    if repeat_count <= 0:
        return

    screen_point = to_screen_point((window.left, window.top), target.cell.center)
    for _index in range(repeat_count):
        if control and not control.is_running():
            return
        click_window_point(window, screen_point, hold_seconds=config.click_hold_seconds)
        time.sleep(config.click_delay_seconds)


def _setup_control(live: bool, once: bool) -> ControlState | None:
    if once or not live:
        return None
    state = ControlState()
    state.start()
    return state


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
    annotated = annotate_candidates(image, candidates, config.thresholds.min_score)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    cv2.imwrite(str(config.debug_dir / f"{stamp}-annotated.png"), annotated)


def _cv():
    try:
        import cv2
        import numpy as np
    except ModuleNotFoundError as exc:
        raise RuntimeError("Missing OpenCV. Install with: python -m pip install -r requirements.txt") from exc
    return cv2, np


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import time
from datetime import datetime
from pathlib import Path

from .config import load_config
from .control import ControlState, Hotkeys, install_hotkeys
from .model import scale_grid_to_window, to_screen_point
from .strategy import MiningStrategy
from .vision import analyze_grid, annotate_candidates, load_templates
from .windows import capture_window, click_screen_point, locate_window


def main() -> int:
    parser = argparse.ArgumentParser(description="Authorized Windows click helper for CISHEN mining.")
    parser.add_argument("--config", default="config.json", help="Path to config.json.")
    parser.add_argument("--live", action="store_true", help="Actually click. Default is dry-run.")
    parser.add_argument("--once", action="store_true", help="Run one screenshot/decision cycle and exit.")
    parser.add_argument("--debug", action="store_true", help="Save annotated screenshots.")
    parser.add_argument("--no-hotkeys", action="store_true", help="Disable F8/F9/F10 live controls.")
    args = parser.parse_args()

    config = load_config(Path(args.config))
    templates = load_templates(config.templates_dir)
    if args.debug:
        config.debug_dir.mkdir(parents=True, exist_ok=True)

    print(f"window_title={config.window_title!r} live={args.live} templates={len(templates)}")
    control = _setup_control(args.live, args.once, args.no_hotkeys)
    strategy = MiningStrategy()

    while True:
        if control and not control.wait_until_running():
            return 0
        targets = run_once(
            config,
            templates,
            live=args.live,
            debug=args.debug,
            control=control,
            strategy=strategy,
        )
        if args.once:
            return 0 if targets else 2
        if control and control.should_stop():
            return 0
        time.sleep(config.loop_interval_seconds)


def run_once(
    config,
    templates: list,
    live: bool,
    debug: bool,
    control: ControlState | None = None,
    strategy: MiningStrategy | None = None,
    logger=print,
):
    window = locate_window(config.window_title)
    image = capture_window(window)
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
    return _click_targets(window, targets, config, live, control, label=label, logger=logger)


def _click_targets(window, targets, config, live: bool, control: ControlState | None, label: str, logger=print):
    for index, target in enumerate(targets, start=1):
        screen_point = to_screen_point((window.left, window.top), target.cell.center)
        logger(
            f"{label} {index}/{len(targets)} row={target.cell.row} col={target.cell.col} "
            f"score={target.score:.2f} reason={target.reason} screen={screen_point}"
        )

        if live:
            if control and not control.is_running():
                return targets[: index - 1]
            click_screen_point(screen_point)
            time.sleep(config.click_delay_seconds)
    return targets


def _setup_control(live: bool, once: bool, no_hotkeys: bool) -> ControlState | None:
    if once or not live:
        return None
    state = ControlState()
    if no_hotkeys:
        state.start()
        return state

    install_hotkeys(state, Hotkeys())
    print("hotkeys: F8=start/resume F9=pause F10=stop")
    print("waiting: press F8 to start")
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

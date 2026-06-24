from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .model import GridConfig, Rect


@dataclass(frozen=True)
class Thresholds:
    min_score: float = 0.7
    min_brightness: float = 62.0
    min_saturation: float = 28.0
    min_content_score: float = 0.18
    template_threshold: float = 0.72
    min_reachable_brightness: float = 70.0
    min_reachable_bright_pixel_ratio: float = 0.60
    min_mineral_color_ratio: float = 0.035


@dataclass(frozen=True)
class AppConfig:
    window_title: str
    grid: GridConfig
    base_window_size: tuple[float, float] | None
    thresholds: Thresholds
    templates_dir: Path
    debug_dir: Path
    loop_interval_seconds: float
    click_delay_seconds: float
    click_hold_seconds: float
    max_targets_per_round: int | None
    use_drill: bool
    use_bomb: bool
    tool_interval_loops: int
    drill_button_ratio: tuple[float, float]
    bomb_button_ratio: tuple[float, float]
    max_runtime_minutes: float | None = None
    max_pickaxe_clicks: int | None = None


def load_config(path: Path) -> AppConfig:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return load_config_from_raw(raw, path.parent)


def load_config_from_raw(raw: dict[str, Any], config_dir: Path) -> AppConfig:
    mine_area = raw["mine_area"]
    base_window = raw.get("base_window")
    thresholds = raw.get("thresholds", {})

    return AppConfig(
        window_title=str(raw.get("window_title", "次神")),
        grid=GridConfig(
            mine_area=Rect(
                x=float(mine_area["x"]),
                y=float(mine_area["y"]),
                width=float(mine_area["width"]),
                height=float(mine_area["height"]),
            ),
            rows=int(raw.get("rows", 7)),
            cols=int(raw.get("cols", 6)),
            active_start_row=int(raw.get("active_start_row", 0)),
            excluded_cells=_load_excluded_cells(raw.get("excluded_cells", [])),
        ),
        base_window_size=_load_base_window_size(base_window),
        thresholds=Thresholds(
            min_score=float(thresholds.get("min_score", 0.7)),
            min_brightness=float(thresholds.get("min_brightness", 62.0)),
            min_saturation=float(thresholds.get("min_saturation", 28.0)),
            min_content_score=float(thresholds.get("min_content_score", 0.18)),
            template_threshold=float(thresholds.get("template_threshold", 0.72)),
            min_reachable_brightness=float(thresholds.get("min_reachable_brightness", 70.0)),
            min_reachable_bright_pixel_ratio=float(
                thresholds.get("min_reachable_bright_pixel_ratio", 0.60)
            ),
            min_mineral_color_ratio=float(thresholds.get("min_mineral_color_ratio", 0.035)),
        ),
        templates_dir=_resolve(config_dir, raw.get("templates_dir", "templates")),
        debug_dir=_resolve(config_dir, raw.get("debug_dir", "debug")),
        loop_interval_seconds=float(raw.get("loop_interval_seconds", 0.5)),
        click_delay_seconds=float(raw.get("click_delay_seconds", 0.12)),
        click_hold_seconds=float(raw.get("click_hold_seconds", 0.08)),
        max_targets_per_round=_load_optional_int(raw.get("max_targets_per_round")),
        use_drill=bool(raw.get("use_drill", False)),
        use_bomb=bool(raw.get("use_bomb", False)),
        tool_interval_loops=max(1, int(raw.get("tool_interval_loops", 4))),
        drill_button_ratio=_load_point_ratio(raw.get("drill_button_ratio"), default=(0.28, 0.84)),
        bomb_button_ratio=_load_point_ratio(raw.get("bomb_button_ratio"), default=(0.74, 0.84)),
        max_runtime_minutes=_load_runtime_minutes(raw),
        max_pickaxe_clicks=_load_optional_int(raw.get("max_pickaxe_clicks")),
    )


def _load_base_window_size(raw: Any) -> tuple[float, float] | None:
    if raw is None:
        return None
    return (float(raw["width"]), float(raw["height"]))


def _load_excluded_cells(raw: Any) -> frozenset[tuple[int, int]]:
    cells = []
    for item in raw or []:
        cells.append((int(item["row"]), int(item["col"])))
    return frozenset(cells)


def _load_optional_int(raw: Any) -> int | None:
    if raw is None:
        return None
    value = int(raw)
    if value < 0:
        return None
    return value


def _load_optional_float(raw: Any) -> float | None:
    if raw is None:
        return None
    value = float(raw)
    if value < 0:
        return None
    return value


def _load_runtime_minutes(raw: dict[str, Any]) -> float | None:
    if "max_runtime_minutes" in raw:
        return _load_optional_float(raw.get("max_runtime_minutes"))

    legacy_seconds = _load_optional_float(raw.get("max_runtime_seconds"))
    if legacy_seconds is None:
        return None
    return legacy_seconds / 60.0


def _load_point_ratio(raw: Any, default: tuple[float, float]) -> tuple[float, float]:
    if raw is None:
        return default
    return (float(raw["x"]), float(raw["y"]))


def _resolve(config_dir: Path, value: Any) -> Path:
    path = Path(str(value))
    if path.is_absolute():
        return path
    return config_dir / path

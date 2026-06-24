from __future__ import annotations

from pathlib import Path
from typing import Any

from ..gui_config import ConfigField
from .base import ModuleSpec


GARDEN_FIELDS: tuple[ConfigField, ...] = (
    ConfigField("window_title", "窗口标题", str),
    ConfigField("loop_interval_seconds", "循环间隔（秒）", float),
)


def create_runtime(raw_config: dict[str, Any], config_dir: Path) -> dict[str, Any]:
    return {"raw_config": raw_config, "config_dir": config_dir}


def run_cycle(*args, **kwargs) -> list[Any]:
    raise NotImplementedError("菜园管理模块尚未实现")


SPEC = ModuleSpec(
    key="garden",
    label="菜园管理",
    fields=GARDEN_FIELDS,
    create_runtime=create_runtime,
    run_cycle=run_cycle,
)

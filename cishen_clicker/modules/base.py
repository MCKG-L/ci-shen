from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from ..gui_config import ConfigField


@dataclass(frozen=True)
class ModuleSpec:
    key: str
    label: str
    fields: tuple[ConfigField, ...]
    create_runtime: Callable[[dict[str, Any], Path], Any]
    run_cycle: Callable[..., list[Any]]

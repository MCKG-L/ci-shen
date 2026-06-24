from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class WorkspaceConfig:
    active_module: str
    modules: dict[str, dict[str, Any]]


def load_workspace_config(path: Path) -> WorkspaceConfig:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if "modules" not in raw:
        return WorkspaceConfig(active_module="mining", modules={"mining": copy.deepcopy(raw)})

    modules = {
        str(key): copy.deepcopy(value)
        for key, value in raw.get("modules", {}).items()
        if isinstance(value, dict)
    }
    return WorkspaceConfig(
        active_module=str(raw.get("active_module", "mining")),
        modules=modules,
    )


def workspace_to_raw(config: WorkspaceConfig) -> dict[str, Any]:
    return {
        "active_module": config.active_module,
        "modules": copy.deepcopy(config.modules),
    }


def save_workspace_config(path: Path, config: WorkspaceConfig) -> None:
    raw = workspace_to_raw(config)
    path.write_text(json.dumps(raw, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

from __future__ import annotations

from . import dungeon, garden, mining, summon
from .base import ModuleSpec


MODULE_SPECS: tuple[ModuleSpec, ...] = (
    mining.SPEC,
    dungeon.SPEC,
    summon.SPEC,
    garden.SPEC,
)


def list_module_keys() -> list[str]:
    return [spec.key for spec in MODULE_SPECS]


def get_module_spec(key: str) -> ModuleSpec:
    for spec in MODULE_SPECS:
        if spec.key == key:
            return spec
    raise KeyError(key)

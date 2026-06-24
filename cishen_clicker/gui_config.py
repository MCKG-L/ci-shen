from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


Parser = Callable[[str], Any]


def _parse_optional_int(text: str) -> int | None:
    if text == "":
        return None
    return int(text)


def _parse_bool(text: str) -> bool:
    value = text.strip().lower()
    if value in {"1", "true", "yes", "y", "on"}:
        return True
    if value in {"0", "false", "no", "n", "off", ""}:
        return False
    raise ValueError(text)


@dataclass(frozen=True)
class ConfigField:
    key: str
    label: str
    parser: Parser
    kind: str = "entry"


CONFIG_FIELDS: tuple[ConfigField, ...] = (
    ConfigField("click_delay_seconds", "点击间隔（秒）", float),
    ConfigField("click_hold_seconds", "按下保持（秒）", float),
    ConfigField("loop_interval_seconds", "循环间隔（秒）", float),
    ConfigField("max_targets_per_round", "每轮最多目标数", _parse_optional_int),
    ConfigField("tool_interval_loops", "道具间隔循环数", int),
    ConfigField("use_drill", "使用钻头", _parse_bool, kind="check"),
    ConfigField("use_bomb", "使用炸药", _parse_bool, kind="check"),
)


def load_raw_config(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def save_raw_config(path: Path, raw: dict[str, Any]) -> None:
    path.write_text(json.dumps(raw, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def extract_gui_values(raw: dict[str, Any]) -> dict[str, str]:
    values = {}
    for field in CONFIG_FIELDS:
        value = _get_nested(raw, field.key)
        if field.kind == "check":
            values[field.key] = "true" if bool(value) else "false"
        else:
            values[field.key] = "" if value is None else str(value)
    return values


def apply_gui_values(raw: dict[str, Any], values: dict[str, str]) -> dict[str, Any]:
    updated = copy.deepcopy(raw)
    fields_by_key = {field.key: field for field in CONFIG_FIELDS}
    for key, text in values.items():
        field = fields_by_key[key]
        try:
            parsed = field.parser(text.strip())
        except ValueError as exc:
            raise ValueError(f"{field.label}: invalid value {text!r}") from exc
        _set_nested(updated, key, parsed)
    return updated


def _get_nested(raw: dict[str, Any], dotted_key: str) -> Any:
    current: Any = raw
    for part in dotted_key.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


def _set_nested(raw: dict[str, Any], dotted_key: str, value: Any) -> None:
    parts = dotted_key.split(".")
    current = raw
    for part in parts[:-1]:
        child = current.get(part)
        if not isinstance(child, dict):
            child = {}
            current[part] = child
        current = child
    current[parts[-1]] = value

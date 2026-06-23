from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Rect:
    x: float
    y: float
    width: float
    height: float

    @property
    def center(self) -> tuple[float, float]:
        return (self.x + self.width / 2, self.y + self.height / 2)


@dataclass(frozen=True)
class GridConfig:
    mine_area: Rect
    rows: int
    cols: int
    active_start_row: int = 0
    excluded_cells: frozenset[tuple[int, int]] = frozenset()


@dataclass(frozen=True)
class Cell:
    row: int
    col: int
    rect: Rect

    @property
    def center(self) -> tuple[float, float]:
        return self.rect.center


@dataclass(frozen=True)
class Candidate:
    cell: Cell
    score: float
    clickable: bool
    reason: str = ""
    reachable: bool = True


def iter_grid_cells(config: GridConfig) -> Iterable[Cell]:
    cell_width = config.mine_area.width / config.cols
    cell_height = config.mine_area.height / config.rows

    active_start_row = min(max(0, config.active_start_row), config.rows)
    for row in range(active_start_row, config.rows):
        for col in range(config.cols):
            if (row, col) in config.excluded_cells:
                continue
            yield Cell(
                row=row,
                col=col,
                rect=Rect(
                    x=config.mine_area.x + col * cell_width,
                    y=config.mine_area.y + row * cell_height,
                    width=cell_width,
                    height=cell_height,
                ),
            )


def scale_grid_to_window(
    config: GridConfig,
    base_size: tuple[float, float],
    current_size: tuple[float, float],
) -> GridConfig:
    base_width, base_height = base_size
    current_width, current_height = current_size
    if base_width <= 0 or base_height <= 0:
        raise ValueError(f"base_size must be positive, got {base_size}")

    scale_x = current_width / base_width
    scale_y = current_height / base_height
    area = config.mine_area
    return GridConfig(
        mine_area=Rect(
            x=area.x * scale_x,
            y=area.y * scale_y,
            width=area.width * scale_x,
            height=area.height * scale_y,
        ),
        rows=config.rows,
        cols=config.cols,
        active_start_row=config.active_start_row,
        excluded_cells=config.excluded_cells,
    )


def to_screen_point(window_origin: tuple[float, float], relative_point: tuple[float, float]) -> tuple[int, int]:
    return (round(window_origin[0] + relative_point[0]), round(window_origin[1] + relative_point[1]))


def choose_click_target(candidates: Iterable[Candidate], min_score: float) -> Candidate | None:
    targets = choose_click_targets(candidates, min_score)
    return targets[0] if targets else None


def choose_click_targets(
    candidates: Iterable[Candidate],
    min_score: float,
    max_targets: int | None = None,
    required_row: int | None = None,
) -> list[Candidate]:
    candidates = list(candidates)
    targets = [
        candidate
        for candidate in candidates
        if candidate.reachable and candidate.clickable and candidate.score >= min_score
    ]
    sorted_targets = sorted(targets, key=lambda candidate: (-candidate.cell.row, candidate.cell.col))
    return _apply_target_rules(sorted_targets, candidates, max_targets, required_row)


def choose_fallback_target(candidates: Iterable[Candidate]) -> Candidate | None:
    targets = choose_fallback_targets(candidates, max_targets=1)
    return targets[0] if targets else None


def choose_fallback_targets(
    candidates: Iterable[Candidate],
    max_targets: int | None = None,
    required_row: int | None = None,
) -> list[Candidate]:
    candidates = list(candidates)
    reachable = [candidate for candidate in candidates if candidate.reachable]
    sorted_targets = sorted(reachable, key=lambda candidate: (-candidate.cell.row, candidate.cell.col))
    return _apply_target_rules(sorted_targets, candidates, max_targets, required_row)


def _apply_target_rules(
    sorted_targets: list[Candidate],
    candidates: list[Candidate],
    max_targets: int | None,
    required_row: int | None,
) -> list[Candidate]:
    if max_targets is None:
        limited_targets = sorted_targets
    else:
        limit = max(0, max_targets)
        limited_targets = sorted_targets[:limit]
        if limit == 0:
            return limited_targets

    if required_row is None or any(target.cell.row == required_row for target in limited_targets):
        return limited_targets

    required_target = _first_reachable_in_row(candidates, required_row, exclude=limited_targets)
    if required_target is None:
        return limited_targets

    adjusted_targets = list(limited_targets)
    if max_targets is not None and len(adjusted_targets) >= max(0, max_targets):
        adjusted_targets[-1] = required_target
    else:
        adjusted_targets.append(required_target)
    return sorted(adjusted_targets, key=lambda candidate: (-candidate.cell.row, candidate.cell.col))


def _first_reachable_in_row(
    candidates: Iterable[Candidate],
    required_row: int,
    exclude: Iterable[Candidate],
) -> Candidate | None:
    excluded_cells = {(candidate.cell.row, candidate.cell.col) for candidate in exclude}
    row_candidates = [
        candidate
        for candidate in candidates
        if candidate.reachable
        and candidate.cell.row == required_row
        and (candidate.cell.row, candidate.cell.col) not in excluded_cells
    ]
    return min(row_candidates, key=lambda candidate: candidate.cell.col, default=None)

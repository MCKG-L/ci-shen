from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .model import Candidate


@dataclass
class MiningStrategy:
    bottom_click_count: int = 5
    value_check_rounds_after_bottom: int = 2
    locked_bottom_cell: tuple[int, int] | None = None
    value_checks_remaining: int = 0

    def select_targets(
        self,
        candidates: Iterable[Candidate],
        min_score: float,
        bottom_row: int,
        max_value_targets: int | None = None,
    ) -> list[Candidate]:
        candidates = list(candidates)
        if self.value_checks_remaining > 0:
            value_targets = self._value_targets_above_bottom(candidates, min_score, bottom_row)
            if value_targets:
                self.locked_bottom_cell = None
                self.value_checks_remaining -= 1
                return _limit(value_targets, max_value_targets)
            self.value_checks_remaining = 0

        bottom_targets = self._bottom_targets(candidates, bottom_row)
        if bottom_targets:
            return bottom_targets

        value_targets = self._value_targets_above_bottom(candidates, min_score, bottom_row)
        if value_targets:
            self.locked_bottom_cell = None
            return _limit(value_targets, max_value_targets)
        return []

    def _value_targets_above_bottom(
        self,
        candidates: list[Candidate],
        min_score: float,
        bottom_row: int,
    ) -> list[Candidate]:
        targets = [
            candidate
            for candidate in candidates
            if candidate.reachable
            and candidate.clickable
            and candidate.score >= min_score
            and candidate.cell.row != bottom_row
        ]
        return sorted(targets, key=lambda candidate: (-candidate.cell.row, candidate.cell.col))

    def _bottom_target(self, candidates: list[Candidate], bottom_row: int) -> Candidate | None:
        locked_target = self._locked_bottom_target(candidates)
        if locked_target is not None:
            return locked_target

        bottom_targets = [
            candidate
            for candidate in candidates
            if candidate.reachable and candidate.cell.row == bottom_row
        ]
        return min(bottom_targets, key=lambda candidate: candidate.cell.col, default=None)

    def _bottom_targets(self, candidates: list[Candidate], bottom_row: int) -> list[Candidate]:
        bottom_target = self._bottom_target(candidates, bottom_row)
        if bottom_target is None:
            self.locked_bottom_cell = None
            self.value_checks_remaining = 0
            return []

        self.locked_bottom_cell = (bottom_target.cell.row, bottom_target.cell.col)
        self.value_checks_remaining = max(0, self.value_check_rounds_after_bottom)
        return [bottom_target for _ in range(max(0, self.bottom_click_count))]

    def _locked_bottom_target(self, candidates: list[Candidate]) -> Candidate | None:
        if self.locked_bottom_cell is None:
            return None
        for candidate in candidates:
            if candidate.reachable and (candidate.cell.row, candidate.cell.col) == self.locked_bottom_cell:
                return candidate
        return None


def _limit(targets: list[Candidate], max_targets: int | None) -> list[Candidate]:
    if max_targets is None:
        return targets
    return targets[: max(0, max_targets)]

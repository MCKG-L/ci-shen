import unittest

from cishen_clicker.model import Candidate, GridConfig, Rect, iter_grid_cells
from cishen_clicker.strategy import MiningStrategy


class MiningStrategyTests(unittest.TestCase):
    def test_starts_with_reachable_bottom_cell_even_when_upper_value_exists(self):
        cells = _cells()
        strategy = MiningStrategy(bottom_click_count=5)
        candidates = [
            Candidate(cell=cells[36], score=0.20, clickable=False, reachable=True),
            Candidate(cell=cells[31], score=0.90, clickable=True, reachable=True),
            Candidate(cell=cells[25], score=0.91, clickable=True, reachable=True),
        ]

        targets = strategy.select_targets(
            candidates,
            min_score=0.7,
            bottom_row=6,
            max_value_targets=5,
        )

        self.assertEqual(
            [(target.cell.row, target.cell.col) for target in targets],
            [(6, 0), (6, 0), (6, 0), (6, 0), (6, 0)],
        )

    def test_confirms_reachable_valuable_targets_after_two_frames(self):
        cells = _cells()
        strategy = MiningStrategy(bottom_click_count=5)
        candidates = [
            Candidate(cell=cells[36], score=0.95, clickable=True, reachable=True),
            Candidate(cell=cells[31], score=0.90, clickable=True, reachable=True),
            Candidate(cell=cells[25], score=0.91, clickable=True, reachable=True),
            Candidate(cell=cells[18], score=0.92, clickable=True, reachable=True),
            Candidate(cell=cells[30], score=0.40, clickable=False, reachable=True),
        ]

        strategy.select_targets(candidates, min_score=0.7, bottom_row=6, max_value_targets=5)
        pending_targets = strategy.select_targets(
            candidates,
            min_score=0.7,
            bottom_row=6,
            max_value_targets=5,
        )
        confirmed_targets = strategy.select_targets(
            candidates,
            min_score=0.7,
            bottom_row=6,
            max_value_targets=5,
        )

        self.assertEqual(pending_targets, [])
        self.assertEqual(
            [(target.cell.row, target.cell.col) for target in confirmed_targets],
            [(5, 1), (4, 1), (3, 0)],
        )

    def test_returns_to_bottom_when_second_value_frame_does_not_match(self):
        cells = _cells()
        strategy = MiningStrategy(bottom_click_count=5, value_check_rounds_after_bottom=2)
        bottom_and_first_value = [
            Candidate(cell=cells[36], score=0.20, clickable=False, reachable=True),
            Candidate(cell=cells[31], score=0.90, clickable=True, reachable=True),
        ]
        bottom_and_shifted_value = [
            Candidate(cell=cells[36], score=0.20, clickable=False, reachable=True),
            Candidate(cell=cells[25], score=0.90, clickable=True, reachable=True),
        ]

        first_targets = strategy.select_targets(
            bottom_and_first_value,
            min_score=0.7,
            bottom_row=6,
            max_value_targets=5,
        )
        second_targets = strategy.select_targets(
            bottom_and_first_value,
            min_score=0.7,
            bottom_row=6,
            max_value_targets=5,
        )
        third_targets = strategy.select_targets(
            bottom_and_shifted_value,
            min_score=0.7,
            bottom_row=6,
            max_value_targets=5,
        )

        self.assertEqual(
            [(target.cell.row, target.cell.col) for target in first_targets],
            [(6, 0), (6, 0), (6, 0), (6, 0), (6, 0)],
        )
        self.assertEqual(second_targets, [])
        self.assertEqual(
            [(target.cell.row, target.cell.col) for target in third_targets],
            [(6, 0), (6, 0), (6, 0), (6, 0), (6, 0)],
        )

    def test_repeats_first_reachable_bottom_cell_when_no_upper_value_exists(self):
        cells = _cells()
        strategy = MiningStrategy(bottom_click_count=5)
        candidates = [
            Candidate(cell=cells[36], score=0.20, clickable=False, reachable=False),
            Candidate(cell=cells[37], score=0.20, clickable=False, reachable=True),
            Candidate(cell=cells[38], score=0.20, clickable=False, reachable=True),
            Candidate(cell=cells[25], score=0.40, clickable=False, reachable=True),
        ]

        targets = strategy.select_targets(
            candidates,
            min_score=0.7,
            bottom_row=6,
            max_value_targets=5,
        )

        self.assertEqual(len(targets), 5)
        self.assertEqual(
            [(target.cell.row, target.cell.col) for target in targets],
            [(6, 1), (6, 1), (6, 1), (6, 1), (6, 1)],
        )

    def test_keeps_locked_bottom_cell_while_it_remains_reachable(self):
        cells = _cells()
        strategy = MiningStrategy(bottom_click_count=5)
        first_candidates = [
            Candidate(cell=cells[36], score=0.20, clickable=False, reachable=False),
            Candidate(cell=cells[37], score=0.20, clickable=False, reachable=True),
        ]
        second_candidates = [
            Candidate(cell=cells[36], score=0.20, clickable=False, reachable=True),
            Candidate(cell=cells[37], score=0.20, clickable=False, reachable=True),
        ]

        strategy.select_targets(first_candidates, min_score=0.7, bottom_row=6, max_value_targets=5)
        targets = strategy.select_targets(
            second_candidates,
            min_score=0.7,
            bottom_row=6,
            max_value_targets=5,
        )

        self.assertEqual(
            [(target.cell.row, target.cell.col) for target in targets],
            [(6, 1), (6, 1), (6, 1), (6, 1), (6, 1)],
        )

    def test_resets_bottom_lock_after_upper_value_targets_are_selected(self):
        cells = _cells()
        strategy = MiningStrategy(bottom_click_count=5)
        strategy.select_targets(
            [Candidate(cell=cells[38], score=0.20, clickable=False, reachable=True)],
            min_score=0.7,
            bottom_row=6,
            max_value_targets=5,
        )
        strategy.select_targets(
            [
                Candidate(cell=cells[25], score=0.90, clickable=True, reachable=True),
                Candidate(cell=cells[38], score=0.20, clickable=False, reachable=True),
            ],
            min_score=0.7,
            bottom_row=6,
            max_value_targets=5,
        )
        strategy.select_targets(
            [
                Candidate(cell=cells[25], score=0.90, clickable=True, reachable=True),
                Candidate(cell=cells[38], score=0.20, clickable=False, reachable=True),
            ],
            min_score=0.7,
            bottom_row=6,
            max_value_targets=5,
        )

        targets = strategy.select_targets(
            [
                Candidate(cell=cells[36], score=0.20, clickable=False, reachable=True),
                Candidate(cell=cells[38], score=0.20, clickable=False, reachable=True),
            ],
            min_score=0.7,
            bottom_row=6,
            max_value_targets=5,
        )

        self.assertEqual(
            [(target.cell.row, target.cell.col) for target in targets],
            [(6, 0), (6, 0), (6, 0), (6, 0), (6, 0)],
        )


def _cells():
    config = GridConfig(mine_area=Rect(x=0, y=0, width=600, height=700), rows=7, cols=6)
    return list(iter_grid_cells(config))


if __name__ == "__main__":
    unittest.main()

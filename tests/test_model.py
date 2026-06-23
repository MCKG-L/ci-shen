import unittest

from cishen_clicker.model import (
    Candidate,
    GridConfig,
    Rect,
    choose_click_target,
    choose_click_targets,
    choose_fallback_targets,
    choose_fallback_target,
    iter_grid_cells,
    scale_grid_to_window,
    to_screen_point,
)


class GridModelTests(unittest.TestCase):
    def test_iter_grid_cells_uses_mine_area_relative_coordinates(self):
        config = GridConfig(mine_area=Rect(x=50, y=100, width=300, height=200), rows=2, cols=3)

        cells = list(iter_grid_cells(config))

        self.assertEqual(len(cells), 6)
        self.assertEqual((cells[0].row, cells[0].col), (0, 0))
        self.assertEqual((cells[0].rect.x, cells[0].rect.y), (50, 100))
        self.assertEqual((cells[0].rect.width, cells[0].rect.height), (100, 100))
        self.assertEqual(cells[5].center, (300, 250))

    def test_iter_grid_cells_can_skip_rows_before_active_start_row(self):
        config = GridConfig(
            mine_area=Rect(x=60, y=140, width=300, height=700),
            rows=7,
            cols=3,
            active_start_row=3,
        )

        cells = list(iter_grid_cells(config))

        self.assertEqual(len(cells), 12)
        self.assertEqual((cells[0].row, cells[0].col), (3, 0))
        self.assertEqual((cells[0].rect.x, cells[0].rect.y), (60, 440))
        self.assertEqual((cells[-1].row, cells[-1].col), (6, 2))

    def test_iter_grid_cells_skips_excluded_cells(self):
        config = GridConfig(
            mine_area=Rect(x=0, y=0, width=600, height=700),
            rows=7,
            cols=6,
            active_start_row=3,
            excluded_cells=frozenset({(5, 0)}),
        )

        cells = list(iter_grid_cells(config))

        self.assertNotIn((5, 0), [(cell.row, cell.col) for cell in cells])
        self.assertEqual(len(cells), 23)

    def test_to_screen_point_offsets_relative_coordinates_by_window_origin(self):
        self.assertEqual(to_screen_point((120, 40), (300.4, 250.6)), (420, 291))

    def test_scale_grid_to_window_uses_base_window_as_coordinate_basis(self):
        config = GridConfig(mine_area=Rect(x=87, y=372, width=501, height=589), rows=7, cols=6)

        scaled = scale_grid_to_window(config, base_size=(671, 1248), current_size=(1342, 2496))

        self.assertEqual(scaled.rows, 7)
        self.assertEqual(scaled.cols, 6)
        self.assertEqual(scaled.mine_area, Rect(x=174, y=744, width=1002, height=1178))

    def test_scale_grid_to_window_preserves_excluded_cells(self):
        config = GridConfig(
            mine_area=Rect(x=87, y=372, width=501, height=589),
            rows=7,
            cols=6,
            excluded_cells=frozenset({(5, 0)}),
        )

        scaled = scale_grid_to_window(config, base_size=(671, 1248), current_size=(1342, 2496))

        self.assertEqual(scaled.excluded_cells, frozenset({(5, 0)}))

    def test_choose_click_target_uses_first_clickable_candidate_in_bottom_up_order(self):
        config = GridConfig(mine_area=Rect(x=0, y=0, width=300, height=200), rows=2, cols=3)
        cells = list(iter_grid_cells(config))
        candidates = [
            Candidate(cell=cells[0], score=0.95, clickable=False),
            Candidate(cell=cells[1], score=0.51, clickable=True),
            Candidate(cell=cells[2], score=0.90, clickable=True),
            Candidate(cell=cells[3], score=0.80, clickable=True),
        ]

        target = choose_click_target(candidates, min_score=0.7)

        self.assertIsNotNone(target)
        self.assertEqual((target.cell.row, target.cell.col), (1, 0))

    def test_choose_click_targets_returns_all_clickable_candidates_by_bottom_row_then_col(self):
        config = GridConfig(mine_area=Rect(x=0, y=0, width=300, height=200), rows=2, cols=3)
        cells = list(iter_grid_cells(config))
        candidates = [
            Candidate(cell=cells[5], score=0.91, clickable=True),
            Candidate(cell=cells[2], score=0.90, clickable=True),
            Candidate(cell=cells[0], score=0.95, clickable=False),
            Candidate(cell=cells[1], score=0.60, clickable=True),
            Candidate(cell=cells[3], score=0.72, clickable=True),
        ]

        targets = choose_click_targets(candidates, min_score=0.7)

        self.assertEqual([(target.cell.row, target.cell.col) for target in targets], [(1, 0), (1, 2), (0, 2)])

    def test_choose_click_targets_can_limit_round_size(self):
        config = GridConfig(mine_area=Rect(x=0, y=0, width=300, height=300), rows=3, cols=3)
        cells = list(iter_grid_cells(config))
        candidates = [
            Candidate(cell=cell, score=0.90, clickable=True, reason="mineral-shape")
            for cell in cells
        ]

        targets = choose_click_targets(candidates, min_score=0.7, max_targets=5)

        self.assertEqual(
            [(target.cell.row, target.cell.col) for target in targets],
            [(2, 0), (2, 1), (2, 2), (1, 0), (1, 1)],
        )

    def test_choose_click_targets_can_require_reachable_row_when_batch_is_full(self):
        config = GridConfig(mine_area=Rect(x=0, y=0, width=600, height=700), rows=7, cols=6)
        cells = list(iter_grid_cells(config))
        candidates = [
            Candidate(cell=cells[18], score=0.90, clickable=True, reason="mineral-shape"),
            Candidate(cell=cells[19], score=0.90, clickable=True, reason="mineral-shape"),
            Candidate(cell=cells[20], score=0.90, clickable=True, reason="mineral-shape"),
            Candidate(cell=cells[21], score=0.90, clickable=True, reason="mineral-shape"),
            Candidate(cell=cells[22], score=0.90, clickable=True, reason="mineral-shape"),
            Candidate(cell=cells[36], score=0.20, clickable=False, reason="low-mineral-color", reachable=True),
        ]

        targets = choose_click_targets(candidates, min_score=0.7, max_targets=5, required_row=6)

        self.assertEqual(
            [(target.cell.row, target.cell.col) for target in targets],
            [(6, 0), (3, 0), (3, 1), (3, 2), (3, 3)],
        )

    def test_choose_click_targets_leaves_batch_unchanged_when_required_row_unreachable(self):
        config = GridConfig(mine_area=Rect(x=0, y=0, width=600, height=700), rows=7, cols=6)
        cells = list(iter_grid_cells(config))
        candidates = [
            Candidate(cell=cells[18], score=0.90, clickable=True, reason="mineral-shape"),
            Candidate(cell=cells[19], score=0.90, clickable=True, reason="mineral-shape"),
            Candidate(cell=cells[36], score=0.20, clickable=False, reason="unreachable", reachable=False),
        ]

        targets = choose_click_targets(candidates, min_score=0.7, max_targets=5, required_row=6)

        self.assertEqual(
            [(target.cell.row, target.cell.col) for target in targets],
            [(3, 0), (3, 1)],
        )

    def test_choose_click_targets_does_not_duplicate_existing_required_row_target(self):
        config = GridConfig(mine_area=Rect(x=0, y=0, width=600, height=700), rows=7, cols=6)
        cells = list(iter_grid_cells(config))
        candidates = [
            Candidate(cell=cells[36], score=0.90, clickable=True, reason="mineral-shape"),
            Candidate(cell=cells[18], score=0.90, clickable=True, reason="mineral-shape"),
        ]

        targets = choose_click_targets(candidates, min_score=0.7, max_targets=5, required_row=6)

        self.assertEqual(
            [(target.cell.row, target.cell.col) for target in targets],
            [(6, 0), (3, 0)],
        )

    def test_choose_fallback_target_uses_bottom_left_reachable_cell(self):
        config = GridConfig(mine_area=Rect(x=0, y=0, width=300, height=200), rows=2, cols=3)
        cells = list(iter_grid_cells(config))
        candidates = [
            Candidate(cell=cells[0], score=0.99, clickable=False),
            Candidate(cell=cells[3], score=0.40, clickable=False),
            Candidate(cell=cells[4], score=0.62, clickable=False),
            Candidate(cell=cells[5], score=0.61, clickable=False),
        ]

        target = choose_fallback_target(candidates)

        self.assertIsNotNone(target)
        self.assertEqual((target.cell.row, target.cell.col), (1, 0))

    def test_choose_fallback_target_skips_unreachable_cells(self):
        config = GridConfig(mine_area=Rect(x=0, y=0, width=300, height=200), rows=2, cols=3)
        cells = list(iter_grid_cells(config))
        candidates = [
            Candidate(cell=cells[3], score=0.99, clickable=False, reason="unreachable", reachable=False),
            Candidate(cell=cells[4], score=0.41, clickable=False, reason="low-mineral-color", reachable=True),
            Candidate(cell=cells[5], score=0.40, clickable=False, reason="unreachable", reachable=False),
        ]

        target = choose_fallback_target(candidates)

        self.assertIsNotNone(target)
        self.assertEqual((target.cell.row, target.cell.col), (1, 1))

    def test_choose_fallback_target_continues_up_when_last_row_is_unreachable(self):
        config = GridConfig(mine_area=Rect(x=0, y=0, width=300, height=200), rows=2, cols=3)
        cells = list(iter_grid_cells(config))
        candidates = [
            Candidate(cell=cells[0], score=0.99, clickable=False, reason="low-mineral-color", reachable=True),
            Candidate(cell=cells[3], score=0.40, clickable=False, reason="unreachable", reachable=False),
            Candidate(cell=cells[4], score=0.62, clickable=False, reason="unreachable", reachable=False),
            Candidate(cell=cells[5], score=0.61, clickable=False, reason="unreachable", reachable=False),
        ]

        target = choose_fallback_target(candidates)

        self.assertIsNotNone(target)
        self.assertEqual((target.cell.row, target.cell.col), (0, 0))

    def test_choose_fallback_target_returns_none_when_no_cells_are_reachable(self):
        config = GridConfig(mine_area=Rect(x=0, y=0, width=300, height=200), rows=2, cols=3)
        cells = list(iter_grid_cells(config))
        candidates = [
            Candidate(cell=cell, score=0.0, clickable=False, reason="unreachable", reachable=False)
            for cell in cells
        ]

        self.assertIsNone(choose_fallback_target(candidates))

    def test_choose_fallback_targets_uses_reachable_cells_from_bottom_to_top(self):
        config = GridConfig(mine_area=Rect(x=0, y=0, width=300, height=300), rows=3, cols=3)
        cells = list(iter_grid_cells(config))
        candidates = [
            Candidate(cell=cells[0], score=0.99, clickable=False, reachable=True),
            Candidate(cell=cells[1], score=0.99, clickable=False, reachable=True),
            Candidate(cell=cells[2], score=0.99, clickable=False, reachable=True),
            Candidate(cell=cells[3], score=0.99, clickable=False, reachable=True),
            Candidate(cell=cells[4], score=0.99, clickable=False, reachable=False),
            Candidate(cell=cells[5], score=0.99, clickable=False, reachable=True),
            Candidate(cell=cells[6], score=0.10, clickable=False, reachable=True),
            Candidate(cell=cells[7], score=0.20, clickable=False, reachable=True),
            Candidate(cell=cells[8], score=0.30, clickable=False, reachable=True),
        ]

        targets = choose_fallback_targets(candidates, max_targets=5)

        self.assertEqual(
            [(target.cell.row, target.cell.col) for target in targets],
            [(2, 0), (2, 1), (2, 2), (1, 0), (1, 2)],
        )


if __name__ == "__main__":
    unittest.main()

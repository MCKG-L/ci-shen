import unittest

import numpy as np

from cishen_clicker.config import Thresholds
from cishen_clicker.model import GridConfig, Rect
from cishen_clicker.vision import analyze_grid, detect_login_conflict_dialog, score_cell


class VisionScoringTests(unittest.TestCase):
    def test_detect_login_conflict_dialog_with_confirm_button(self):
        image = np.full((1200, 600, 3), (48, 58, 56), dtype=np.uint8)
        image[390:760, 70:530] = (245, 245, 245)
        image[620:705, 320:500] = (80, 195, 30)

        self.assertTrue(detect_login_conflict_dialog(image))

    def test_detect_login_conflict_dialog_rejects_plain_game_screen(self):
        image = np.full((1200, 600, 3), (48, 58, 56), dtype=np.uint8)
        image[620:705, 320:500] = (80, 195, 30)

        self.assertFalse(detect_login_conflict_dialog(image))

    def test_dark_unreachable_cell_is_rejected_before_mineral_scoring(self):
        image = np.full((80, 80, 3), (42, 55, 34), dtype=np.uint8)

        score, reason = score_cell(image, Thresholds(), templates=[])

        self.assertEqual(score, 0.0)
        self.assertEqual(reason, "unreachable")

    def test_partly_bright_ui_overlay_does_not_make_dark_cell_reachable(self):
        image = np.full((80, 80, 3), (50, 58, 48), dtype=np.uint8)
        image[48:68, 8:52] = (20, 190, 230)

        score, reason = score_cell(image, Thresholds(min_score=0.65), templates=[])

        self.assertEqual(score, 0.0)
        self.assertEqual(reason, "unreachable")

    def test_reachable_red_mineral_scores_as_clickable(self):
        image = np.full((80, 80, 3), (72, 82, 86), dtype=np.uint8)
        image[24:56, 24:56] = (30, 40, 220)

        score, reason = score_cell(image, Thresholds(min_score=0.65), templates=[])

        self.assertGreaterEqual(score, 0.65)
        self.assertEqual(reason, "valuable-color:red")

    def test_reachable_blue_mineral_scores_as_clickable(self):
        image = np.full((80, 80, 3), (72, 82, 86), dtype=np.uint8)
        image[24:56, 24:56] = (220, 120, 30)

        score, reason = score_cell(image, Thresholds(min_score=0.65), templates=[])

        self.assertGreaterEqual(score, 0.65)
        self.assertEqual(reason, "mineral-color:blue")

    def test_reachable_textured_brown_mineral_scores_as_clickable(self):
        image = np.full((80, 80, 3), (72, 82, 86), dtype=np.uint8)
        image[26:54, 26:54] = (40, 70, 120)
        image[30:34, 30:50] = (18, 28, 45)
        image[46:50, 30:50] = (18, 28, 45)
        image[30:50, 30:34] = (18, 28, 45)
        image[30:50, 46:50] = (18, 28, 45)

        score, reason = score_cell(image, Thresholds(min_score=0.65), templates=[])

        self.assertGreaterEqual(score, 0.65)
        self.assertEqual(reason, "mineral-shape")

    def test_reachable_plain_dirt_stays_below_click_threshold(self):
        image = np.full((80, 80, 3), (62, 105, 145), dtype=np.uint8)

        score, reason = score_cell(image, Thresholds(min_score=0.65), templates=[])

        self.assertLess(score, 0.65)
        self.assertEqual(reason, "low-mineral-color")

    def test_empty_crop_is_not_reachable(self):
        image = np.zeros((20, 20, 3), dtype=np.uint8)
        grid = GridConfig(mine_area=Rect(30, 30, 10, 10), rows=1, cols=1)

        candidates = analyze_grid(image, grid, Thresholds(), templates=[])

        self.assertFalse(candidates[0].reachable)
        self.assertFalse(candidates[0].clickable)
        self.assertEqual(candidates[0].reason, "empty-crop")

    def test_analyze_grid_ignores_rows_before_active_start_row(self):
        image = np.full((700, 300, 3), (90, 90, 90), dtype=np.uint8)
        grid = GridConfig(
            mine_area=Rect(0, 0, 300, 700),
            rows=7,
            cols=6,
            active_start_row=3,
        )

        candidates = analyze_grid(image, grid, Thresholds(), templates=[])

        self.assertEqual(len(candidates), 24)
        self.assertEqual(min(candidate.cell.row for candidate in candidates), 3)
        self.assertEqual(max(candidate.cell.row for candidate in candidates), 6)


if __name__ == "__main__":
    unittest.main()

import tempfile
import unittest
from pathlib import Path

import numpy as np

from cishen_clicker.__main__ import _save_debug_image
from cishen_clicker.config import AppConfig, Thresholds
from cishen_clicker.model import Candidate, Cell, GridConfig, Rect


class DebugOutputTests(unittest.TestCase):
    def test_save_debug_image_writes_only_annotated_image(self):
        with tempfile.TemporaryDirectory() as tmp:
            debug_dir = Path(tmp)
            config = AppConfig(
                window_title="test",
                grid=GridConfig(mine_area=Rect(0, 0, 10, 10), rows=1, cols=1),
                base_window_size=None,
                thresholds=Thresholds(),
                templates_dir=debug_dir,
                debug_dir=debug_dir,
                loop_interval_seconds=0.5,
                click_delay_seconds=0.2,
                click_hold_seconds=0.08,
                max_targets_per_round=None,
                use_drill=False,
                use_bomb=False,
                tool_interval_loops=4,
                drill_button_ratio=(0.28, 0.84),
                bomb_button_ratio=(0.74, 0.84),
            )
            image = np.zeros((10, 10, 3), dtype=np.uint8)
            candidates = [
                Candidate(
                    cell=Cell(row=0, col=0, rect=Rect(0, 0, 10, 10)),
                    score=0.0,
                    clickable=False,
                    reason="unreachable",
                    reachable=False,
                )
            ]

            _save_debug_image(config, image, candidates)

            raw_images = list(debug_dir.glob("*-raw.png"))
            annotated_images = list(debug_dir.glob("*-annotated.png"))
            self.assertEqual(len(raw_images), 0)
            self.assertEqual(len(annotated_images), 1)


if __name__ == "__main__":
    unittest.main()

import unittest

from cishen_clicker.gui_config import CONFIG_FIELDS, apply_gui_values, extract_gui_values


class GuiConfigTests(unittest.TestCase):
    def test_config_fields_expose_click_timing_parameters(self):
        self.assertEqual(
            [field.key for field in CONFIG_FIELDS],
            [
                "click_delay_seconds",
                "click_hold_seconds",
                "loop_interval_seconds",
                "max_targets_per_round",
                "tool_interval_loops",
                "use_drill",
                "use_bomb",
            ],
        )

    def test_extract_gui_values_reads_key_parameters(self):
        raw = {
            "click_delay_seconds": 0.03,
            "click_hold_seconds": 0.08,
            "loop_interval_seconds": 0.3,
            "max_targets_per_round": 8,
            "tool_interval_loops": 3,
            "use_drill": True,
            "use_bomb": False,
            "thresholds": {
                "min_score": 0.65,
                "min_reachable_brightness": 75,
            },
        }

        values = extract_gui_values(raw)

        self.assertEqual(
            values,
            {
                "click_delay_seconds": "0.03",
                "click_hold_seconds": "0.08",
                "loop_interval_seconds": "0.3",
                "max_targets_per_round": "8",
                "tool_interval_loops": "3",
                "use_drill": "true",
                "use_bomb": "false",
            },
        )

    def test_apply_gui_values_updates_key_parameters(self):
        raw = {
            "click_delay_seconds": 0.2,
            "click_hold_seconds": 0.08,
            "loop_interval_seconds": 0.5,
            "max_targets_per_round": 5,
            "tool_interval_loops": 4,
            "use_drill": False,
            "use_bomb": False,
            "thresholds": {"min_score": 0.7},
        }

        updated = apply_gui_values(
            raw,
            {
                "click_delay_seconds": "0.01",
                "click_hold_seconds": "0.09",
                "loop_interval_seconds": "0.25",
                "max_targets_per_round": "",
                "tool_interval_loops": "2",
                "use_drill": "true",
                "use_bomb": "false",
            },
        )

        self.assertEqual(updated["click_delay_seconds"], 0.01)
        self.assertEqual(updated["click_hold_seconds"], 0.09)
        self.assertEqual(updated["loop_interval_seconds"], 0.25)
        self.assertIsNone(updated["max_targets_per_round"])
        self.assertEqual(updated["tool_interval_loops"], 2)
        self.assertTrue(updated["use_drill"])
        self.assertFalse(updated["use_bomb"])
        self.assertEqual(updated["thresholds"]["min_score"], 0.7)
        self.assertEqual(raw["click_delay_seconds"], 0.2)


if __name__ == "__main__":
    unittest.main()

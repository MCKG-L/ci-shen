import unittest

from cishen_clicker.gui_config import CONFIG_FIELDS, apply_gui_values, extract_gui_values


class GuiConfigTests(unittest.TestCase):
    def test_config_fields_only_expose_three_parameters(self):
        self.assertEqual(
            [field.key for field in CONFIG_FIELDS],
            ["click_delay_seconds", "loop_interval_seconds", "max_targets_per_round"],
        )

    def test_extract_gui_values_reads_only_three_parameters(self):
        raw = {
            "click_delay_seconds": 0.03,
            "loop_interval_seconds": 0.3,
            "max_targets_per_round": 8,
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
                "loop_interval_seconds": "0.3",
                "max_targets_per_round": "8",
            },
        )

    def test_apply_gui_values_updates_only_three_parameters(self):
        raw = {
            "click_delay_seconds": 0.2,
            "loop_interval_seconds": 0.5,
            "max_targets_per_round": 5,
            "thresholds": {"min_score": 0.7},
        }

        updated = apply_gui_values(
            raw,
            {
                "click_delay_seconds": "0.01",
                "loop_interval_seconds": "0.25",
                "max_targets_per_round": "",
            },
        )

        self.assertEqual(updated["click_delay_seconds"], 0.01)
        self.assertEqual(updated["loop_interval_seconds"], 0.25)
        self.assertIsNone(updated["max_targets_per_round"])
        self.assertEqual(updated["thresholds"]["min_score"], 0.7)
        self.assertEqual(raw["click_delay_seconds"], 0.2)


if __name__ == "__main__":
    unittest.main()

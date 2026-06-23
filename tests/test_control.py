import unittest

from cishen_clicker.control import ControlState


class ControlStateTests(unittest.TestCase):
    def test_control_state_starts_paused(self):
        state = ControlState()

        self.assertFalse(state.is_running())
        self.assertFalse(state.should_stop())

    def test_control_state_can_start_pause_and_stop(self):
        state = ControlState()

        state.start()
        self.assertTrue(state.is_running())

        state.pause()
        self.assertFalse(state.is_running())

        state.stop()
        self.assertTrue(state.should_stop())
        self.assertFalse(state.is_running())


if __name__ == "__main__":
    unittest.main()

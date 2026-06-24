import unittest

from cishen_clicker.control import ControlState


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


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

    def test_active_elapsed_seconds_ignores_paused_time(self):
        clock = FakeClock()
        state = ControlState(clock=clock)

        state.start()
        clock.advance(3.0)
        self.assertEqual(state.active_elapsed_seconds(), 3.0)

        state.pause()
        clock.advance(100.0)
        self.assertEqual(state.active_elapsed_seconds(), 3.0)

        state.start()
        clock.advance(2.0)
        self.assertEqual(state.active_elapsed_seconds(), 5.0)


if __name__ == "__main__":
    unittest.main()

import unittest

from cishen_clicker.gui import install_gui_hotkeys


class FakeRoot:
    def __init__(self) -> None:
        self.calls = []

    def after(self, delay, callback):
        self.calls.append((delay, callback))


class FakeKeyboard:
    def __init__(self) -> None:
        self.bindings = []

    def add_hotkey(self, key, callback):
        self.bindings.append((key, callback))


class GuiHotkeyTests(unittest.TestCase):
    def test_install_gui_hotkeys_schedules_callbacks_on_main_thread(self):
        root = FakeRoot()
        keyboard = FakeKeyboard()
        events = []

        install_gui_hotkeys(
            root,
            lambda: events.append("start"),
            lambda: events.append("pause"),
            lambda: events.append("stop"),
            keyboard_module=keyboard,
        )

        self.assertEqual([key for key, _callback in keyboard.bindings], ["f6", "f9", "f10"])

        keyboard.bindings[1][1]()
        self.assertEqual(root.calls[0][0], 0)
        root.calls[0][1]()
        self.assertEqual(events, ["pause"])


if __name__ == "__main__":
    unittest.main()

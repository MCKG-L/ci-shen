import unittest
from unittest import mock

from cishen_clicker.windows import (
    WM_LBUTTONDOWN,
    WM_LBUTTONUP,
    WindowRect,
    click_window_point,
    client_area_to_window_rect,
    make_lparam,
)


class WindowGeometryTests(unittest.TestCase):
    def test_client_area_to_window_rect_uses_client_origin_and_size(self):
        rect = client_area_to_window_rect(hwnd=1234, client_origin=(120, 80), client_size=(462, 839))

        self.assertEqual(rect, WindowRect(hwnd=1234, left=120, top=80, width=462, height=839))

    def test_client_area_to_window_rect_rejects_empty_client_area(self):
        with self.assertRaisesRegex(RuntimeError, "empty client area"):
            client_area_to_window_rect(hwnd=1234, client_origin=(120, 80), client_size=(0, 839))

    def test_make_lparam_packs_client_coordinates(self):
        self.assertEqual(make_lparam(258, 772), (772 << 16) | 258)

    @mock.patch("cishen_clicker.windows.time.sleep")
    def test_click_window_point_posts_mouse_messages_without_moving_cursor(self, sleep):
        class FakeUser32:
            def __init__(self):
                self.messages = []

            def PostMessageW(self, hwnd, message, wparam, lparam):
                self.messages.append((hwnd, message, wparam, lparam))
                return 1

        user32 = FakeUser32()
        rect = WindowRect(hwnd=1234, left=100, top=200, width=400, height=800)

        click_window_point(rect, (250, 500), hold_seconds=0.08, user32=user32)

        lparam = make_lparam(150, 300)
        self.assertEqual(
            [(hwnd.value, message, wparam, lparam) for hwnd, message, wparam, lparam in user32.messages],
            [
                (1234, WM_LBUTTONDOWN, 1, lparam),
                (1234, WM_LBUTTONUP, 0, lparam),
            ],
        )
        sleep.assert_called_once_with(0.08)


if __name__ == "__main__":
    unittest.main()

import unittest

from cishen_clicker.windows import WindowRect, client_area_to_window_rect


class WindowGeometryTests(unittest.TestCase):
    def test_client_area_to_window_rect_uses_client_origin_and_size(self):
        rect = client_area_to_window_rect(client_origin=(120, 80), client_size=(462, 839))

        self.assertEqual(rect, WindowRect(left=120, top=80, width=462, height=839))

    def test_client_area_to_window_rect_rejects_empty_client_area(self):
        with self.assertRaisesRegex(RuntimeError, "empty client area"):
            client_area_to_window_rect(client_origin=(120, 80), client_size=(0, 839))


if __name__ == "__main__":
    unittest.main()

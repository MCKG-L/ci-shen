from __future__ import annotations

import ctypes
import sys
import time
from ctypes import wintypes
from dataclasses import dataclass


WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
MK_LBUTTON = 0x0001


@dataclass(frozen=True)
class WindowRect:
    hwnd: int
    left: int
    top: int
    width: int
    height: int


def client_area_to_window_rect(
    hwnd: int,
    client_origin: tuple[int, int],
    client_size: tuple[int, int],
) -> WindowRect:
    width, height = client_size
    if width <= 0 or height <= 0:
        raise RuntimeError(f"Matched window has an empty client area: {client_size}")
    return WindowRect(hwnd=hwnd, left=client_origin[0], top=client_origin[1], width=width, height=height)


def locate_window(title_keyword: str) -> WindowRect:
    if not sys.platform.startswith("win"):
        raise RuntimeError("Window location is only supported on Windows.")

    _set_process_dpi_awareness()
    user32 = ctypes.windll.user32

    matches = _find_visible_windows(title_keyword, user32)
    if not matches:
        titles = _visible_window_titles(user32)
        raise RuntimeError(f"No visible window matched {title_keyword!r}. Visible titles include: {titles[:12]}")

    hwnd = matches[0]
    try:
        user32.SetForegroundWindow(hwnd)
    except Exception:
        pass

    return _client_rect_for_hwnd(hwnd, user32)


def capture_window(rect: WindowRect):
    try:
        import mss
        import numpy as np
    except ModuleNotFoundError as exc:
        raise RuntimeError("Missing screenshot dependencies. Install with: python -m pip install -r requirements.txt") from exc

    with mss.mss() as sct:
        raw = sct.grab({"left": rect.left, "top": rect.top, "width": rect.width, "height": rect.height})
        bgra = np.array(raw)
        return bgra[:, :, :3]


def click_window_point(
    window: WindowRect,
    screen_point: tuple[int, int],
    hold_seconds: float = 0.08,
    user32=None,
) -> None:
    if not sys.platform.startswith("win") and user32 is None:
        raise RuntimeError("Window message click is only supported on Windows.")

    user32 = user32 or ctypes.windll.user32
    client_x = round(screen_point[0] - window.left)
    client_y = round(screen_point[1] - window.top)
    lparam = make_lparam(client_x, client_y)

    if not user32.PostMessageW(wintypes.HWND(window.hwnd), WM_LBUTTONDOWN, MK_LBUTTON, lparam):
        raise RuntimeError("Failed to send mouse down message to window.")
    time.sleep(max(0.0, hold_seconds))
    if not user32.PostMessageW(wintypes.HWND(window.hwnd), WM_LBUTTONUP, 0, lparam):
        raise RuntimeError("Failed to send mouse up message to window.")


def make_lparam(x: int, y: int) -> int:
    return (y & 0xFFFF) << 16 | (x & 0xFFFF)


def _set_process_dpi_awareness() -> None:
    try:
        ctypes.windll.user32.SetProcessDpiAwarenessContext(wintypes.HANDLE(-4))
        return
    except Exception:
        pass

    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
        return
    except Exception:
        pass

    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


def _find_visible_windows(title_keyword: str, user32) -> list[int]:
    keyword = title_keyword.lower()
    matches: list[int] = []

    def callback(hwnd, _lparam):
        if user32.IsWindowVisible(hwnd):
            title = _window_title(hwnd, user32)
            if keyword in title.lower():
                matches.append(int(hwnd))
        return True

    enum_proc = _enum_windows_proc(callback)
    user32.EnumWindows(enum_proc, 0)
    return matches


def _visible_window_titles(user32) -> list[str]:
    titles: list[str] = []

    def callback(hwnd, _lparam):
        if user32.IsWindowVisible(hwnd):
            title = _window_title(hwnd, user32).strip()
            if title:
                titles.append(title)
        return True

    enum_proc = _enum_windows_proc(callback)
    user32.EnumWindows(enum_proc, 0)
    return titles


def _window_title(hwnd, user32) -> str:
    length = user32.GetWindowTextLengthW(hwnd)
    if length <= 0:
        return ""
    buffer = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buffer, length + 1)
    return buffer.value


def _client_rect_for_hwnd(hwnd: int, user32) -> WindowRect:
    rect = wintypes.RECT()
    if not user32.GetClientRect(wintypes.HWND(hwnd), ctypes.byref(rect)):
        raise RuntimeError("Failed to read window client rect.")

    point = wintypes.POINT(0, 0)
    if not user32.ClientToScreen(wintypes.HWND(hwnd), ctypes.byref(point)):
        raise RuntimeError("Failed to convert client origin to screen coordinates.")

    return client_area_to_window_rect(
        hwnd=hwnd,
        client_origin=(int(point.x), int(point.y)),
        client_size=(int(rect.right - rect.left), int(rect.bottom - rect.top)),
    )


def _enum_windows_proc(callback):
    return ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)(callback)

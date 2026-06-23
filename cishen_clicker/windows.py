from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes
from dataclasses import dataclass


@dataclass(frozen=True)
class WindowRect:
    left: int
    top: int
    width: int
    height: int


def client_area_to_window_rect(client_origin: tuple[int, int], client_size: tuple[int, int]) -> WindowRect:
    width, height = client_size
    if width <= 0 or height <= 0:
        raise RuntimeError(f"Matched window has an empty client area: {client_size}")
    return WindowRect(left=client_origin[0], top=client_origin[1], width=width, height=height)


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


def click_screen_point(point: tuple[int, int]) -> None:
    try:
        import pyautogui
    except ModuleNotFoundError as exc:
        raise RuntimeError("Missing pyautogui. Install dependencies with: python -m pip install -r requirements.txt") from exc

    pyautogui.click(point[0], point[1])


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
        client_origin=(int(point.x), int(point.y)),
        client_size=(int(rect.right - rect.left), int(rect.bottom - rect.top)),
    )


def _enum_windows_proc(callback):
    return ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)(callback)

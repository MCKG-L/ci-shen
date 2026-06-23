from __future__ import annotations

import threading
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class Hotkeys:
    start: str = "f6"
    pause: str = "f9"
    stop: str = "f10"


class ControlState:
    def __init__(self) -> None:
        self._running = threading.Event()
        self._stopped = threading.Event()

    def start(self) -> None:
        if not self.should_stop():
            self._running.set()

    def pause(self) -> None:
        self._running.clear()

    def stop(self) -> None:
        self._running.clear()
        self._stopped.set()

    def is_running(self) -> bool:
        return self._running.is_set() and not self.should_stop()

    def should_stop(self) -> bool:
        return self._stopped.is_set()

    def wait_until_running(self, poll_seconds: float = 0.05) -> bool:
        while not self.should_stop():
            if self.is_running():
                return True
            time.sleep(poll_seconds)
        return False


def install_hotkeys(state: ControlState, hotkeys: Hotkeys = Hotkeys()) -> None:
    try:
        import keyboard
    except ModuleNotFoundError as exc:
        raise RuntimeError("Missing keyboard dependency. Install with: python -m pip install -r requirements.txt") from exc

    keyboard.add_hotkey(hotkeys.start, _announce_start, args=(state, hotkeys.start))
    keyboard.add_hotkey(hotkeys.pause, _announce_pause, args=(state, hotkeys.pause))
    keyboard.add_hotkey(hotkeys.stop, _announce_stop, args=(state, hotkeys.stop))


def _announce_start(state: ControlState, key: str) -> None:
    state.start()
    print(f"[hotkey {key}] started")


def _announce_pause(state: ControlState, key: str) -> None:
    state.pause()
    print(f"[hotkey {key}] paused")


def _announce_stop(state: ControlState, key: str) -> None:
    state.stop()
    print(f"[hotkey {key}] stopping")

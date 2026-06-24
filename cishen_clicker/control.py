from __future__ import annotations

import threading
import time
from typing import Callable


class ControlState:
    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        self._clock = clock
        self._lock = threading.Lock()
        self._running = threading.Event()
        self._stopped = threading.Event()
        self._active_seconds = 0.0
        self._active_started_at: float | None = None

    def start(self) -> None:
        if not self.should_stop():
            with self._lock:
                if self._active_started_at is None:
                    self._active_started_at = self._clock()
            self._running.set()

    def pause(self) -> None:
        self._capture_active_seconds()
        self._running.clear()

    def stop(self) -> None:
        self._capture_active_seconds()
        self._running.clear()
        self._stopped.set()

    def is_running(self) -> bool:
        return self._running.is_set() and not self.should_stop()

    def should_stop(self) -> bool:
        return self._stopped.is_set()

    def active_elapsed_seconds(self) -> float:
        with self._lock:
            elapsed = self._active_seconds
            if self._active_started_at is not None and self.is_running():
                elapsed += self._clock() - self._active_started_at
            return max(0.0, elapsed)

    def wait_until_running(self, poll_seconds: float = 0.05) -> bool:
        while not self.should_stop():
            if self.is_running():
                return True
            time.sleep(poll_seconds)
        return False

    def _capture_active_seconds(self) -> None:
        with self._lock:
            if self._active_started_at is not None:
                self._active_seconds += self._clock() - self._active_started_at
                self._active_started_at = None

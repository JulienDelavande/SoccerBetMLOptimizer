"""In-process stale-while-revalidate cache for the public site.

A fresh value is returned as is. An expired value is still returned at once while one background
refresh recomputes it, so no visitor waits for a slow rebuild (the Elo history takes seconds).
Only a key that was never computed blocks, and concurrent cold callers share that computation.
"""
import logging
import threading
import time
from typing import Any, Callable

logger = logging.getLogger(__name__)


def _thread(job: Callable[[], None]) -> None:
    threading.Thread(target=job, daemon=True).start()


class SWRCache:
    def __init__(self, clock: Callable[[], float] = time.monotonic,
                 background: Callable[[Callable[[], None]], None] = _thread):
        self._clock = clock
        self._background = background
        self._lock = threading.Lock()
        self._values: dict[str, tuple[float, Any]] = {}
        self._key_locks: dict[str, threading.Lock] = {}
        self._refreshing: set[str] = set()

    def get(self, key: str, ttl: float, compute: Callable[[], Any]) -> Any:
        with self._lock:
            hit = self._values.get(key)
            if hit and self._clock() - hit[0] < ttl:
                return hit[1]
            if hit:
                if key not in self._refreshing:
                    self._refreshing.add(key)
                    self._background(lambda: self._refresh(key, compute))
                return hit[1]
            key_lock = self._key_locks.setdefault(key, threading.Lock())
        with key_lock:  # cold key: one computation, other callers wait for it
            with self._lock:
                hit = self._values.get(key)
            if hit:
                return hit[1]
            value = compute()
            self._store(key, value)
            return value

    def _refresh(self, key: str, compute: Callable[[], Any]) -> None:
        try:
            self._store(key, compute())
        except Exception:
            logger.exception("Background refresh of %s failed; serving the previous value", key)
        finally:
            with self._lock:
                self._refreshing.discard(key)

    def _store(self, key: str, value: Any) -> None:
        with self._lock:
            self._values[key] = (self._clock(), value)

from __future__ import annotations

from dataclasses import dataclass
from time import monotonic
from typing import Any, Callable


_MISS = object()


@dataclass
class _Entry:
    value: Any
    expires_at: float


class DataCacheHook:
    """Optional get_data cache. The agent core does not depend on this class."""

    def __init__(self, ttl_seconds: float = 300, key: Callable[[dict[str, Any]], str] | None = None) -> None:
        self.ttl_seconds = ttl_seconds
        self.key = key or (lambda p: f"{p['source']}:{p['query']}")
        self._items: dict[str, _Entry] = {}

    def before(self, context: Any) -> Any:
        key = self.key(context.payload)
        entry = self._items.get(key)
        if entry and entry.expires_at > monotonic():
            return entry.value
        if entry:
            self._items.pop(key, None)
        return None

    def after(self, context: Any, result: Any) -> Any:
        self._items[self.key(context.payload)] = _Entry(result, monotonic() + self.ttl_seconds)
        return None

    def invalidate(self, predicate: Callable[[str], bool] | None = None) -> None:
        if predicate is None:
            self._items.clear()
        else:
            for key in list(self._items):
                if predicate(key):
                    self._items.pop(key, None)


class AllowAllSecurityHook:
    """Default no-op policy for the POC; replace with a host policy in real use."""

    def before(self, context: Any) -> Any:
        if context.kind == "execute":
            return True
        return None

    def after(self, context: Any, result: Any) -> Any:
        return None


class RecordingEvents:
    """Tiny in-memory event sink useful for tests and local auditing."""

    def __init__(self) -> None:
        self.events: list[tuple[str, dict[str, Any]]] = []

    def publish(self, name: str, payload: dict[str, Any]) -> None:
        self.events.append((name, payload))

"""
Purpose:  Small thread-safe least-recently-used cache (replaces four hand-rolled caches).
Layer:    sleng.infra
Exports:  LruCache
Depends:  standard library only
"""

from __future__ import annotations

import threading
from collections import OrderedDict
from collections.abc import Hashable
from typing import Generic, TypeVar

K = TypeVar("K", bound=Hashable)
V = TypeVar("V")


class LruCache(Generic[K, V]):
    """Keeps at most `capacity` items; the least recently used one is dropped first."""

    def __init__(self, capacity: int = 500) -> None:
        self._items: OrderedDict[K, V] = OrderedDict()
        self._capacity = capacity
        self._lock = threading.Lock()

    def get(self, key: K) -> V | None:
        with self._lock:
            if key not in self._items:
                return None
            self._items.move_to_end(key)
            return self._items[key]

    def put(self, key: K, value: V) -> None:
        with self._lock:
            self._items[key] = value
            self._items.move_to_end(key)
            while len(self._items) > self._capacity:
                self._items.popitem(last=False)

    def __len__(self) -> int:
        with self._lock:
            return len(self._items)

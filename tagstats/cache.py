"""Simple in-memory cache for tag statistics with TTL support."""

import time
from dataclasses import dataclass, field
from typing import Optional

from tagstats.analyzer import TagReport

DEFAULT_TTL_SECONDS = 300  # 5 minutes


@dataclass
class CacheEntry:
    report: TagReport
    created_at: float = field(default_factory=time.monotonic)
    ttl: float = DEFAULT_TTL_SECONDS

    def is_expired(self) -> bool:
        return (time.monotonic() - self.created_at) > self.ttl


class TagReportCache:
    """Thread-safe in-memory cache for TagReport objects."""

    def __init__(self, ttl: float = DEFAULT_TTL_SECONDS) -> None:
        self._store: dict[str, CacheEntry] = {}
        self._ttl = ttl

    @staticmethod
    def _make_key(key: str, value: Optional[str], area: Optional[str]) -> str:
        return f"{key}|{value or ''}|{area or ''}"

    def get(self, key: str, value: Optional[str] = None, area: Optional[str] = None) -> Optional[TagReport]:
        cache_key = self._make_key(key, value, area)
        entry = self._store.get(cache_key)
        if entry is None:
            return None
        if entry.is_expired():
            del self._store[cache_key]
            return None
        return entry.report

    def set(self, report: TagReport, key: str, value: Optional[str] = None, area: Optional[str] = None) -> None:
        cache_key = self._make_key(key, value, area)
        self._store[cache_key] = CacheEntry(report=report, ttl=self._ttl)

    def invalidate(self, key: str, value: Optional[str] = None, area: Optional[str] = None) -> None:
        cache_key = self._make_key(key, value, area)
        self._store.pop(cache_key, None)

    def clear(self) -> None:
        self._store.clear()

    def size(self) -> int:
        return len(self._store)

    def purge_expired(self) -> int:
        expired = [k for k, v in self._store.items() if v.is_expired()]
        for k in expired:
            del self._store[k]
        return len(expired)

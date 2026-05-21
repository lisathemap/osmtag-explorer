"""Tests for tagstats.cache module."""

import time
import unittest
from unittest.mock import patch

from tagstats.analyzer import TagReport, TagStat
from tagstats.cache import CacheEntry, TagReportCache, DEFAULT_TTL_SECONDS


def _make_report(tag_key: str = "amenity") -> TagReport:
    stats = [
        TagStat(key=tag_key, value="cafe", count=100),
        TagStat(key=tag_key, value="restaurant", count=200),
    ]
    return TagReport(key=tag_key, stats=stats)


class TestCacheEntry(unittest.TestCase):
    def test_not_expired_immediately(self):
        entry = CacheEntry(report=_make_report(), ttl=60)
        self.assertFalse(entry.is_expired())

    def test_expired_after_ttl(self):
        entry = CacheEntry(report=_make_report(), ttl=1)
        with patch("tagstats.cache.time.monotonic", return_value=entry.created_at + 2):
            self.assertTrue(entry.is_expired())


class TestTagReportCache(unittest.TestCase):
    def setUp(self):
        self.cache = TagReportCache(ttl=60)
        self.report = _make_report()

    def test_miss_returns_none(self):
        self.assertIsNone(self.cache.get("amenity"))

    def test_set_and_get(self):
        self.cache.set(self.report, key="amenity")
        result = self.cache.get("amenity")
        self.assertIs(result, self.report)

    def test_key_value_cache(self):
        self.cache.set(self.report, key="amenity", value="cafe")
        self.assertIsNone(self.cache.get("amenity"))
        self.assertIsNone(self.cache.get("amenity", value="restaurant"))
        self.assertIs(self.cache.get("amenity", value="cafe"), self.report)

    def test_area_differentiates_entries(self):
        r1 = _make_report()
        r2 = _make_report()
        self.cache.set(r1, key="amenity", area="london")
        self.cache.set(r2, key="amenity", area="paris")
        self.assertIs(self.cache.get("amenity", area="london"), r1)
        self.assertIs(self.cache.get("amenity", area="paris"), r2)

    def test_invalidate_removes_entry(self):
        self.cache.set(self.report, key="amenity")
        self.cache.invalidate("amenity")
        self.assertIsNone(self.cache.get("amenity"))

    def test_clear_empties_cache(self):
        self.cache.set(self.report, key="amenity")
        self.cache.set(self.report, key="shop")
        self.cache.clear()
        self.assertEqual(self.cache.size(), 0)

    def test_expired_entry_returns_none(self):
        self.cache.set(self.report, key="amenity")
        entry = self.cache._store["amenity||"]
        with patch.object(entry, "is_expired", return_value=True):
            self.assertIsNone(self.cache.get("amenity"))

    def test_purge_expired_removes_stale(self):
        self.cache.set(self.report, key="amenity")
        self.cache.set(self.report, key="shop")
        for entry in self.cache._store.values():
            entry.ttl = -1  # force expiry
        removed = self.cache.purge_expired()
        self.assertEqual(removed, 2)
        self.assertEqual(self.cache.size(), 0)

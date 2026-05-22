"""Tests for tagstats.differ."""
import pytest

from tagstats.analyzer import TagReport, TagStat
from tagstats.differ import DiffEntry, DiffReport, diff_reports


def _make_report(*pairs: tuple) -> TagReport:
    stats = [TagStat(key=k, value=v, count=c) for k, v, c in pairs]
    return TagReport(stats=stats)


class TestDiffEntry:
    def test_delta_positive(self):
        e = DiffEntry(key="amenity", value=None, count_a=100, count_b=150)
        assert e.delta == 50

    def test_delta_negative(self):
        e = DiffEntry(key="amenity", value=None, count_a=200, count_b=100)
        assert e.delta == -100

    def test_delta_pct_basic(self):
        e = DiffEntry(key="amenity", value=None, count_a=100, count_b=150)
        assert e.delta_pct == 50.0

    def test_delta_pct_zero_base_returns_inf(self):
        e = DiffEntry(key="amenity", value=None, count_a=0, count_b=10)
        assert e.delta_pct == float("inf")

    def test_label_key_only(self):
        e = DiffEntry(key="amenity", value=None, count_a=1, count_b=2)
        assert e.label == "amenity"

    def test_label_key_value(self):
        e = DiffEntry(key="amenity", value="cafe", count_a=1, count_b=2)
        assert e.label == "amenity=cafe"


class TestDiffReport:
    def _make_diff(self):
        a = _make_report(("highway", None, 500), ("amenity", "cafe", 100))
        b = _make_report(("highway", None, 600), ("shop", "bakery", 50))
        return diff_reports(a, b)

    def test_added_contains_new_tags(self):
        dr = self._make_diff()
        labels = [e.label for e in dr.added]
        assert "shop=bakery" in labels

    def test_removed_contains_dropped_tags(self):
        dr = self._make_diff()
        labels = [e.label for e in dr.removed]
        assert "amenity=cafe" in labels

    def test_changed_contains_updated_counts(self):
        dr = self._make_diff()
        labels = [e.label for e in dr.changed]
        assert "highway" in labels

    def test_unchanged_when_counts_equal(self):
        a = _make_report(("highway", None, 500))
        b = _make_report(("highway", None, 500))
        dr = diff_reports(a, b)
        assert len(dr.unchanged) == 1
        assert dr.unchanged[0].label == "highway"

    def test_total_entries_covers_union(self):
        a = _make_report(("highway", None, 500), ("amenity", "cafe", 100))
        b = _make_report(("highway", None, 600), ("shop", "bakery", 50))
        dr = diff_reports(a, b)
        assert len(dr.entries) == 3


class TestDiffReports:
    def test_empty_reports_produce_empty_diff(self):
        a = TagReport(stats=[])
        b = TagReport(stats=[])
        dr = diff_reports(a, b)
        assert dr.entries == []

    def test_entries_sorted_alphabetically(self):
        a = _make_report(("zoo", None, 10), ("amenity", None, 20))
        b = _make_report(("zoo", None, 15), ("amenity", None, 25))
        dr = diff_reports(a, b)
        labels = [e.label for e in dr.entries]
        assert labels == sorted(labels)

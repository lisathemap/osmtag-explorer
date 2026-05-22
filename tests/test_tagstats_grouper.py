"""Tests for tagstats.grouper."""
from __future__ import annotations

import pytest

from tagstats.analyzer import TagReport, TagStat
from tagstats.grouper import GroupResult, group_by_key, group_by_key_prefix


def _make_report(*entries: tuple) -> TagReport:
    """Build a TagReport from (key, value, count) tuples."""
    stats = [TagStat(key=k, value=v, count=c) for k, v, c in entries]
    return TagReport(stats=stats)


class TestGroupResult:
    def test_keys_are_sorted(self):
        report = _make_report(("highway", None, 10), ("amenity", None, 5))
        result = group_by_key(report)
        assert result.keys() == ["amenity", "highway"]

    def test_total_groups(self):
        report = _make_report(("highway", None, 10), ("amenity", None, 5))
        result = group_by_key(report)
        assert result.total_groups() == 2

    def test_get_existing_key(self):
        report = _make_report(("highway", "residential", 10))
        result = group_by_key(report)
        grp = result.get("highway")
        assert grp is not None
        assert len(grp.stats) == 1

    def test_get_missing_key_returns_none(self):
        report = _make_report(("highway", None, 10))
        result = group_by_key(report)
        assert result.get("nonexistent") is None

    def test_as_dict_structure(self):
        report = _make_report(("highway", "primary", 7))
        result = group_by_key(report)
        d = result.as_dict()
        assert "highway" in d
        assert d["highway"][0]["count"] == 7


class TestGroupByKey:
    def test_single_key_one_group(self):
        report = _make_report(("highway", "primary", 10), ("highway", "secondary", 5))
        result = group_by_key(report)
        assert result.total_groups() == 1
        assert len(result.get("highway").stats) == 2

    def test_multiple_keys_multiple_groups(self):
        report = _make_report(
            ("highway", "primary", 10),
            ("amenity", "cafe", 3),
            ("highway", "secondary", 5),
        )
        result = group_by_key(report)
        assert result.total_groups() == 2
        assert len(result.get("highway").stats) == 2
        assert len(result.get("amenity").stats) == 1

    def test_empty_report_yields_no_groups(self):
        report = TagReport(stats=[])
        result = group_by_key(report)
        assert result.total_groups() == 0


class TestGroupByKeyPrefix:
    def test_groups_by_first_segment(self):
        report = _make_report(
            ("addr:city", None, 10),
            ("addr:street", None, 8),
            ("name", None, 20),
        )
        result = group_by_key_prefix(report)
        assert result.total_groups() == 2
        assert len(result.get("addr").stats) == 2
        assert len(result.get("name").stats) == 1

    def test_key_without_separator_uses_full_key(self):
        report = _make_report(("highway", "primary", 5))
        result = group_by_key_prefix(report)
        assert result.get("highway") is not None

    def test_custom_separator(self):
        report = _make_report(
            ("ref-local", None, 3),
            ("ref-national", None, 7),
        )
        result = group_by_key_prefix(report, separator="-")
        assert result.total_groups() == 1
        assert len(result.get("ref").stats) == 2

    def test_empty_report_yields_no_groups(self):
        result = group_by_key_prefix(TagReport(stats=[]))
        assert result.total_groups() == 0

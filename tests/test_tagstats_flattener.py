"""Tests for tagstats.flattener."""
import pytest

from tagstats.analyzer import TagReport, TagStat
from tagstats.flattener import FlattenOptions, flatten_report


def _make_report(*pairs) -> TagReport:
    stats = [TagStat(key=k, value=v, count=c) for k, v, c in pairs]
    return TagReport(stats=stats)


class TestFlattenOptions:
    def test_defaults(self):
        opts = FlattenOptions()
        assert opts.include_key is True
        assert opts.include_value is True
        assert opts.include_count is True
        assert opts.include_rank is False
        assert opts.top_n is None

    def test_zero_top_n_raises(self):
        with pytest.raises(ValueError, match="top_n"):
            FlattenOptions(top_n=0)

    def test_negative_top_n_raises(self):
        with pytest.raises(ValueError):
            FlattenOptions(top_n=-3)

    def test_positive_top_n_ok(self):
        opts = FlattenOptions(top_n=5)
        assert opts.top_n == 5


class TestFlattenReport:
    def test_returns_list_of_dicts(self):
        report = _make_report(("highway", "primary", 10))
        rows = flatten_report(report)
        assert isinstance(rows, list)
        assert isinstance(rows[0], dict)

    def test_sorted_descending_by_count(self):
        report = _make_report(
            ("amenity", "cafe", 5),
            ("highway", "primary", 20),
            ("name", None, 12),
        )
        rows = flatten_report(report)
        counts = [r["count"] for r in rows]
        assert counts == sorted(counts, reverse=True)

    def test_top_n_limits_rows(self):
        report = _make_report(
            ("a", None, 1),
            ("b", None, 2),
            ("c", None, 3),
            ("d", None, 4),
        )
        rows = flatten_report(report, FlattenOptions(top_n=2))
        assert len(rows) == 2

    def test_top_n_returns_highest_counts(self):
        report = _make_report(
            ("a", None, 1),
            ("b", None, 100),
            ("c", None, 50),
        )
        rows = flatten_report(report, FlattenOptions(top_n=1))
        assert rows[0]["count"] == 100

    def test_include_rank_adds_rank_field(self):
        report = _make_report(("x", "y", 7))
        rows = flatten_report(report, FlattenOptions(include_rank=True))
        assert "rank" in rows[0]
        assert rows[0]["rank"] == 1

    def test_rank_not_present_by_default(self):
        report = _make_report(("x", "y", 7))
        rows = flatten_report(report)
        assert "rank" not in rows[0]

    def test_value_none_becomes_empty_string(self):
        report = _make_report(("name", None, 3))
        rows = flatten_report(report)
        assert rows[0]["value"] == ""

    def test_exclude_key(self):
        report = _make_report(("highway", "primary", 10))
        rows = flatten_report(report, FlattenOptions(include_key=False))
        assert "key" not in rows[0]

    def test_exclude_count(self):
        report = _make_report(("highway", "primary", 10))
        rows = flatten_report(report, FlattenOptions(include_count=False))
        assert "count" not in rows[0]

    def test_empty_report_returns_empty_list(self):
        report = TagReport(stats=[])
        rows = flatten_report(report)
        assert rows == []

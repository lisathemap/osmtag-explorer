"""Tests for tagstats.aggregator module."""
import pytest

from tagstats.analyzer import TagReport, TagStat
from tagstats.aggregator import (
    AggregateOptions,
    AggregateGroup,
    AggregateResult,
    aggregate_report,
)


def _make_report(*pairs) -> TagReport:
    stats = [TagStat(key=k, value=v, count=c) for k, v, c in pairs]
    return TagReport(stats=stats)


# ---------------------------------------------------------------------------
# AggregateOptions
# ---------------------------------------------------------------------------

class TestAggregateOptions:
    def test_defaults(self):
        opts = AggregateOptions()
        assert opts.bucket_by == "key"
        assert opts.top_n == 10
        assert opts.min_count == 0

    def test_invalid_bucket_by_raises(self):
        with pytest.raises(ValueError, match="bucket_by"):
            AggregateOptions(bucket_by="unknown")

    def test_zero_top_n_raises(self):
        with pytest.raises(ValueError, match="top_n"):
            AggregateOptions(top_n=0)

    def test_negative_min_count_raises(self):
        with pytest.raises(ValueError, match="min_count"):
            AggregateOptions(min_count=-1)


# ---------------------------------------------------------------------------
# aggregate_report — bucket_by key
# ---------------------------------------------------------------------------

class TestAggregateByKey:
    def setup_method(self):
        self.report = _make_report(
            ("highway", "primary", 100),
            ("highway", "secondary", 80),
            ("amenity", "cafe", 50),
            ("amenity", "school", 30),
        )

    def test_groups_by_key(self):
        result = aggregate_report(self.report)
        buckets = {g.bucket for g in result.groups}
        assert buckets == {"highway", "amenity"}

    def test_highway_total(self):
        result = aggregate_report(self.report)
        hw = next(g for g in result.groups if g.bucket == "highway")
        assert hw.total == 180

    def test_groups_sorted_descending(self):
        result = aggregate_report(self.report)
        totals = [g.total for g in result.groups]
        assert totals == sorted(totals, reverse=True)

    def test_top_n_limits_groups(self):
        result = aggregate_report(self.report, AggregateOptions(top_n=1))
        assert len(result.groups) == 1
        assert result.groups[0].bucket == "highway"

    def test_min_count_filters_stats(self):
        result = aggregate_report(self.report, AggregateOptions(min_count=60))
        hw = next((g for g in result.groups if g.bucket == "highway"), None)
        assert hw is not None
        assert all(s.count >= 60 for s in hw.stats)


# ---------------------------------------------------------------------------
# aggregate_report — bucket_by value / prefix
# ---------------------------------------------------------------------------

class TestAggregateByValue:
    def test_bucket_by_value(self):
        report = _make_report(("highway", "primary", 10), ("amenity", "primary", 5))
        result = aggregate_report(report, AggregateOptions(bucket_by="value"))
        assert result.groups[0].bucket == "primary"
        assert result.groups[0].total == 15

    def test_bucket_by_prefix(self):
        report = _make_report(
            ("addr:city", None, 40),
            ("addr:street", None, 60),
            ("name", None, 20),
        )
        result = aggregate_report(report, AggregateOptions(bucket_by="prefix"))
        addr_group = next(g for g in result.groups if g.bucket == "addr")
        assert addr_group.total == 100


# ---------------------------------------------------------------------------
# AggregateResult helpers
# ---------------------------------------------------------------------------

class TestAggregateResult:
    def test_total_groups(self):
        report = _make_report(("a", None, 1), ("b", None, 2))
        result = aggregate_report(report)
        assert result.total_groups() == 2

    def test_grand_total(self):
        report = _make_report(("a", None, 10), ("b", None, 20))
        result = aggregate_report(report)
        assert result.grand_total() == 30

    def test_as_dict_keys(self):
        report = _make_report(("highway", "primary", 5))
        d = aggregate_report(report).as_dict()
        assert "total_groups" in d
        assert "grand_total" in d
        assert "groups" in d

"""Tests for tagstats.merger module."""
import pytest
from tagstats.analyzer import TagStat, TagReport
from tagstats.merger import MergeStrategy, merge_reports


def _make_report(pairs: list, label: str = "test") -> TagReport:
    stats = [TagStat(key=k, value=v, count=c) for k, v, c in pairs]
    return TagReport(stats=stats, label=label)


class TestMergeStrategy:
    def test_sum_mode(self):
        ms = MergeStrategy(mode="sum")
        assert ms.combine([10, 20, 5]) == 35

    def test_average_mode_rounds(self):
        ms = MergeStrategy(mode="average")
        assert ms.combine([10, 11]) == 11  # 10.5 -> 11

    def test_max_mode(self):
        ms = MergeStrategy(mode="max")
        assert ms.combine([3, 99, 7]) == 99

    def test_empty_counts_returns_zero(self):
        ms = MergeStrategy()
        assert ms.combine([]) == 0

    def test_unknown_mode_raises(self):
        ms = MergeStrategy(mode="unknown")
        with pytest.raises(ValueError, match="Unknown merge mode"):
            ms.combine([1, 2])


class TestMergeReports:
    def test_empty_list_raises(self):
        with pytest.raises(ValueError, match="empty"):
            merge_reports([])

    def test_single_report_returns_equivalent(self):
        r = _make_report([("amenity", "cafe", 100), ("shop", None, 50)])
        result = merge_reports([r])
        assert len(result.stats) == 2
        assert result.stats[0].count == 100

    def test_sum_strategy_adds_counts(self):
        r1 = _make_report([("amenity", "cafe", 100)])
        r2 = _make_report([("amenity", "cafe", 50)])
        result = merge_reports([r1, r2], MergeStrategy(mode="sum"))
        assert result.stats[0].count == 150

    def test_average_strategy(self):
        r1 = _make_report([("amenity", "cafe", 100)])
        r2 = _make_report([("amenity", "cafe", 50)])
        result = merge_reports([r1, r2], MergeStrategy(mode="average"))
        assert result.stats[0].count == 75

    def test_max_strategy(self):
        r1 = _make_report([("highway", "primary", 200)])
        r2 = _make_report([("highway", "primary", 800)])
        result = merge_reports([r1, r2], MergeStrategy(mode="max"))
        assert result.stats[0].count == 800

    def test_disjoint_keys_are_combined(self):
        r1 = _make_report([("amenity", "cafe", 10)])
        r2 = _make_report([("shop", "bakery", 20)])
        result = merge_reports([r1, r2])
        keys = {(s.key, s.value) for s in result.stats}
        assert ("amenity", "cafe") in keys
        assert ("shop", "bakery") in keys

    def test_result_sorted_by_count_descending(self):
        r1 = _make_report([("a", None, 5), ("b", None, 50)])
        result = merge_reports([r1])
        assert result.stats[0].count >= result.stats[1].count

    def test_custom_label(self):
        r = _make_report([("k", None, 1)])
        result = merge_reports([r], label="my-label")
        assert result.label == "my-label"

    def test_partial_overlap(self):
        r1 = _make_report([("amenity", "cafe", 30), ("shop", None, 10)])
        r2 = _make_report([("amenity", "cafe", 20), ("highway", "primary", 100)])
        result = merge_reports([r1, r2])
        counts = {(s.key, s.value): s.count for s in result.stats}
        assert counts[("amenity", "cafe")] == 50
        assert counts[("shop", None)] == 10
        assert counts[("highway", "primary")] == 100

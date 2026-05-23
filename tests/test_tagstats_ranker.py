"""Tests for tagstats.ranker."""
import pytest

from tagstats.analyzer import TagReport, TagStat
from tagstats.ranker import RankResult, RankedStat, rank_report


def _make_report(*pairs: tuple) -> TagReport:
    """Build a TagReport from (key, value_or_None, count) triples."""
    stats = []
    for key, value, count in pairs:
        stats.append(TagStat(key=key, value=value, count=count))
    return TagReport(stats=stats)


class TestRankedStat:
    def test_label_key_only(self):
        stat = TagStat(key="highway", value=None, count=10)
        rs = RankedStat(stat=stat, rank=1)
        assert rs.label == "highway"

    def test_label_key_value(self):
        stat = TagStat(key="highway", value="residential", count=5)
        rs = RankedStat(stat=stat, rank=2)
        assert rs.label == "highway=residential"

    def test_count_passthrough(self):
        stat = TagStat(key="amenity", value="cafe", count=42)
        rs = RankedStat(stat=stat, rank=1)
        assert rs.count == 42


class TestRankResult:
    def _result(self):
        report = _make_report(
            ("highway", "primary", 100),
            ("amenity", "cafe", 50),
            ("shop", None, 25),
        )
        return rank_report(report)

    def test_len(self):
        result = self._result()
        assert len(result) == 3

    def test_by_rank_found(self):
        result = self._result()
        item = result.by_rank(1)
        assert item is not None
        assert item.count == 100

    def test_by_rank_not_found(self):
        result = self._result()
        assert result.by_rank(99) is None

    def test_as_dicts_keys(self):
        result = self._result()
        d = result.as_dicts()[0]
        assert set(d.keys()) == {"rank", "label", "count"}


class TestRankReportStandardRanking:
    def test_first_rank_is_one(self):
        report = _make_report(("a", None, 10), ("b", None, 5))
        result = rank_report(report)
        assert result.items[0].rank == 1

    def test_ranks_are_sequential_when_no_ties(self):
        report = _make_report(
            ("a", None, 30), ("b", None, 20), ("c", None, 10)
        )
        result = rank_report(report)
        assert [r.rank for r in result.items] == [1, 2, 3]

    def test_tied_entries_share_rank(self):
        report = _make_report(
            ("a", None, 50), ("b", None, 50), ("c", None, 10)
        )
        result = rank_report(report)
        assert result.items[0].rank == 1
        assert result.items[1].rank == 1

    def test_after_tie_rank_skips_standard(self):
        report = _make_report(
            ("a", None, 50), ("b", None, 50), ("c", None, 10)
        )
        result = rank_report(report)
        # standard: 1, 1, 3
        assert result.items[2].rank == 3


class TestRankReportDenseRanking:
    def test_after_tie_rank_does_not_skip(self):
        report = _make_report(
            ("a", None, 50), ("b", None, 50), ("c", None, 10)
        )
        result = rank_report(report, dense=True)
        # dense: 1, 1, 2
        assert result.items[2].rank == 2

    def test_no_ties_same_as_standard(self):
        report = _make_report(
            ("a", None, 30), ("b", None, 20), ("c", None, 10)
        )
        result = rank_report(report, dense=True)
        assert [r.rank for r in result.items] == [1, 2, 3]


class TestRankReportEdgeCases:
    def test_empty_report(self):
        report = TagReport(stats=[])
        result = rank_report(report)
        assert len(result) == 0

    def test_single_stat(self):
        report = _make_report(("highway", None, 99))
        result = rank_report(report)
        assert len(result) == 1
        assert result.items[0].rank == 1

    def test_sorted_descending_by_count(self):
        report = _make_report(
            ("low", None, 1), ("high", None, 999), ("mid", None, 50)
        )
        result = rank_report(report)
        counts = [r.count for r in result.items]
        assert counts == sorted(counts, reverse=True)

"""Tests for tagstats.deduplicator."""
import pytest

from tagstats.analyzer import TagReport, TagStat
from tagstats.deduplicator import (
    DeduplicateOptions,
    DeduplicateResult,
    deduplicate_report,
)


def _make_report(*pairs: tuple) -> TagReport:
    stats = [TagStat(key=k, value=v, count=c) for k, v, c in pairs]
    return TagReport(stats=stats)


# ---------------------------------------------------------------------------
# DeduplicateOptions
# ---------------------------------------------------------------------------

class TestDeduplicateOptions:
    def test_defaults(self):
        opts = DeduplicateOptions()
        assert opts.case_sensitive is False
        assert opts.keep == "first"

    def test_invalid_keep_raises(self):
        with pytest.raises(ValueError, match="keep must be one of"):
            DeduplicateOptions(keep="random")

    def test_valid_keep_values(self):
        for val in ("first", "last", "highest", "lowest"):
            opts = DeduplicateOptions(keep=val)
            assert opts.keep == val


# ---------------------------------------------------------------------------
# DeduplicateResult helpers
# ---------------------------------------------------------------------------

class TestDeduplicateResult:
    def test_kept_property(self):
        report = _make_report(("amenity", None, 10))
        result = DeduplicateResult(report=report, removed=3, original_count=5)
        assert result.kept == 2


# ---------------------------------------------------------------------------
# deduplicate_report
# ---------------------------------------------------------------------------

class TestDeduplicateReport:
    def test_no_duplicates_unchanged(self):
        report = _make_report(
            ("amenity", "cafe", 10),
            ("highway", "residential", 5),
        )
        result = deduplicate_report(report)
        assert result.removed == 0
        assert result.kept == 2

    def test_removes_duplicate_key_value(self):
        report = _make_report(
            ("amenity", "cafe", 10),
            ("amenity", "cafe", 20),
        )
        result = deduplicate_report(report)
        assert result.removed == 1
        assert len(result.report.stats) == 1

    def test_keep_first(self):
        report = _make_report(
            ("amenity", "cafe", 10),
            ("amenity", "cafe", 20),
        )
        result = deduplicate_report(report, DeduplicateOptions(keep="first"))
        assert result.report.stats[0].count == 10

    def test_keep_last(self):
        report = _make_report(
            ("amenity", "cafe", 10),
            ("amenity", "cafe", 20),
        )
        result = deduplicate_report(report, DeduplicateOptions(keep="last"))
        assert result.report.stats[0].count == 20

    def test_keep_highest(self):
        report = _make_report(
            ("amenity", "cafe", 5),
            ("amenity", "cafe", 99),
            ("amenity", "cafe", 42),
        )
        result = deduplicate_report(report, DeduplicateOptions(keep="highest"))
        assert result.report.stats[0].count == 99

    def test_keep_lowest(self):
        report = _make_report(
            ("amenity", "cafe", 5),
            ("amenity", "cafe", 99),
        )
        result = deduplicate_report(report, DeduplicateOptions(keep="lowest"))
        assert result.report.stats[0].count == 5

    def test_case_insensitive_dedup(self):
        report = _make_report(
            ("Amenity", "Cafe", 10),
            ("amenity", "cafe", 20),
        )
        result = deduplicate_report(report, DeduplicateOptions(case_sensitive=False))
        assert result.removed == 1

    def test_case_sensitive_no_dedup(self):
        report = _make_report(
            ("Amenity", "Cafe", 10),
            ("amenity", "cafe", 20),
        )
        result = deduplicate_report(report, DeduplicateOptions(case_sensitive=True))
        assert result.removed == 0

    def test_original_count_recorded(self):
        report = _make_report(
            ("a", None, 1),
            ("a", None, 2),
            ("b", None, 3),
        )
        result = deduplicate_report(report)
        assert result.original_count == 3

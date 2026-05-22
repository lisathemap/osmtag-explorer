"""Tests for tagstats.summarizer."""
import pytest
from tagstats.analyzer import TagReport, TagStat
from tagstats.summarizer import ReportSummary, summarize_report


def _make_report(*pairs) -> TagReport:
    stats = [TagStat(key=k, value=v, count=c) for k, v, c in pairs]
    return TagReport(key="amenity", stats=stats)


class TestSummarizeReportEmpty:
    def test_empty_report_returns_zero_totals(self):
        report = TagReport(key="amenity", stats=[])
        summary = summarize_report(report)
        assert summary.total_tags == 0
        assert summary.total_count == 0

    def test_empty_report_top_tag_is_none(self):
        report = TagReport(key="amenity", stats=[])
        summary = summarize_report(report)
        assert summary.top_tag is None

    def test_empty_report_unique_keys_is_zero(self):
        report = TagReport(key="amenity", stats=[])
        summary = summarize_report(report)
        assert summary.unique_keys == 0


class TestSummarizeReportSingleStat:
    def setup_method(self):
        self.report = _make_report(("amenity", "cafe", 100))
        self.summary = summarize_report(self.report)

    def test_total_tags_is_one(self):
        assert self.summary.total_tags == 1

    def test_total_count_equals_single_count(self):
        assert self.summary.total_count == 100

    def test_mean_equals_count(self):
        assert self.summary.mean_count == 100.0

    def test_median_equals_count(self):
        assert self.summary.median_count == 100.0

    def test_top_tag_label(self):
        assert self.summary.top_tag.tag_label == "amenity=cafe"


class TestSummarizeReportMultipleStats:
    def setup_method(self):
        self.report = _make_report(
            ("amenity", "cafe", 300),
            ("amenity", "restaurant", 500),
            ("amenity", "bar", 100),
            ("amenity", "pub", 200),
        )
        self.summary = summarize_report(self.report)

    def test_total_tags(self):
        assert self.summary.total_tags == 4

    def test_total_count(self):
        assert self.summary.total_count == 1100

    def test_mean_count(self):
        assert self.summary.mean_count == 275.0

    def test_median_count_even_number(self):
        # sorted: 100, 200, 300, 500 -> median = (200+300)/2 = 250
        assert self.summary.median_count == 250.0

    def test_max_count(self):
        assert self.summary.max_count == 500

    def test_min_count(self):
        assert self.summary.min_count == 100

    def test_top_tag_is_highest_count(self):
        assert self.summary.top_tag.value == "restaurant"

    def test_unique_keys_single_key(self):
        assert self.summary.unique_keys == 1


class TestSummarizeReportAsDict:
    def test_as_dict_keys(self):
        report = _make_report(("amenity", "cafe", 42))
        summary = summarize_report(report)
        d = summary.as_dict()
        assert set(d.keys()) == {
            "total_tags", "total_count", "mean_count",
            "median_count", "max_count", "min_count",
            "top_tag", "unique_keys",
        }

    def test_as_dict_top_tag_label(self):
        report = _make_report(("amenity", "cafe", 42))
        summary = summarize_report(report)
        assert summary.as_dict()["top_tag"] == "amenity=cafe"

    def test_as_dict_mean_rounded(self):
        report = _make_report(("a", "x", 1), ("a", "y", 2))
        summary = summarize_report(report)
        assert summary.as_dict()["mean_count"] == 1.5

"""Tests for tagstats.filter module."""
import pytest
from tagstats.analyzer import TagStat, TagReport
from tagstats.filter import FilterCriteria, filter_report, _matches


def _make_report():
    return TagReport(stats=[
        TagStat(key="amenity", value="cafe", count=120),
        TagStat(key="amenity", value="restaurant", count=340),
        TagStat(key="highway", value="residential", count=800),
        TagStat(key="name", value=None, count=50),
        TagStat(key="shop", value="bakery", count=15),
    ])


class TestFilterCriteria:
    def test_is_empty_when_all_none(self):
        assert FilterCriteria().is_empty() is True

    def test_not_empty_when_min_count_set(self):
        assert FilterCriteria(min_count=10).is_empty() is False

    def test_not_empty_when_key_contains_set(self):
        assert FilterCriteria(key_contains="shop").is_empty() is False


class TestMatches:
    def test_min_count_excludes_low(self):
        stat = TagStat(key="x", value=None, count=5)
        assert _matches(stat, FilterCriteria(min_count=10)) is False

    def test_min_count_includes_equal(self):
        stat = TagStat(key="x", value=None, count=10)
        assert _matches(stat, FilterCriteria(min_count=10)) is True

    def test_max_count_excludes_high(self):
        stat = TagStat(key="x", value=None, count=500)
        assert _matches(stat, FilterCriteria(max_count=100)) is False

    def test_key_contains_case_insensitive(self):
        stat = TagStat(key="Highway", value=None, count=10)
        assert _matches(stat, FilterCriteria(key_contains="highway")) is True

    def test_value_contains_none_value(self):
        stat = TagStat(key="name", value=None, count=10)
        assert _matches(stat, FilterCriteria(value_contains="cafe")) is False

    def test_value_contains_matches(self):
        stat = TagStat(key="amenity", value="cafe", count=10)
        assert _matches(stat, FilterCriteria(value_contains="cafe")) is True


class TestFilterReport:
    def setup_method(self):
        self.report = _make_report()

    def test_empty_criteria_returns_all(self):
        result = filter_report(self.report, FilterCriteria())
        assert len(result.stats) == len(self.report.stats)

    def test_min_count_filters_correctly(self):
        result = filter_report(self.report, FilterCriteria(min_count=100))
        assert all(s.count >= 100 for s in result.stats)
        assert len(result.stats) == 3

    def test_key_contains_filters_amenity(self):
        result = filter_report(self.report, FilterCriteria(key_contains="amenity"))
        assert len(result.stats) == 2
        assert all(s.key == "amenity" for s in result.stats)

    def test_combined_criteria(self):
        result = filter_report(
            self.report,
            FilterCriteria(key_contains="amenity", min_count=200)
        )
        assert len(result.stats) == 1
        assert result.stats[0].value == "restaurant"

    def test_returns_new_report_instance(self):
        result = filter_report(self.report, FilterCriteria(min_count=50))
        assert result is not self.report

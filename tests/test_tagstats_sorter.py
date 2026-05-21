"""Tests for tagstats.sorter module."""
import pytest

from tagstats.analyzer import TagReport, TagStat
from tagstats.sorter import (
    SortCriteria,
    SortField,
    SortOrder,
    sort_report,
)


def _make_report() -> TagReport:
    return TagReport(
        stats=[
            TagStat(key="highway", value="primary", count=500),
            TagStat(key="amenity", value=None, count=1200),
            TagStat(key="building", value="yes", count=300),
            TagStat(key="name", value=None, count=800),
        ]
    )


class TestSortCriteria:
    def test_default_field_is_count(self):
        c = SortCriteria()
        assert c.field == SortField.COUNT

    def test_default_order_is_desc(self):
        c = SortCriteria()
        assert c.order == SortOrder.DESC

    def test_is_descending_true_for_desc(self):
        c = SortCriteria(order=SortOrder.DESC)
        assert c.is_descending() is True

    def test_is_descending_false_for_asc(self):
        c = SortCriteria(order=SortOrder.ASC)
        assert c.is_descending() is False


class TestSortReport:
    def test_default_sort_by_count_descending(self):
        report = _make_report()
        result = sort_report(report)
        counts = [s.count for s in result.stats]
        assert counts == sorted(counts, reverse=True)

    def test_sort_by_count_ascending(self):
        report = _make_report()
        criteria = SortCriteria(field=SortField.COUNT, order=SortOrder.ASC)
        result = sort_report(report, criteria)
        counts = [s.count for s in result.stats]
        assert counts == sorted(counts)

    def test_sort_by_key_ascending(self):
        report = _make_report()
        criteria = SortCriteria(field=SortField.KEY, order=SortOrder.ASC)
        result = sort_report(report, criteria)
        keys = [s.key for s in result.stats]
        assert keys == sorted(keys, key=str.lower)

    def test_sort_by_key_descending(self):
        report = _make_report()
        criteria = SortCriteria(field=SortField.KEY, order=SortOrder.DESC)
        result = sort_report(report, criteria)
        keys = [s.key for s in result.stats]
        assert keys == sorted(keys, key=str.lower, reverse=True)

    def test_sort_by_label_ascending(self):
        report = _make_report()
        criteria = SortCriteria(field=SortField.LABEL, order=SortOrder.ASC)
        result = sort_report(report, criteria)
        labels = [s.tag_label for s in result.stats]
        assert labels == sorted(labels, key=str.lower)

    def test_sort_does_not_mutate_original(self):
        report = _make_report()
        original_order = [s.key for s in report.stats]
        sort_report(report, SortCriteria(field=SortField.KEY, order=SortOrder.ASC))
        assert [s.key for s in report.stats] == original_order

    def test_sort_returns_tag_report_instance(self):
        report = _make_report()
        result = sort_report(report)
        assert isinstance(result, TagReport)

    def test_none_criteria_uses_defaults(self):
        report = _make_report()
        result = sort_report(report, None)
        counts = [s.count for s in result.stats]
        assert counts == sorted(counts, reverse=True)

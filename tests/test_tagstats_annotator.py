"""Tests for tagstats.annotator."""
import pytest

from tagstats.analyzer import TagReport, TagStat
from tagstats.annotator import (
    AnnotateOptions,
    AnnotatedStat,
    annotate_report,
    _resolve_category,
)


def _make_report(*pairs) -> TagReport:
    stats = [TagStat(key=k, value=v, count=c) for k, v, c in pairs]
    return TagReport(stats=stats)


class TestAnnotatedStat:
    def test_label_key_only(self):
        stat = TagStat(key="highway", value=None, count=10)
        ann = AnnotatedStat(stat=stat, category="transport")
        assert ann.label == "highway"

    def test_label_key_value(self):
        stat = TagStat(key="highway", value="primary", count=5)
        ann = AnnotatedStat(stat=stat, category="transport")
        assert ann.label == "highway=primary"

    def test_count_passthrough(self):
        stat = TagStat(key="amenity", value="cafe", count=42)
        ann = AnnotatedStat(stat=stat, category="amenity")
        assert ann.count == 42

    def test_as_dict_keys(self):
        stat = TagStat(key="shop", value="bakery", count=7)
        ann = AnnotatedStat(stat=stat, category="commerce", note="a note")
        d = ann.as_dict()
        assert set(d.keys()) == {"key", "value", "count", "category", "note"}

    def test_as_dict_values(self):
        stat = TagStat(key="shop", value="bakery", count=7)
        ann = AnnotatedStat(stat=stat, category="commerce", note=None)
        d = ann.as_dict()
        assert d["key"] == "shop"
        assert d["value"] == "bakery"
        assert d["count"] == 7
        assert d["category"] == "commerce"
        assert d["note"] is None


class TestResolveCategory:
    def test_exact_match(self):
        opts = AnnotateOptions()
        assert _resolve_category("highway", opts) == "transport"

    def test_prefix_match(self):
        opts = AnnotateOptions()
        assert _resolve_category("addr:street", opts) == "address"

    def test_unknown_key_returns_default(self):
        opts = AnnotateOptions(default_category="other")
        assert _resolve_category("unknown_key", opts) == "other"

    def test_unknown_key_no_default_returns_none(self):
        opts = AnnotateOptions(default_category=None)
        assert _resolve_category("unknown_key", opts) is None

    def test_custom_categories(self):
        opts = AnnotateOptions(categories={"mykey": "custom_cat"}, default_category=None)
        assert _resolve_category("mykey", opts) == "custom_cat"
        assert _resolve_category("mykey:sub", opts) == "custom_cat"


class TestAnnotateReport:
    def test_returns_one_per_stat(self):
        report = _make_report(("highway", "primary", 10), ("amenity", "cafe", 5))
        result = annotate_report(report)
        assert len(result) == 2

    def test_empty_report(self):
        report = _make_report()
        result = annotate_report(report)
        assert result == []

    def test_categories_assigned(self):
        report = _make_report(("highway", None, 10), ("shop", "bakery", 3))
        result = annotate_report(report)
        cats = {r.label: r.category for r in result}
        assert cats["highway"] == "transport"
        assert cats["shop=bakery"] == "commerce"

    def test_note_none_by_default(self):
        report = _make_report(("highway", "primary", 10))
        result = annotate_report(report)
        assert result[0].note is None

    def test_note_set_when_enabled_and_has_value(self):
        report = _make_report(("highway", "primary", 10))
        opts = AnnotateOptions(include_note=True)
        result = annotate_report(report, options=opts)
        assert result[0].note is not None
        assert "primary" in result[0].note

    def test_note_none_when_enabled_but_no_value(self):
        report = _make_report(("highway", None, 10))
        opts = AnnotateOptions(include_note=True)
        result = annotate_report(report, options=opts)
        assert result[0].note is None

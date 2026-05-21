"""Tests for tagstats.normalizer."""

import pytest

from tagstats.analyzer import TagReport, TagStat
from tagstats.normalizer import (
    NormalizeOptions,
    normalize_key,
    normalize_value,
    normalize_stat,
    normalize_report,
)


class TestNormalizeKey:
    def test_lowercases_by_default(self):
        assert normalize_key("Highway") == "highway"

    def test_strips_whitespace_by_default(self):
        assert normalize_key("  name  ") == "name"

    def test_no_lowercase_when_disabled(self):
        opts = NormalizeOptions(lowercase_keys=False)
        assert normalize_key("Highway", opts) == "Highway"

    def test_no_strip_when_disabled(self):
        opts = NormalizeOptions(strip_whitespace=False)
        assert normalize_key("  name  ", opts) == "  name  "


class TestNormalizeValue:
    def test_returns_none_for_none(self):
        assert normalize_value(None) is None

    def test_strips_whitespace_by_default(self):
        assert normalize_value("  yes  ") == "yes"

    def test_does_not_lowercase_by_default(self):
        assert normalize_value("YES") == "YES"

    def test_lowercases_when_enabled(self):
        opts = NormalizeOptions(lowercase_values=True)
        assert normalize_value("YES", opts) == "yes"

    def test_collapse_semicolons_keeps_first_token(self):
        opts = NormalizeOptions(collapse_semicolons=True)
        assert normalize_value("residential;living_street", opts) == "residential"

    def test_collapse_semicolons_strips_token(self):
        opts = NormalizeOptions(collapse_semicolons=True)
        assert normalize_value(" primary ; secondary", opts) == "primary"


class TestNormalizeStat:
    def test_key_is_normalized(self):
        stat = TagStat(key="Highway", value="primary", count=10)
        result = normalize_stat(stat)
        assert result.key == "highway"

    def test_value_unchanged_by_default(self):
        stat = TagStat(key="name", value="  Berlin  ", count=5)
        result = normalize_stat(stat)
        assert result.value == "Berlin"

    def test_count_preserved(self):
        stat = TagStat(key="amenity", value="cafe", count=42)
        assert normalize_stat(stat).count == 42


class TestNormalizeReport:
    def _make_report(self, *stats):
        return TagReport(stats=list(stats))

    def test_keys_are_normalized(self):
        report = self._make_report(
            TagStat(key="Highway", value="primary", count=3),
        )
        result = normalize_report(report)
        assert result.stats[0].key == "highway"

    def test_duplicate_keys_after_normalization_are_merged(self):
        report = self._make_report(
            TagStat(key="Highway", value="primary", count=3),
            TagStat(key="highway", value="primary", count=7),
        )
        result = normalize_report(report)
        assert len(result.stats) == 1
        assert result.stats[0].count == 10

    def test_different_values_remain_separate(self):
        report = self._make_report(
            TagStat(key="highway", value="primary", count=3),
            TagStat(key="highway", value="secondary", count=5),
        )
        result = normalize_report(report)
        assert len(result.stats) == 2

    def test_empty_report_returns_empty(self):
        result = normalize_report(TagReport(stats=[]))
        assert result.stats == []

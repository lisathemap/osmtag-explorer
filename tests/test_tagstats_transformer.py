"""Tests for tagstats.transformer."""
import pytest

from tagstats.analyzer import TagReport, TagStat
from tagstats.transformer import (
    TransformRules,
    TransformResult,
    transform_report,
)


def _make_report(*entries):
    """Build a TagReport from (key, value, count) tuples."""
    stats = [TagStat(key=k, value=v, count=c) for k, v, c in entries]
    return TagReport(stats=stats)


class TestTransformRules:
    def test_defaults_are_empty(self):
        rules = TransformRules()
        assert rules.key_aliases == {}
        assert rules.value_aliases == {}
        assert rules.drop_keys == frozenset()

    def test_drop_keys_coerced_to_frozenset(self):
        rules = TransformRules(drop_keys=["highway", "name"])
        assert isinstance(rules.drop_keys, frozenset)
        assert "highway" in rules.drop_keys


class TestTransformResult:
    def test_unchanged_calculation(self):
        report = _make_report(("k", None, 1), ("k2", None, 2))
        result = TransformResult(report=report, remapped=1, dropped=0)
        assert result.unchanged == 1

    def test_as_dict_keys(self):
        report = _make_report(("k", None, 5))
        result = TransformResult(report=report, remapped=0, dropped=2)
        d = result.as_dict()
        assert set(d.keys()) == {"total", "remapped", "dropped", "unchanged"}

    def test_as_dict_values(self):
        report = _make_report(("k", None, 1), ("k2", None, 1))
        result = TransformResult(report=report, remapped=1, dropped=3)
        d = result.as_dict()
        assert d["total"] == 2
        assert d["remapped"] == 1
        assert d["dropped"] == 3
        assert d["unchanged"] == 1


class TestTransformReport:
    def test_no_rules_returns_same_stats(self):
        report = _make_report(("highway", "residential", 10))
        result = transform_report(report, TransformRules())
        assert len(result.report.stats) == 1
        assert result.remapped == 0
        assert result.dropped == 0

    def test_key_alias_remaps_key(self):
        report = _make_report(("hwy", None, 5))
        rules = TransformRules(key_aliases={"hwy": "highway"})
        result = transform_report(report, rules)
        assert result.report.stats[0].key == "highway"
        assert result.remapped == 1

    def test_value_alias_remaps_value(self):
        report = _make_report(("surface", "asph", 3))
        rules = TransformRules(value_aliases={"asph": "asphalt"})
        result = transform_report(report, rules)
        assert result.report.stats[0].value == "asphalt"
        assert result.remapped == 1

    def test_drop_key_removes_stat(self):
        report = _make_report(("name", None, 100), ("highway", None, 50))
        rules = TransformRules(drop_keys=["name"])
        result = transform_report(report, rules)
        assert len(result.report.stats) == 1
        assert result.dropped == 1
        assert result.report.stats[0].key == "highway"

    def test_count_is_preserved(self):
        report = _make_report(("old_key", "v", 42))
        rules = TransformRules(key_aliases={"old_key": "new_key"})
        result = transform_report(report, rules)
        assert result.report.stats[0].count == 42

    def test_empty_report_returns_empty_result(self):
        report = TagReport(stats=[])
        result = transform_report(report, TransformRules())
        assert result.report.stats == []
        assert result.remapped == 0
        assert result.dropped == 0

    def test_multiple_aliases_applied_independently(self):
        report = _make_report(("k1", "v1", 1), ("k2", "v2", 2))
        rules = TransformRules(
            key_aliases={"k1": "key_one"},
            value_aliases={"v2": "value_two"},
        )
        result = transform_report(report, rules)
        keys = [s.key for s in result.report.stats]
        values = [s.value for s in result.report.stats]
        assert "key_one" in keys
        assert "value_two" in values
        assert result.remapped == 2

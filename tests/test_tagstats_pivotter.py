"""Tests for tagstats.pivotter."""
import pytest

from tagstats.analyzer import TagReport, TagStat
from tagstats.pivotter import PivotOptions, PivotTable, pivot_report


def _make_report(*triples) -> TagReport:
    """Build a TagReport from (key, value, count) triples."""
    stats = [TagStat(key=k, value=v, count=c) for k, v, c in triples]
    return TagReport(stats=stats)


# ---------------------------------------------------------------------------
# PivotOptions
# ---------------------------------------------------------------------------

class TestPivotOptions:
    def test_defaults(self):
        opts = PivotOptions()
        assert opts.top_keys == 10
        assert opts.top_values == 10
        assert opts.fill_value == 0

    def test_zero_top_keys_raises(self):
        with pytest.raises(ValueError, match="top_keys"):
            PivotOptions(top_keys=0)

    def test_zero_top_values_raises(self):
        with pytest.raises(ValueError, match="top_values"):
            PivotOptions(top_values=0)

    def test_negative_top_keys_raises(self):
        with pytest.raises(ValueError):
            PivotOptions(top_keys=-1)


# ---------------------------------------------------------------------------
# PivotTable.get
# ---------------------------------------------------------------------------

class TestPivotTableGet:
    def _table(self):
        return PivotTable(
            keys=["amenity"],
            values=["cafe"],
            cells={"amenity": {"cafe": 42}},
            fill_value=0,
        )

    def test_get_existing_cell(self):
        assert self._table().get("amenity", "cafe") == 42

    def test_get_missing_key_returns_fill(self):
        assert self._table().get("shop", "cafe") == 0

    def test_get_missing_value_returns_fill(self):
        assert self._table().get("amenity", "pub") == 0

    def test_as_dict_structure(self):
        d = self._table().as_dict()
        assert "keys" in d and "values" in d and "cells" in d
        assert d["cells"]["amenity"]["cafe"] == 42


# ---------------------------------------------------------------------------
# pivot_report
# ---------------------------------------------------------------------------

class TestPivotReport:
    def _sample(self):
        return _make_report(
            ("amenity", "cafe", 300),
            ("amenity", "pub", 200),
            ("shop", "bakery", 150),
            ("shop", "cafe", 50),
        )

    def test_keys_sorted_by_total_desc(self):
        table = pivot_report(self._sample())
        assert table.keys[0] == "amenity"  # 500 total
        assert table.keys[1] == "shop"     # 200 total

    def test_values_sorted_by_total_desc(self):
        table = pivot_report(self._sample())
        assert table.values[0] == "cafe"  # 350 total
        assert table.values[1] == "pub"   # 200 total

    def test_cell_value_correct(self):
        table = pivot_report(self._sample())
        assert table.get("amenity", "cafe") == 300
        assert table.get("shop", "bakery") == 150

    def test_top_keys_limit_respected(self):
        table = pivot_report(self._sample(), PivotOptions(top_keys=1))
        assert len(table.keys) == 1

    def test_top_values_limit_respected(self):
        table = pivot_report(self._sample(), PivotOptions(top_values=1))
        assert len(table.values) == 1

    def test_stats_without_value_excluded(self):
        report = _make_report(("amenity", None, 999))
        table = pivot_report(report)
        assert len(table.keys) == 0

    def test_default_options_used_when_none(self):
        table = pivot_report(self._sample(), None)
        assert isinstance(table, PivotTable)

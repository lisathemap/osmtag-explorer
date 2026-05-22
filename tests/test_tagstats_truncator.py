"""Tests for tagstats.truncator."""
import pytest

from tagstats.analyzer import TagReport, TagStat
from tagstats.truncator import TruncateOptions, TruncateResult, truncate_report


def _make_report(n: int = 10) -> TagReport:
    stats = [TagStat(key="amenity", value=str(i), count=(n - i) * 10) for i in range(n)]
    return TagReport(stats=stats)


# ---------------------------------------------------------------------------
# TruncateOptions validation
# ---------------------------------------------------------------------------

class TestTruncateOptions:
    def test_default_limit_is_50(self):
        opts = TruncateOptions()
        assert opts.limit == 50

    def test_default_offset_is_0(self):
        opts = TruncateOptions()
        assert opts.offset == 0

    def test_zero_limit_raises(self):
        with pytest.raises(ValueError, match="limit"):
            TruncateOptions(limit=0)

    def test_negative_limit_raises(self):
        with pytest.raises(ValueError, match="limit"):
            TruncateOptions(limit=-5)

    def test_negative_offset_raises(self):
        with pytest.raises(ValueError, match="offset"):
            TruncateOptions(offset=-1)


# ---------------------------------------------------------------------------
# truncate_report
# ---------------------------------------------------------------------------

class TestTruncateReport:
    def test_returns_truncate_result(self):
        report = _make_report(5)
        result = truncate_report(report)
        assert isinstance(result, TruncateResult)

    def test_total_reflects_full_report(self):
        report = _make_report(20)
        result = truncate_report(report, TruncateOptions(limit=5))
        assert result.total == 20

    def test_limit_caps_returned_rows(self):
        report = _make_report(20)
        result = truncate_report(report, TruncateOptions(limit=7))
        assert result.returned == 7

    def test_offset_skips_rows(self):
        report = _make_report(10)
        result = truncate_report(report, TruncateOptions(limit=5, offset=3))
        assert result.stats[0].value == "3"

    def test_offset_beyond_total_returns_empty(self):
        report = _make_report(5)
        result = truncate_report(report, TruncateOptions(limit=10, offset=10))
        assert result.returned == 0

    def test_has_more_true_when_items_remain(self):
        report = _make_report(10)
        result = truncate_report(report, TruncateOptions(limit=5, offset=0))
        assert result.has_more is True

    def test_has_more_false_when_all_returned(self):
        report = _make_report(5)
        result = truncate_report(report, TruncateOptions(limit=10, offset=0))
        assert result.has_more is False

    def test_as_dict_keys(self):
        report = _make_report(8)
        result = truncate_report(report, TruncateOptions(limit=3, offset=1))
        d = result.as_dict()
        assert set(d.keys()) == {"total", "limit", "offset", "returned", "has_more"}

    def test_none_options_uses_defaults(self):
        report = _make_report(10)
        result = truncate_report(report, None)
        assert result.limit == 50
        assert result.offset == 0

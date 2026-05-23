"""Tests for tagstats.sampler."""
import pytest

from tagstats.analyzer import TagReport, TagStat
from tagstats.sampler import SampleOptions, SampleResult, sample_report


def _make_report(n: int = 10) -> TagReport:
    stats = [TagStat(key=f"key{i}", value=None, count=(i + 1) * 5) for i in range(n)]
    return TagReport(stats=stats)


class TestSampleOptions:
    def test_default_size_is_10(self):
        opts = SampleOptions()
        assert opts.size == 10

    def test_default_seed_is_none(self):
        assert SampleOptions().seed is None

    def test_default_with_replacement_is_false(self):
        assert SampleOptions().with_replacement is False

    def test_zero_size_raises(self):
        with pytest.raises(ValueError):
            SampleOptions(size=0)

    def test_negative_size_raises(self):
        with pytest.raises(ValueError):
            SampleOptions(size=-1)


class TestSampleResult:
    def test_returned_equals_items_length(self):
        report = _make_report(5)
        result = sample_report(report, SampleOptions(size=3))
        assert result.returned == len(result.items)

    def test_is_full_population_when_sample_equals_total(self):
        report = _make_report(3)
        result = sample_report(report, SampleOptions(size=3))
        assert result.is_full_population is True

    def test_not_full_population_when_sample_smaller(self):
        report = _make_report(10)
        result = sample_report(report, SampleOptions(size=5))
        assert result.is_full_population is False

    def test_as_dict_has_expected_keys(self):
        report = _make_report(5)
        result = sample_report(report, SampleOptions(size=2))
        d = result.as_dict()
        assert "returned" in d
        assert "total_available" in d
        assert "seed_used" in d
        assert "items" in d


class TestSampleReport:
    def test_size_capped_at_population(self):
        report = _make_report(4)
        result = sample_report(report, SampleOptions(size=20))
        assert result.returned == 4

    def test_empty_report_returns_empty(self):
        report = TagReport(stats=[])
        result = sample_report(report, SampleOptions(size=5))
        assert result.returned == 0
        assert result.total_available == 0

    def test_seed_produces_deterministic_results(self):
        report = _make_report(20)
        opts = SampleOptions(size=5, seed=42)
        r1 = sample_report(report, opts)
        r2 = sample_report(report, opts)
        assert [s.key for s in r1.items] == [s.key for s in r2.items]

    def test_different_seeds_may_differ(self):
        report = _make_report(20)
        r1 = sample_report(report, SampleOptions(size=5, seed=1))
        r2 = sample_report(report, SampleOptions(size=5, seed=99))
        assert [s.key for s in r1.items] != [s.key for s in r2.items]

    def test_with_replacement_allows_larger_sample(self):
        report = _make_report(3)
        result = sample_report(report, SampleOptions(size=10, with_replacement=True))
        assert result.returned == 10

    def test_default_options_used_when_none_passed(self):
        report = _make_report(20)
        result = sample_report(report)
        assert result.returned == 10

    def test_total_available_is_correct(self):
        report = _make_report(7)
        result = sample_report(report, SampleOptions(size=3))
        assert result.total_available == 7

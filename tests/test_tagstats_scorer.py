"""Tests for tagstats.scorer."""
import pytest
from tagstats.analyzer import TagStat, TagReport
from tagstats.scorer import (
    ScoreOptions,
    ScoredStat,
    score_stat,
    score_report,
    _normalize_count,
    _match_score,
)


def _make_report(*pairs) -> TagReport:
    stats = [TagStat(key=k, value=v, count=c) for k, v, c in pairs]
    return TagReport(stats=stats)


class TestScoreOptions:
    def test_default_weights(self):
        opts = ScoreOptions()
        assert opts.count_weight == 1.0
        assert opts.match_weight == 2.0

    def test_negative_count_weight_raises(self):
        with pytest.raises(ValueError, match="count_weight"):
            ScoreOptions(count_weight=-0.1)

    def test_negative_match_weight_raises(self):
        with pytest.raises(ValueError, match="match_weight"):
            ScoreOptions(match_weight=-1.0)


class TestNormalizeCount:
    def test_max_count_zero_returns_zero(self):
        assert _normalize_count(0, 0) == 0.0

    def test_full_count_returns_one(self):
        assert _normalize_count(100, 100) == 1.0

    def test_partial_count(self):
        assert _normalize_count(50, 200) == 0.25

    def test_capped_at_one(self):
        assert _normalize_count(300, 100) == 1.0


class TestMatchScore:
    def _stat(self, key, value=None):
        return TagStat(key=key, value=value, count=1)

    def test_no_query_returns_zero(self):
        assert _match_score(self._stat("highway"), None) == 0.0

    def test_exact_match_returns_one(self):
        assert _match_score(self._stat("highway"), "highway") == 1.0

    def test_prefix_match(self):
        assert _match_score(self._stat("highway"), "high") == 0.75

    def test_substring_match(self):
        assert _match_score(self._stat("highway"), "ghwa") == 0.5

    def test_no_match_returns_zero(self):
        assert _match_score(self._stat("highway"), "zzz") == 0.0

    def test_case_insensitive(self):
        assert _match_score(self._stat("Highway"), "HIGHWAY") == 1.0


class TestScoreStat:
    def test_score_is_float(self):
        stat = TagStat(key="amenity", value=None, count=100)
        opts = ScoreOptions(max_count=100)
        result = score_stat(stat, opts)
        assert isinstance(result.score, float)

    def test_higher_count_higher_score(self):
        s1 = TagStat(key="a", value=None, count=10)
        s2 = TagStat(key="b", value=None, count=90)
        opts = ScoreOptions(max_count=100)
        assert score_stat(s2, opts).score > score_stat(s1, opts).score

    def test_label_property(self):
        stat = TagStat(key="amenity", value="cafe", count=5)
        opts = ScoreOptions(max_count=100)
        result = score_stat(stat, opts)
        assert result.label == "amenity=cafe"


class TestScoreReport:
    def test_returns_sorted_descending(self):
        report = _make_report(("a", None, 10), ("b", None, 90), ("c", None, 50))
        results = score_report(report)
        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_empty_report_returns_empty(self):
        report = TagReport(stats=[])
        assert score_report(report) == []

    def test_query_boosts_matching_stat(self):
        report = _make_report(("highway", None, 10), ("amenity", None, 10))
        opts = ScoreOptions(query="highway")
        results = score_report(report, opts)
        assert results[0].stat.key == "highway"

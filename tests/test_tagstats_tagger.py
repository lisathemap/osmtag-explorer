"""Tests for tagstats.tagger suggestion utilities."""
import pytest
from tagstats.tagger import (
    TagSuggestion,
    suggest_keys,
    suggest_values,
    suggest_tags,
)


class TestTagSuggestion:
    def test_label_key_only(self):
        s = TagSuggestion(key="amenity")
        assert s.label == "amenity"

    def test_label_key_value(self):
        s = TagSuggestion(key="amenity", value="cafe")
        assert s.label == "amenity=cafe"

    def test_default_score(self):
        s = TagSuggestion(key="highway")
        assert s.score == 1.0


class TestSuggestKeys:
    def test_returns_list_of_suggestions(self):
        results = suggest_keys("a")
        assert all(isinstance(r, TagSuggestion) for r in results)

    def test_prefix_filters_results(self):
        results = suggest_keys("am")
        assert all(r.key.startswith("am") for r in results)

    def test_amenity_found(self):
        keys = [r.key for r in suggest_keys("amen")]
        assert "amenity" in keys

    def test_no_match_returns_empty(self):
        results = suggest_keys("zzz")
        assert results == []

    def test_limit_respected(self):
        results = suggest_keys("", limit=3)
        assert len(results) <= 3

    def test_results_sorted(self):
        results = suggest_keys("")
        keys = [r.key for r in results]
        assert keys == sorted(keys)

    def test_case_insensitive_prefix(self):
        results = suggest_keys("AMEN")
        keys = [r.key for r in results]
        assert "amenity" in keys


class TestSuggestValues:
    def test_returns_values_for_known_key(self):
        results = suggest_values("amenity")
        assert len(results) > 0

    def test_unknown_key_returns_empty(self):
        results = suggest_values("nonexistent_key")
        assert results == []

    def test_prefix_filters_values(self):
        results = suggest_values("amenity", prefix="ca")
        assert all(r.value.startswith("ca") for r in results)

    def test_limit_respected(self):
        results = suggest_values("amenity", limit=2)
        assert len(results) <= 2

    def test_suggestion_has_correct_key(self):
        results = suggest_values("building")
        assert all(r.key == "building" for r in results)

    def test_results_sorted(self):
        results = suggest_values("highway")
        values = [r.value for r in results]
        assert values == sorted(values)


class TestSuggestTags:
    def test_key_only_query_returns_key_suggestions(self):
        results = suggest_tags("high")
        assert all(r.value is None for r in results)

    def test_key_value_query_returns_value_suggestions(self):
        results = suggest_tags("amenity=ca")
        assert all(r.key == "amenity" for r in results)
        assert all(r.value is not None for r in results)

    def test_empty_query_returns_all_keys(self):
        results = suggest_tags("")
        assert len(results) > 0

    def test_limit_propagated(self):
        results = suggest_tags("a", limit=2)
        assert len(results) <= 2

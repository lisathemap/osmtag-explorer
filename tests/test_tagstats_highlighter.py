import pytest
from tagstats.highlighter import Span, HighlightResult, highlight, highlight_stat


class TestSpan:
    def test_valid_span(self):
        s = Span(0, 5)
        assert s.length == 5

    def test_zero_length_span(self):
        s = Span(3, 3)
        assert s.length == 0

    def test_negative_start_raises(self):
        with pytest.raises(ValueError):
            Span(-1, 5)

    def test_end_before_start_raises(self):
        with pytest.raises(ValueError):
            Span(5, 2)


class TestHighlightResult:
    def test_has_match_false_when_no_spans(self):
        r = HighlightResult(text="hello")
        assert not r.has_match

    def test_has_match_true_with_spans(self):
        r = HighlightResult(text="hello", spans=[Span(0, 2)])
        assert r.has_match

    def test_to_html_no_spans_returns_plain_text(self):
        r = HighlightResult(text="hello")
        assert r.to_html() == "hello"

    def test_to_html_wraps_span(self):
        r = HighlightResult(text="hello world", spans=[Span(6, 11)])
        assert r.to_html() == "hello <mark>world</mark>"

    def test_to_html_custom_tag(self):
        r = HighlightResult(text="abc", spans=[Span(0, 3)])
        assert r.to_html(tag="strong") == "<strong>abc</strong>"

    def test_to_html_multiple_spans(self):
        r = HighlightResult(text="ababab", spans=[Span(0, 2), Span(2, 4), Span(4, 6)])
        html = r.to_html()
        assert html.count("<mark>") == 3


class TestHighlight:
    def test_empty_query_returns_no_spans(self):
        result = highlight("highway", "")
        assert not result.has_match

    def test_single_match(self):
        result = highlight("highway", "way")
        assert len(result.spans) == 1
        assert result.spans[0] == Span(4, 7)

    def test_multiple_matches(self):
        result = highlight("ababab", "ab")
        assert len(result.spans) == 3

    def test_case_insensitive_by_default(self):
        result = highlight("Highway", "high")
        assert result.has_match

    def test_case_sensitive_no_match(self):
        result = highlight("Highway", "high", case_sensitive=True)
        assert not result.has_match

    def test_case_sensitive_match(self):
        result = highlight("Highway", "High", case_sensitive=True)
        assert result.has_match

    def test_no_match_returns_empty_spans(self):
        result = highlight("highway", "xyz")
        assert result.spans == []

    def test_original_text_preserved_in_result(self):
        result = highlight("Highway", "high")
        assert result.text == "Highway"


class TestHighlightStat:
    def test_key_highlighted(self):
        r = highlight_stat("highway", "primary", "high")
        assert r["key"].has_match

    def test_value_highlighted(self):
        r = highlight_stat("highway", "primary", "prim")
        assert r["value"].has_match

    def test_value_none_when_no_value(self):
        r = highlight_stat("name", None, "nam")
        assert r["value"] is None

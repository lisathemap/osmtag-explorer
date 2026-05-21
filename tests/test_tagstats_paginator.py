import pytest
from tagstats.analyzer import TagStat
from tagstats.paginator import paginate, PageResult, DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE


def _make_stats(n: int) -> list:
    return [TagStat(key="amenity", value=str(i), count=n - i) for i in range(n)]


class TestPageResult:
    def test_total_pages_exact_division(self):
        r = PageResult(items=[], page=1, page_size=10, total=30)
        assert r.total_pages == 3

    def test_total_pages_rounds_up(self):
        r = PageResult(items=[], page=1, page_size=10, total=25)
        assert r.total_pages == 3

    def test_has_next_true(self):
        r = PageResult(items=[], page=1, page_size=10, total=25)
        assert r.has_next is True

    def test_has_next_false_on_last_page(self):
        r = PageResult(items=[], page=3, page_size=10, total=25)
        assert r.has_next is False

    def test_has_prev_false_on_first_page(self):
        r = PageResult(items=[], page=1, page_size=10, total=25)
        assert r.has_prev is False

    def test_has_prev_true(self):
        r = PageResult(items=[], page=2, page_size=10, total=25)
        assert r.has_prev is True

    def test_total_pages_zero_when_page_size_zero(self):
        r = PageResult(items=[], page=1, page_size=0, total=10)
        assert r.total_pages == 0


class TestPaginate:
    def test_first_page_returns_correct_items(self):
        stats = _make_stats(50)
        result = paginate(stats, page=1, page_size=10)
        assert result.items == stats[:10]

    def test_second_page_returns_correct_items(self):
        stats = _make_stats(50)
        result = paginate(stats, page=2, page_size=10)
        assert result.items == stats[10:20]

    def test_last_page_may_be_partial(self):
        stats = _make_stats(25)
        result = paginate(stats, page=3, page_size=10)
        assert len(result.items) == 5

    def test_total_reflects_full_list(self):
        stats = _make_stats(35)
        result = paginate(stats, page=1, page_size=10)
        assert result.total == 35

    def test_page_beyond_range_returns_empty(self):
        stats = _make_stats(10)
        result = paginate(stats, page=5, page_size=10)
        assert result.items == []

    def test_invalid_page_raises(self):
        with pytest.raises(ValueError, match="page must be"):
            paginate(_make_stats(10), page=0)

    def test_invalid_page_size_too_small_raises(self):
        with pytest.raises(ValueError, match="page_size must be"):
            paginate(_make_stats(10), page_size=0)

    def test_invalid_page_size_too_large_raises(self):
        with pytest.raises(ValueError, match="page_size must be"):
            paginate(_make_stats(10), page_size=MAX_PAGE_SIZE + 1)

    def test_default_page_size_used(self):
        stats = _make_stats(100)
        result = paginate(stats)
        assert result.page_size == DEFAULT_PAGE_SIZE
        assert len(result.items) == DEFAULT_PAGE_SIZE

from dataclasses import dataclass
from typing import List, Generic, TypeVar
from tagstats.analyzer import TagStat

T = TypeVar("T")

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 200


@dataclass
class PageResult(Generic[T]):
    items: List[T]
    page: int
    page_size: int
    total: int

    @property
    def total_pages(self) -> int:
        if self.page_size == 0:
            return 0
        return (self.total + self.page_size - 1) // self.page_size

    @property
    def has_next(self) -> bool:
        return self.page < self.total_pages

    @property
    def has_prev(self) -> bool:
        return self.page > 1


def paginate(
    items: List[TagStat],
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> PageResult[TagStat]:
    """Return a PageResult for the given list of TagStat items."""
    if page < 1:
        raise ValueError(f"page must be >= 1, got {page}")
    if page_size < 1 or page_size > MAX_PAGE_SIZE:
        raise ValueError(
            f"page_size must be between 1 and {MAX_PAGE_SIZE}, got {page_size}"
        )

    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    return PageResult(
        items=items[start:end],
        page=page,
        page_size=page_size,
        total=total,
    )

"""Truncate a TagReport to a maximum number of entries, with optional offset."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from tagstats.analyzer import TagReport, TagStat


@dataclass
class TruncateOptions:
    limit: int = 50
    offset: int = 0

    def __post_init__(self) -> None:
        if self.limit < 1:
            raise ValueError(f"limit must be >= 1, got {self.limit}")
        if self.offset < 0:
            raise ValueError(f"offset must be >= 0, got {self.offset}")


@dataclass
class TruncateResult:
    stats: list[TagStat]
    total: int
    limit: int
    offset: int

    @property
    def returned(self) -> int:
        return len(self.stats)

    @property
    def has_more(self) -> bool:
        return self.offset + self.returned < self.total

    def as_dict(self) -> dict:
        return {
            "total": self.total,
            "limit": self.limit,
            "offset": self.offset,
            "returned": self.returned,
            "has_more": self.has_more,
        }


def truncate_report(
    report: TagReport,
    options: Optional[TruncateOptions] = None,
) -> TruncateResult:
    """Return a slice of *report* according to *options*."""
    if options is None:
        options = TruncateOptions()

    all_stats: list[TagStat] = list(report.stats)
    total = len(all_stats)
    sliced = all_stats[options.offset : options.offset + options.limit]

    return TruncateResult(
        stats=sliced,
        total=total,
        limit=options.limit,
        offset=options.offset,
    )

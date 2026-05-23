"""Flatten a TagReport into a simple list of dicts for export or display."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from tagstats.analyzer import TagReport, TagStat


@dataclass
class FlattenOptions:
    include_key: bool = True
    include_value: bool = True
    include_count: bool = True
    include_rank: bool = False
    top_n: Optional[int] = None

    def __post_init__(self) -> None:
        if self.top_n is not None and self.top_n < 1:
            raise ValueError("top_n must be a positive integer")


@dataclass
class FlatRow:
    key: str
    value: Optional[str]
    count: int
    rank: Optional[int] = field(default=None)

    def as_dict(self, opts: FlattenOptions) -> dict:
        row: dict = {}
        if opts.include_key:
            row["key"] = self.key
        if opts.include_value:
            row["value"] = self.value if self.value is not None else ""
        if opts.include_count:
            row["count"] = self.count
        if opts.include_rank and self.rank is not None:
            row["rank"] = self.rank
        return row


def flatten_report(
    report: TagReport,
    opts: Optional[FlattenOptions] = None,
) -> List[dict]:
    """Return a list of flat dicts from a TagReport, sorted by count descending."""
    if opts is None:
        opts = FlattenOptions()

    stats: List[TagStat] = sorted(report.stats, key=lambda s: s.count, reverse=True)

    if opts.top_n is not None:
        stats = stats[: opts.top_n]

    rows: List[dict] = []
    for rank, stat in enumerate(stats, start=1):
        row = FlatRow(
            key=stat.key,
            value=stat.value,
            count=stat.count,
            rank=rank if opts.include_rank else None,
        )
        rows.append(row.as_dict(opts))

    return rows

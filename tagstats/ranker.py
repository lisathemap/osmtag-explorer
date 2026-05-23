"""Rank TagStats within a TagReport by assigning ordinal positions."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from tagstats.analyzer import TagReport, TagStat


@dataclass(frozen=True)
class RankedStat:
    """A TagStat decorated with its rank (1-based)."""

    stat: TagStat
    rank: int

    @property
    def label(self) -> str:  # convenience passthrough
        return self.stat.tag_label

    @property
    def count(self) -> int:
        return self.stat.count


@dataclass(frozen=True)
class RankResult:
    """Ordered collection of RankedStat entries."""

    items: List[RankedStat]

    def __len__(self) -> int:
        return len(self.items)

    def by_rank(self, rank: int) -> RankedStat | None:
        """Return the entry with the given rank, or None."""
        for item in self.items:
            if item.rank == rank:
                return item
        return None

    def as_dicts(self) -> List[dict]:
        return [
            {"rank": item.rank, "label": item.label, "count": item.count}
            for item in self.items
        ]


def rank_report(
    report: TagReport,
    *,
    dense: bool = False,
) -> RankResult:
    """Rank all stats in *report* by descending count.

    Parameters
    ----------
    report:
        Source report whose stats will be ranked.
    dense:
        When *True* use dense ranking (1, 2, 2, 3 …).
        When *False* (default) use standard competition ranking (1, 2, 2, 4 …).
    """
    sorted_stats: List[TagStat] = sorted(
        report.stats, key=lambda s: s.count, reverse=True
    )

    ranked: List[RankedStat] = []
    prev_count: int | None = None
    prev_rank: int = 0
    position: int = 0

    for stat in sorted_stats:
        position += 1
        if stat.count == prev_count:
            rank = prev_rank
        else:
            rank = len(ranked) + 1 if dense else position
            prev_rank = rank
        prev_count = stat.count
        ranked.append(RankedStat(stat=stat, rank=rank))

    return RankResult(items=ranked)

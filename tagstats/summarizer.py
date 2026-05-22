"""Summarize a TagReport into aggregate statistics."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from tagstats.analyzer import TagReport, TagStat


@dataclass
class ReportSummary:
    total_tags: int
    total_count: int
    mean_count: float
    median_count: float
    max_count: int
    min_count: int
    top_tag: Optional[TagStat]
    unique_keys: int

    def as_dict(self) -> dict:
        return {
            "total_tags": self.total_tags,
            "total_count": self.total_count,
            "mean_count": round(self.mean_count, 2),
            "median_count": self.median_count,
            "max_count": self.max_count,
            "min_count": self.min_count,
            "top_tag": self.top_tag.tag_label if self.top_tag else None,
            "unique_keys": self.unique_keys,
        }


def summarize_report(report: TagReport) -> ReportSummary:
    """Compute aggregate statistics for a TagReport."""
    stats = report.stats
    if not stats:
        return ReportSummary(
            total_tags=0,
            total_count=0,
            mean_count=0.0,
            median_count=0.0,
            max_count=0,
            min_count=0,
            top_tag=None,
            unique_keys=0,
        )

    counts = [s.count for s in stats]
    total = sum(counts)
    n = len(counts)
    sorted_counts = sorted(counts)

    if n % 2 == 1:
        median = float(sorted_counts[n // 2])
    else:
        median = (sorted_counts[n // 2 - 1] + sorted_counts[n // 2]) / 2.0

    sorted_stats = sorted(stats, key=lambda s: s.count, reverse=True)
    unique_keys = len({s.key for s in stats})

    return ReportSummary(
        total_tags=n,
        total_count=total,
        mean_count=total / n,
        median_count=median,
        max_count=max(counts),
        min_count=min(counts),
        top_tag=sorted_stats[0],
        unique_keys=unique_keys,
    )

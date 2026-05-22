"""Merge multiple TagReports into a single combined report."""
from dataclasses import dataclass
from typing import List, Dict
from tagstats.analyzer import TagStat, TagReport


@dataclass
class MergeStrategy:
    """Controls how counts are combined across reports."""
    mode: str = "sum"  # "sum" | "average" | "max"

    def combine(self, counts: List[int]) -> int:
        if not counts:
            return 0
        if self.mode == "sum":
            return sum(counts)
        if self.mode == "average":
            return round(sum(counts) / len(counts))
        if self.mode == "max":
            return max(counts)
        raise ValueError(f"Unknown merge mode: {self.mode!r}")


def merge_reports(
    reports: List[TagReport],
    strategy: MergeStrategy | None = None,
    label: str = "merged",
) -> TagReport:
    """Merge a list of TagReports into one, combining counts per (key, value).

    Args:
        reports: Non-empty list of TagReport objects to merge.
        strategy: How to combine counts. Defaults to MergeStrategy(mode="sum").
        label: Descriptive label for the resulting report.

    Returns:
        A new TagReport with combined statistics.

    Raises:
        ValueError: If reports list is empty.
    """
    if not reports:
        raise ValueError("Cannot merge an empty list of reports.")

    if strategy is None:
        strategy = MergeStrategy()

    # Accumulate counts per (key, value) key
    bucket: Dict[tuple, List[int]] = {}
    for report in reports:
        for stat in report.stats:
            key = (stat.key, stat.value)
            bucket.setdefault(key, []).append(stat.count)

    merged_stats = [
        TagStat(key=k, value=v, count=strategy.combine(counts))
        for (k, v), counts in sorted(bucket.items(), key=lambda x: -strategy.combine(x[1]))
    ]

    return TagReport(stats=merged_stats, label=label)


def filter_merged_report(report: TagReport, min_count: int = 1) -> TagReport:
    """Return a new TagReport containing only stats at or above a minimum count.

    Args:
        report: The TagReport to filter.
        min_count: Minimum count threshold (inclusive). Defaults to 1.

    Returns:
        A new TagReport with low-count entries removed, preserving the label.
    """
    if min_count < 1:
        raise ValueError(f"min_count must be at least 1, got {min_count}.")
    filtered = [stat for stat in report.stats if stat.count >= min_count]
    return TagReport(stats=filtered, label=report.label)

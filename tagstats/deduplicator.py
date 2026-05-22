"""Deduplication utilities for TagReport instances."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from tagstats.analyzer import TagReport, TagStat


@dataclass
class DeduplicateOptions:
    """Options controlling deduplication behaviour."""
    case_sensitive: bool = False
    keep: str = "first"  # "first" | "last" | "highest" | "lowest"

    def __post_init__(self) -> None:
        valid_keep = {"first", "last", "highest", "lowest"}
        if self.keep not in valid_keep:
            raise ValueError(f"keep must be one of {valid_keep}, got {self.keep!r}")


@dataclass
class DeduplicateResult:
    """Result of a deduplication pass."""
    report: TagReport
    removed: int
    original_count: int

    @property
    def kept(self) -> int:
        return self.original_count - self.removed


def _normalise_label(stat: TagStat, case_sensitive: bool) -> str:
    label = stat.tag_label
    return label if case_sensitive else label.lower()


def _pick_winner(candidates: List[TagStat], keep: str) -> TagStat:
    if keep == "first":
        return candidates[0]
    if keep == "last":
        return candidates[-1]
    if keep == "highest":
        return max(candidates, key=lambda s: s.count)
    # lowest
    return min(candidates, key=lambda s: s.count)


def deduplicate_report(
    report: TagReport,
    options: Optional[DeduplicateOptions] = None,
) -> DeduplicateResult:
    """Return a new TagReport with duplicate tag entries removed.

    Two entries are considered duplicates when their *tag_label* matches
    (optionally case-insensitively).  The *keep* option controls which
    duplicate survives.
    """
    if options is None:
        options = DeduplicateOptions()

    original_count = len(report.stats)
    seen: dict[str, List[TagStat]] = {}

    for stat in report.stats:
        key = _normalise_label(stat, options.case_sensitive)
        seen.setdefault(key, []).append(stat)

    deduped: List[TagStat] = [
        _pick_winner(group, options.keep) for group in seen.values()
    ]

    new_report = TagReport(stats=deduped)
    removed = original_count - len(deduped)
    return DeduplicateResult(report=new_report, removed=removed, original_count=original_count)

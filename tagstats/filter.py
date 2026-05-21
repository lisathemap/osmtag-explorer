"""Filtering utilities for TagReport results."""
from dataclasses import dataclass
from typing import Optional
from tagstats.analyzer import TagReport, TagStat


@dataclass
class FilterCriteria:
    min_count: Optional[int] = None
    max_count: Optional[int] = None
    key_contains: Optional[str] = None
    value_contains: Optional[str] = None

    def is_empty(self) -> bool:
        return all(v is None for v in [
            self.min_count, self.max_count,
            self.key_contains, self.value_contains
        ])


def _matches(stat: TagStat, criteria: FilterCriteria) -> bool:
    if criteria.min_count is not None and stat.count < criteria.min_count:
        return False
    if criteria.max_count is not None and stat.count > criteria.max_count:
        return False
    if criteria.key_contains is not None:
        if criteria.key_contains.lower() not in stat.key.lower():
            return False
    if criteria.value_contains is not None:
        value = stat.value or ""
        if criteria.value_contains.lower() not in value.lower():
            return False
    return True


def filter_report(report: TagReport, criteria: FilterCriteria) -> TagReport:
    """Return a new TagReport containing only stats matching the criteria."""
    if criteria.is_empty():
        return report
    filtered = [s for s in report.stats if _matches(s, criteria)]
    return TagReport(stats=filtered)

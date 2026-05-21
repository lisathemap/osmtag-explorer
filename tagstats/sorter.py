"""Sorting utilities for TagReport results."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from tagstats.analyzer import TagReport, TagStat


class SortField(str, Enum):
    COUNT = "count"
    KEY = "key"
    VALUE = "value"
    LABEL = "label"


class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"


@dataclass
class SortCriteria:
    field: SortField = SortField.COUNT
    order: SortOrder = SortOrder.DESC

    def is_descending(self) -> bool:
        return self.order == SortOrder.DESC


def _sort_key(stat: TagStat, field: SortField):
    if field == SortField.COUNT:
        return stat.count
    if field == SortField.KEY:
        return stat.key.lower()
    if field == SortField.VALUE:
        return (stat.value or "").lower()
    if field == SortField.LABEL:
        return stat.tag_label.lower()
    raise ValueError(f"Unknown sort field: {field}")


def sort_report(
    report: TagReport,
    criteria: Optional[SortCriteria] = None,
) -> TagReport:
    """Return a new TagReport with stats sorted by the given criteria."""
    if criteria is None:
        criteria = SortCriteria()

    reverse = criteria.is_descending()
    sorted_stats = sorted(
        report.stats,
        key=lambda s: _sort_key(s, criteria.field),
        reverse=reverse,
    )
    return TagReport(stats=sorted_stats)

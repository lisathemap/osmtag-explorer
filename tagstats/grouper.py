"""Group TagReport entries by key prefix or value pattern."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from tagstats.analyzer import TagReport, TagStat


@dataclass
class GroupResult:
    """Result of grouping a TagReport by key."""
    groups: Dict[str, TagReport] = field(default_factory=dict)

    def keys(self) -> List[str]:
        """Return sorted group keys."""
        return sorted(self.groups.keys())

    def get(self, key: str) -> Optional[TagReport]:
        """Return the TagReport for a group, or None."""
        return self.groups.get(key)

    def total_groups(self) -> int:
        return len(self.groups)

    def as_dict(self) -> Dict[str, List[dict]]:
        return {
            k: [
                {"key": s.key, "value": s.value, "count": s.count}
                for s in report.stats
            ]
            for k, report in self.groups.items()
        }


def group_by_key(report: TagReport) -> GroupResult:
    """Group stats by their OSM key.

    Each distinct key becomes a group containing all TagStat entries
    that share that key, regardless of value.
    """
    buckets: Dict[str, List[TagStat]] = {}
    for stat in report.stats:
        buckets.setdefault(stat.key, []).append(stat)

    groups = {
        k: TagReport(stats=v)
        for k, v in buckets.items()
    }
    return GroupResult(groups=groups)


def group_by_key_prefix(report: TagReport, separator: str = ":") -> GroupResult:
    """Group stats by the first segment of the key when split by *separator*.

    For example ``addr:city`` and ``addr:street`` both fall under ``addr``.
    Keys without the separator are placed in a group named after themselves.
    """
    buckets: Dict[str, List[TagStat]] = {}
    for stat in report.stats:
        prefix = stat.key.split(separator, 1)[0]
        buckets.setdefault(prefix, []).append(stat)

    groups = {
        k: TagReport(stats=v)
        for k, v in buckets.items()
    }
    return GroupResult(groups=groups)

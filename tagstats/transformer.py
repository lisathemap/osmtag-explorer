"""Transform TagReport entries by applying key/value remapping rules."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional

from tagstats.analyzer import TagReport, TagStat


@dataclass
class TransformRules:
    """Mapping rules applied during transformation."""
    key_aliases: Dict[str, str] = field(default_factory=dict)
    value_aliases: Dict[str, str] = field(default_factory=dict)
    drop_keys: frozenset = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        if not isinstance(self.drop_keys, frozenset):
            self.drop_keys = frozenset(self.drop_keys)


@dataclass
class TransformResult:
    """Outcome of a transformation pass."""
    report: TagReport
    remapped: int
    dropped: int

    @property
    def unchanged(self) -> int:
        return len(self.report.stats) - self.remapped

    def as_dict(self) -> dict:
        return {
            "total": len(self.report.stats),
            "remapped": self.remapped,
            "dropped": self.dropped,
            "unchanged": self.unchanged,
        }


def _remap_stat(stat: TagStat, rules: TransformRules) -> Optional[TagStat]:
    """Return a (possibly remapped) stat, or None if it should be dropped."""
    key = rules.key_aliases.get(stat.key, stat.key)
    if key in rules.drop_keys:
        return None
    value = stat.value
    if value is not None:
        value = rules.value_aliases.get(value, value)
    return TagStat(key=key, value=value, count=stat.count)


def transform_report(report: TagReport, rules: TransformRules) -> TransformResult:
    """Apply *rules* to every stat in *report* and return a TransformResult."""
    new_stats: list[TagStat] = []
    remapped = 0
    dropped = 0

    for stat in report.stats:
        result = _remap_stat(stat, rules)
        if result is None:
            dropped += 1
            continue
        changed = (result.key != stat.key) or (result.value != stat.value)
        if changed:
            remapped += 1
        new_stats.append(result)

    new_report = TagReport(stats=new_stats)
    return TransformResult(report=new_report, remapped=remapped, dropped=dropped)

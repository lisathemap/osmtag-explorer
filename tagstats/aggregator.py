"""Aggregate TagReport statistics by time buckets or custom dimensions."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from tagstats.analyzer import TagReport, TagStat


@dataclass
class AggregateOptions:
    bucket_by: str = "key"          # "key" | "value" | "prefix"
    top_n: int = 10
    min_count: int = 0

    def __post_init__(self) -> None:
        if self.bucket_by not in ("key", "value", "prefix"):
            raise ValueError(f"bucket_by must be 'key', 'value', or 'prefix', got {self.bucket_by!r}")
        if self.top_n <= 0:
            raise ValueError("top_n must be a positive integer")
        if self.min_count < 0:
            raise ValueError("min_count must be >= 0")


@dataclass
class AggregateGroup:
    bucket: str
    stats: List[TagStat]
    total: int = 0

    def __post_init__(self) -> None:
        self.total = sum(s.count for s in self.stats)

    def as_dict(self) -> dict:
        return {
            "bucket": self.bucket,
            "total": self.total,
            "count": len(self.stats),
            "stats": [{"key": s.key, "value": s.value, "count": s.count} for s in self.stats],
        }


@dataclass
class AggregateResult:
    groups: List[AggregateGroup] = field(default_factory=list)
    options: Optional[AggregateOptions] = None

    def total_groups(self) -> int:
        return len(self.groups)

    def grand_total(self) -> int:
        return sum(g.total for g in self.groups)

    def as_dict(self) -> dict:
        return {
            "total_groups": self.total_groups(),
            "grand_total": self.grand_total(),
            "groups": [g.as_dict() for g in self.groups],
        }


def _bucket_key(stat: TagStat, bucket_by: str) -> str:
    if bucket_by == "value":
        return stat.value or "(no value)"
    if bucket_by == "prefix":
        return stat.key.split(":")[0] if ":" in stat.key else stat.key
    return stat.key


def aggregate_report(report: TagReport, options: Optional[AggregateOptions] = None) -> AggregateResult:
    if options is None:
        options = AggregateOptions()

    buckets: Dict[str, List[TagStat]] = {}
    for stat in report.stats:
        if stat.count < options.min_count:
            continue
        key = _bucket_key(stat, options.bucket_by)
        buckets.setdefault(key, []).append(stat)

    groups = [
        AggregateGroup(bucket=k, stats=v)
        for k, v in buckets.items()
    ]
    groups.sort(key=lambda g: g.total, reverse=True)
    groups = groups[: options.top_n]

    return AggregateResult(groups=groups, options=options)

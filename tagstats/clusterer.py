"""Cluster TagStats by key prefix or value pattern."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from tagstats.analyzer import TagReport, TagStat


@dataclass
class ClusterOptions:
    separator: str = ":"
    max_depth: int = 1
    min_cluster_size: int = 1

    def __post_init__(self) -> None:
        if self.max_depth < 1:
            raise ValueError("max_depth must be >= 1")
        if self.min_cluster_size < 1:
            raise ValueError("min_cluster_size must be >= 1")


@dataclass
class Cluster:
    prefix: str
    stats: List[TagStat] = field(default_factory=list)

    @property
    def total_count(self) -> int:
        return sum(s.count for s in self.stats)

    @property
    def size(self) -> int:
        return len(self.stats)

    def as_dict(self) -> dict:
        return {
            "prefix": self.prefix,
            "size": self.size,
            "total_count": self.total_count,
            "stats": [{"key": s.key, "value": s.value, "count": s.count} for s in self.stats],
        }


@dataclass
class ClusterResult:
    clusters: List[Cluster]
    ungrouped: List[TagStat]

    @property
    def total_clusters(self) -> int:
        return len(self.clusters)

    def get(self, prefix: str) -> Optional[Cluster]:
        for c in self.clusters:
            if c.prefix == prefix:
                return c
        return None

    def as_dict(self) -> dict:
        return {
            "total_clusters": self.total_clusters,
            "ungrouped_count": len(self.ungrouped),
            "clusters": [c.as_dict() for c in self.clusters],
        }


def _extract_prefix(key: str, separator: str, max_depth: int) -> str:
    parts = key.split(separator)
    return separator.join(parts[:max_depth])


def cluster_report(report: TagReport, options: Optional[ClusterOptions] = None) -> ClusterResult:
    if options is None:
        options = ClusterOptions()

    buckets: Dict[str, List[TagStat]] = {}
    for stat in report.stats:
        prefix = _extract_prefix(stat.key, options.separator, options.max_depth)
        buckets.setdefault(prefix, []).append(stat)

    clusters: List[Cluster] = []
    ungrouped: List[TagStat] = []

    for prefix, stats in sorted(buckets.items()):
        if len(stats) >= options.min_cluster_size:
            clusters.append(Cluster(prefix=prefix, stats=stats))
        else:
            ungrouped.extend(stats)

    return ClusterResult(clusters=clusters, ungrouped=ungrouped)

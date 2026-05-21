"""Tag statistics analyzer for processing Overpass API results."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TagStat:
    """Represents statistics for a single OSM tag."""
    key: str
    value: Optional[str]
    count: int
    area: Optional[str] = None
    percentage: Optional[float] = None

    def __post_init__(self):
        if self.count < 0:
            raise ValueError("count must be non-negative")

    @property
    def tag_label(self) -> str:
        if self.value:
            return f"{self.key}={self.value}"
        return self.key


@dataclass
class TagReport:
    """Aggregated report for a set of tag statistics."""
    stats: list[TagStat] = field(default_factory=list)

    @property
    def total_count(self) -> int:
        return sum(s.count for s in self.stats)

    def with_percentages(self) -> "TagReport"
        total = self.total_count
        if total == 0:
            return self
        for stat in self.stats:
            stat.percentage = round((stat.count / total) * 100, 2)
        return self

    def sorted_by_count(self, descending: bool = True) -> list[TagStat]:
        return sorted(self.stats, key=lambda s: s.count, reverse=descending)

    def top(self, n: int) -> list[TagStat]:
        return self.sorted_by_count()[:n]


class TagStatsAnalyzer:
    """Processes raw Overpass results into TagReport objects."""

    def build_report(self, raw_results: list[dict], key: str, area: Optional[str] = None) -> TagReport:
        """Build a TagReport from a list of raw Overpass result dicts."""
        stats = []
        for item in raw_results:
            value = item.get("value")
            count = item.get("count", 0)
            stats.append(TagStat(key=key, value=value, count=int(count), area=area))
        report = TagReport(stats=stats)
        report.with_percentages()
        return report

    def merge_reports(self, reports: list[TagReport]) -> TagReport:
        """Merge multiple TagReports into one, summing counts for duplicate tags."""
        merged: dict[str, TagStat] = {}
        for report in reports:
            for stat in report.stats:
                label = stat.tag_label
                if label in merged:
                    merged[label].count += stat.count
                else:
                    merged[label] = TagStat(
                        key=stat.key,
                        value=stat.value,
                        count=stat.count,
                        area=stat.area,
                    )
        result = TagReport(stats=list(merged.values()))
        result.with_percentages()
        return result

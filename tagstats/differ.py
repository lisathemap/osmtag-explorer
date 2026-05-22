"""Compute differences between two TagReports."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from tagstats.analyzer import TagReport, TagStat


@dataclass
class DiffEntry:
    key: str
    value: Optional[str]
    count_a: int
    count_b: int

    @property
    def delta(self) -> int:
        return self.count_b - self.count_a

    @property
    def delta_pct(self) -> float:
        if self.count_a == 0:
            return float("inf")
        return round((self.delta / self.count_a) * 100, 2)

    @property
    def label(self) -> str:
        if self.value:
            return f"{self.key}={self.value}"
        return self.key


@dataclass
class DiffReport:
    entries: List[DiffEntry]

    @property
    def added(self) -> List[DiffEntry]:
        return [e for e in self.entries if e.count_a == 0 and e.count_b > 0]

    @property
    def removed(self) -> List[DiffEntry]:
        return [e for e in self.entries if e.count_a > 0 and e.count_b == 0]

    @property
    def changed(self) -> List[DiffEntry]:
        return [e for e in self.entries if e.count_a > 0 and e.count_b > 0 and e.delta != 0]

    @property
    def unchanged(self) -> List[DiffEntry]:
        return [e for e in self.entries if e.delta == 0]


def _index_report(report: TagReport) -> Dict[str, TagStat]:
    return {stat.tag_label: stat for stat in report.stats}


def diff_reports(report_a: TagReport, report_b: TagReport) -> DiffReport:
    """Return a DiffReport comparing report_a (baseline) to report_b."""
    index_a = _index_report(report_a)
    index_b = _index_report(report_b)
    all_labels = set(index_a) | set(index_b)

    entries: List[DiffEntry] = []
    for label in sorted(all_labels):
        stat_a = index_a.get(label)
        stat_b = index_b.get(label)
        key = (stat_a or stat_b).key  # type: ignore[union-attr]
        value = (stat_a or stat_b).value  # type: ignore[union-attr]
        entries.append(
            DiffEntry(
                key=key,
                value=value,
                count_a=stat_a.count if stat_a else 0,
                count_b=stat_b.count if stat_b else 0,
            )
        )
    return DiffReport(entries=entries)

"""Formatting utilities for tag statistics output."""

from dataclasses import dataclass
from typing import List, Optional
from tagstats.analyzer import TagReport, TagStat


DEFAULT_TOP_N = 10
BAR_WIDTH = 30


@dataclass
class FormattedRow:
    label: str
    count: int
    percentage: float
    bar: str

    def __str__(self) -> str:
        return f"{self.label:<40} {self.count:>8,}  {self.percentage:>6.2f}%  {self.bar}"


class TagReportFormatter:
    """Formats a TagReport into human-readable or structured output."""

    def __init__(self, report: TagReport, top_n: int = DEFAULT_TOP_N):
        if top_n < 1:
            raise ValueError("top_n must be at least 1")
        self.report = report
        self.top_n = top_n

    def _make_bar(self, percentage: float) -> str:
        filled = round(percentage / 100 * BAR_WIDTH)
        return "█" * filled + "░" * (BAR_WIDTH - filled)

    def _format_row(self, stat: TagStat) -> FormattedRow:
        pct = self.report.percentage(stat)
        return FormattedRow(
            label=stat.tag_label,
            count=stat.count,
            percentage=pct,
            bar=self._make_bar(pct),
        )

    def top_rows(self) -> List[FormattedRow]:
        """Return formatted rows for the top N tags by count."""
        top_stats = self.report.top_n(self.top_n)
        return [self._format_row(s) for s in top_stats]

    def summary_line(self) -> str:
        """Return a one-line summary of the report."""
        return (
            f"Total tags: {self.report.total_count:,} | "
            f"Unique tags: {len(self.report.stats)} | "
            f"Showing top {min(self.top_n, len(self.report.stats))}"
        )

    def render_text(self) -> str:
        """Render the full report as a plain-text table."""
        lines = [
            self.summary_line(),
            "-" * 80,
            f"{'Tag':<40} {'Count':>8}   {'Pct':>6}   Bar",
            "-" * 80,
        ]
        for row in self.top_rows():
            lines.append(str(row))
        lines.append("-" * 80)
        return "\n".join(lines)

    def render_csv(self, include_header: bool = True) -> str:
        """Render the top N tags as CSV."""
        lines = []
        if include_header:
            lines.append("tag,count,percentage")
        for row in self.top_rows():
            lines.append(f"{row.label},{row.count},{row.percentage:.4f}")
        return "\n".join(lines)

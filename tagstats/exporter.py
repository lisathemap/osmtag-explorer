"""Export TagReport data to various formats (CSV, JSON)."""

from __future__ import annotations

import csv
import io
import json
from dataclasses import asdict
from typing import Literal

from tagstats.analyzer import TagReport

ExportFormat = Literal["csv", "json"]


class TagReportExporter:
    """Serialises a TagReport into CSV or JSON text."""

    def __init__(self, report: TagReport) -> None:
        if not isinstance(report, TagReport):
            raise TypeError("report must be a TagReport instance")
        self._report = report

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def to_csv(self, top_n: int = 20) -> str:
        """Return CSV text for the top *top_n* tags."""
        rows = self._top_rows(top_n)
        buf = io.StringIO()
        writer = csv.DictWriter(
            buf,
            fieldnames=["tag", "count", "percentage"],
            lineterminator="\n",
        )
        writer.writeheader()
        for stat in rows:
            writer.writerow(
                {
                    "tag": stat.tag_label,
                    "count": stat.count,
                    "percentage": round(self._pct(stat.count), 4),
                }
            )
        return buf.getvalue()

    def to_json(self, top_n: int = 20) -> str:
        """Return a JSON string for the top *top_n* tags."""
        rows = self._top_rows(top_n)
        payload = {
            "key": self._report.key,
            "total": self._report.total_count,
            "entries": [
                {
                    "tag": s.tag_label,
                    "count": s.count,
                    "percentage": round(self._pct(s.count), 4),
                }
                for s in rows
            ],
        }
        return json.dumps(payload, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _top_rows(self, top_n: int):
        if top_n < 1:
            raise ValueError("top_n must be >= 1")
        sorted_stats = sorted(
            self._report.stats, key=lambda s: s.count, reverse=True
        )
        return sorted_stats[:top_n]

    def _pct(self, count: int) -> float:
        total = self._report.total_count
        if total == 0:
            return 0.0
        return count / total * 100

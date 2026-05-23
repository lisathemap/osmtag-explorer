"""Pivot a TagReport into a 2-D key × value count table."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from tagstats.analyzer import TagReport, TagStat


@dataclass
class PivotOptions:
    top_keys: int = 10
    top_values: int = 10
    fill_value: int = 0

    def __post_init__(self) -> None:
        if self.top_keys < 1:
            raise ValueError("top_keys must be >= 1")
        if self.top_values < 1:
            raise ValueError("top_values must be >= 1")


@dataclass
class PivotTable:
    keys: List[str]
    values: List[str]
    cells: Dict[str, Dict[str, int]]
    fill_value: int = 0

    def get(self, key: str, value: str) -> int:
        return self.cells.get(key, {}).get(value, self.fill_value)

    def as_dict(self) -> dict:
        return {
            "keys": self.keys,
            "values": self.values,
            "cells": {
                k: {v: self.get(k, v) for v in self.values}
                for k in self.keys
            },
        }


def pivot_report(report: TagReport, options: Optional[PivotOptions] = None) -> PivotTable:
    """Build a PivotTable from *report*.

    Rows = top keys by total count; columns = top values (across all keys)
    by total count.
    """
    if options is None:
        options = PivotOptions()

    # Aggregate counts per key and per value
    key_totals: Dict[str, int] = {}
    value_totals: Dict[str, int] = {}
    cells: Dict[str, Dict[str, int]] = {}

    for stat in report.stats:
        if stat.value is None:
            continue
        key_totals[stat.key] = key_totals.get(stat.key, 0) + stat.count
        value_totals[stat.value] = value_totals.get(stat.value, 0) + stat.count
        cells.setdefault(stat.key, {})[stat.value] = stat.count

    top_keys = [
        k for k, _ in sorted(key_totals.items(), key=lambda x: x[1], reverse=True)
    ][: options.top_keys]

    top_values = [
        v for v, _ in sorted(value_totals.items(), key=lambda x: x[1], reverse=True)
    ][: options.top_values]

    return PivotTable(
        keys=top_keys,
        values=top_values,
        cells=cells,
        fill_value=options.fill_value,
    )

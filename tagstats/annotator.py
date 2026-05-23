"""Annotate TagReport entries with human-readable notes or category labels."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from tagstats.analyzer import TagReport, TagStat

# Simple built-in category rules: key prefix -> category label
_DEFAULT_CATEGORIES: Dict[str, str] = {
    "addr": "address",
    "building": "building",
    "highway": "transport",
    "railway": "transport",
    "amenity": "amenity",
    "shop": "commerce",
    "landuse": "landuse",
    "natural": "natural",
    "name": "naming",
    "ref": "reference",
    "access": "access",
    "source": "metadata",
}


@dataclass
class AnnotatedStat:
    stat: TagStat
    category: Optional[str] = None
    note: Optional[str] = None

    @property
    def label(self) -> str:
        return self.stat.tag_label

    @property
    def count(self) -> int:
        return self.stat.count

    def as_dict(self) -> dict:
        return {
            "key": self.stat.key,
            "value": self.stat.value,
            "count": self.stat.count,
            "category": self.category,
            "note": self.note,
        }


@dataclass
class AnnotateOptions:
    categories: Dict[str, str] = field(default_factory=lambda: dict(_DEFAULT_CATEGORIES))
    default_category: Optional[str] = "other"
    include_note: bool = False


def _resolve_category(key: str, options: AnnotateOptions) -> Optional[str]:
    for prefix, category in options.categories.items():
        if key == prefix or key.startswith(prefix + ":"):
            return category
    return options.default_category


def annotate_report(
    report: TagReport,
    options: Optional[AnnotateOptions] = None,
) -> List[AnnotatedStat]:
    """Return a list of AnnotatedStat for every entry in *report*."""
    if options is None:
        options = AnnotateOptions()

    results: List[AnnotatedStat] = []
    for stat in report.stats:
        category = _resolve_category(stat.key, options)
        note: Optional[str] = None
        if options.include_note and stat.value:
            note = f"Specific value '{stat.value}' for key '{stat.key}'"
        results.append(AnnotatedStat(stat=stat, category=category, note=note))
    return results

"""Tag key/value normalization utilities for OSM tag statistics."""

from dataclasses import dataclass
from typing import Optional

from tagstats.analyzer import TagReport, TagStat


@dataclass
class NormalizeOptions:
    """Options controlling normalization behaviour."""
    lowercase_keys: bool = True
    lowercase_values: bool = False
    strip_whitespace: bool = True
    collapse_semicolons: bool = False  # treat multi-values as single tag


def normalize_key(key: str, options: Optional[NormalizeOptions] = None) -> str:
    """Return a normalized version of *key* according to *options*."""
    if options is None:
        options = NormalizeOptions()
    if options.strip_whitespace:
        key = key.strip()
    if options.lowercase_keys:
        key = key.lower()
    return key


def normalize_value(value: Optional[str], options: Optional[NormalizeOptions] = None) -> Optional[str]:
    """Return a normalized version of *value* according to *options*."""
    if value is None:
        return None
    if options is None:
        options = NormalizeOptions()
    if options.strip_whitespace:
        value = value.strip()
    if options.lowercase_values:
        value = value.lower()
    if options.collapse_semicolons:
        # Keep only the first token in a semicolon-separated list
        value = value.split(";")[0].strip()
    return value


def normalize_stat(stat: TagStat, options: Optional[NormalizeOptions] = None) -> TagStat:
    """Return a new :class:`TagStat` with normalized key and value."""
    return TagStat(
        key=normalize_key(stat.key, options),
        value=normalize_value(stat.value, options),
        count=stat.count,
    )


def normalize_report(report: TagReport, options: Optional[NormalizeOptions] = None) -> TagReport:
    """Return a new :class:`TagReport` whose stats have been normalized.

    When normalization causes two stats to share the same key/value pair their
    counts are summed.
    """
    merged: dict[tuple[str, Optional[str]], int] = {}
    for stat in report.stats:
        norm = normalize_stat(stat, options)
        bucket = (norm.key, norm.value)
        merged[bucket] = merged.get(bucket, 0) + norm.count

    normalized_stats = [
        TagStat(key=k, value=v, count=c)
        for (k, v), c in merged.items()
    ]
    return TagReport(stats=normalized_stats)

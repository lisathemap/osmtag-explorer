"""Tag suggestion and auto-completion utilities for OSM tags."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional

# Common OSM keys for suggestion purposes
_COMMON_KEYS = [
    "amenity", "building", "highway", "landuse", "leisure",
    "name", "natural", "shop", "tourism", "waterway",
    "railway", "power", "barrier", "boundary", "place",
    "surface", "access", "oneway", "maxspeed", "lanes",
]

_COMMON_VALUES: dict[str, list[str]] = {
    "amenity": ["cafe", "restaurant", "school", "hospital", "parking", "bank", "pharmacy"],
    "building": ["yes", "residential", "commercial", "industrial", "retail", "house"],
    "highway": ["residential", "primary", "secondary", "tertiary", "footway", "cycleway"],
    "landuse": ["residential", "commercial", "industrial", "forest", "farmland", "grass"],
    "natural": ["wood", "water", "scrub", "heath", "grassland", "beach"],
    "shop": ["supermarket", "clothes", "bakery", "hairdresser", "convenience"],
    "tourism": ["hotel", "attraction", "museum", "viewpoint", "camp_site"],
}


@dataclass
class TagSuggestion:
    key: str
    value: Optional[str] = None
    score: float = 1.0

    @property
    def label(self) -> str:
        if self.value:
            return f"{self.key}={self.value}"
        return self.key


def suggest_keys(prefix: str, limit: int = 10) -> List[TagSuggestion]:
    """Return key suggestions matching the given prefix."""
    prefix = prefix.strip().lower()
    matches = [k for k in _COMMON_KEYS if k.startswith(prefix)]
    matches.sort()
    return [TagSuggestion(key=k) for k in matches[:limit]]


def suggest_values(key: str, prefix: str = "", limit: int = 10) -> List[TagSuggestion]:
    """Return value suggestions for a given key, optionally filtered by prefix."""
    key = key.strip().lower()
    prefix = prefix.strip().lower()
    values = _COMMON_VALUES.get(key, [])
    if prefix:
        values = [v for v in values if v.startswith(prefix)]
    values.sort()
    return [TagSuggestion(key=key, value=v) for v in values[:limit]]


def suggest_tags(query: str, limit: int = 10) -> List[TagSuggestion]:
    """Parse 'key=value' or 'key' query and return combined suggestions."""
    query = query.strip()
    if "=" in query:
        key, _, value_prefix = query.partition("=")
        return suggest_values(key, value_prefix, limit)
    return suggest_keys(query, limit)

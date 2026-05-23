"""Random sampling utilities for TagReport objects."""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import List, Optional

from tagstats.analyzer import TagReport, TagStat


@dataclass
class SampleOptions:
    size: int = 10
    seed: Optional[int] = None
    with_replacement: bool = False

    def __post_init__(self) -> None:
        if self.size <= 0:
            raise ValueError("size must be a positive integer")


@dataclass
class SampleResult:
    items: List[TagStat]
    total_available: int
    seed_used: Optional[int]

    @property
    def returned(self) -> int:
        return len(self.items)

    @property
    def is_full_population(self) -> bool:
        return self.returned == self.total_available

    def as_dict(self) -> dict:
        return {
            "returned": self.returned,
            "total_available": self.total_available,
            "seed_used": self.seed_used,
            "is_full_population": self.is_full_population,
            "items": [
                {"key": s.key, "value": s.value, "count": s.count}
                for s in self.items
            ],
        }


def sample_report(report: TagReport, options: Optional[SampleOptions] = None) -> SampleResult:
    """Return a random sample of stats from a TagReport."""
    if options is None:
        options = SampleOptions()

    rng = random.Random(options.seed)
    population = list(report.stats)
    total = len(population)
    actual_size = min(options.size, total)

    if actual_size == 0:
        return SampleResult(items=[], total_available=total, seed_used=options.seed)

    if options.with_replacement:
        chosen = rng.choices(population, k=options.size)
    else:
        chosen = rng.sample(population, k=actual_size)

    return SampleResult(items=chosen, total_available=total, seed_used=options.seed)

"""Score TagStats by relevance based on count, key popularity, and query match."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from tagstats.analyzer import TagStat, TagReport


@dataclass
class ScoredStat:
    stat: TagStat
    score: float

    @property
    def label(self) -> str:
        return self.stat.tag_label


@dataclass
class ScoreOptions:
    query: Optional[str] = None
    count_weight: float = 1.0
    match_weight: float = 2.0
    max_count: Optional[int] = None

    def __post_init__(self) -> None:
        if self.count_weight < 0:
            raise ValueError("count_weight must be non-negative")
        if self.match_weight < 0:
            raise ValueError("match_weight must be non-negative")


def _normalize_count(count: int, max_count: int) -> float:
    if max_count == 0:
        return 0.0
    return min(count / max_count, 1.0)


def _match_score(stat: TagStat, query: Optional[str]) -> float:
    if not query:
        return 0.0
    q = query.lower()
    label = stat.tag_label.lower()
    if label == q:
        return 1.0
    if label.startswith(q):
        return 0.75
    if q in label:
        return 0.5
    return 0.0


def score_stat(stat: TagStat, options: ScoreOptions) -> ScoredStat:
    max_count = options.max_count or stat.count
    norm = _normalize_count(stat.count, max_count)
    match = _match_score(stat, options.query)
    score = (norm * options.count_weight) + (match * options.match_weight)
    return ScoredStat(stat=stat, score=round(score, 4))


def score_report(report: TagReport, options: Optional[ScoreOptions] = None) -> List[ScoredStat]:
    opts = options or ScoreOptions()
    if opts.max_count is None and report.stats:
        opts = ScoreOptions(
            query=opts.query,
            count_weight=opts.count_weight,
            match_weight=opts.match_weight,
            max_count=max(s.count for s in report.stats),
        )
    scored = [score_stat(s, opts) for s in report.stats]
    scored.sort(key=lambda x: x.score, reverse=True)
    return scored

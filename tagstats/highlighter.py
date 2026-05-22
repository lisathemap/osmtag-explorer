"""Highlight matching substrings in tag keys and values."""
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Span:
    start: int
    end: int

    def __post_init__(self) -> None:
        if self.start < 0 or self.end < self.start:
            raise ValueError(f"Invalid span: start={self.start}, end={self.end}")

    @property
    def length(self) -> int:
        return self.end - self.start


@dataclass
class HighlightResult:
    text: str
    spans: List[Span] = field(default_factory=list)

    @property
    def has_match(self) -> bool:
        return len(self.spans) > 0

    def to_html(self, tag: str = "mark") -> str:
        """Wrap matched spans in an HTML tag."""
        if not self.spans:
            return self.text
        parts: List[str] = []
        cursor = 0
        for span in sorted(self.spans, key=lambda s: s.start):
            parts.append(self.text[cursor:span.start])
            parts.append(f"<{tag}>{self.text[span.start:span.end]}</{tag}>")
            cursor = span.end
        parts.append(self.text[cursor:])
        return "".join(parts)


def highlight(text: str, query: str, case_sensitive: bool = False) -> HighlightResult:
    """Find all non-overlapping occurrences of *query* in *text*."""
    if not query:
        return HighlightResult(text=text)
    haystack = text if case_sensitive else text.lower()
    needle = query if case_sensitive else query.lower()
    spans: List[Span] = []
    start = 0
    while True:
        idx = haystack.find(needle, start)
        if idx == -1:
            break
        spans.append(Span(start=idx, end=idx + len(needle)))
        start = idx + len(needle)
    return HighlightResult(text=text, spans=spans)


def highlight_stat(key: str, value: Optional[str], query: str) -> dict:
    """Return highlight results for both key and optional value."""
    return {
        "key": highlight(key, query),
        "value": highlight(value, query) if value is not None else None,
    }

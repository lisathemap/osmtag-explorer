"""Application-level cache registry for the Flask web app."""

from tagstats.cache import TagReportCache

# Singleton cache instance shared across requests
_cache: TagReportCache | None = None


def get_cache() -> TagReportCache:
    """Return the application cache, creating it on first call."""
    global _cache
    if _cache is None:
        _cache = TagReportCache()
    return _cache


def reset_cache() -> None:
    """Reset the cache (useful for testing)."""
    global _cache
    _cache = None

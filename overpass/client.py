"""Overpass API client for querying OpenStreetMap tag usage statistics."""

import urllib.request
import urllib.parse
import urllib.error
import json
import time
from typing import Optional

OVERPASS_ENDPOINT = "https://overpass-api.de/api/interpreter"
DEFAULT_TIMEOUT = 60
DEFAULT_MAX_SIZE = 536870912  # 512 MB


class OverpassError(Exception):
    """Raised when an Overpass API request fails."""
    pass


class OverpassClient:
    """Simple synchronous client for the Overpass API."""

    def __init__(
        self,
        endpoint: str = OVERPASS_ENDPOINT,
        timeout: int = DEFAULT_TIMEOUT,
        max_size: int = DEFAULT_MAX_SIZE,
    ):
        self.endpoint = endpoint
        self.timeout = timeout
        self.max_size = max_size

    def _build_query(self, key: str, value: Optional[str] = None, area: Optional[str] = None) -> str:
        """Build an Overpass QL query to count tag usage."""
        tag_filter = f'["{key}"]' if value is None else f'["{key}"="{value}"]'
        area_filter = f'(area.searchArea)' if area else ''
        return (
            f'[out:json][timeout:{self.timeout}][maxsize:{self.max_size}];\n'
            + (f'area[name="{area}"]->.searchArea;\n' if area else '')
            + f'nwr{tag_filter}{area_filter};\n'
            f'out count;'
        )

    def query_tag_count(self, key: str, value: Optional[str] = None, area: Optional[str] = None) -> dict:
        """Query the count of elements with a given tag key (and optional value)."""
        ql = self._build_query(key, value, area)
        return self._execute(ql)

    def _execute(self, ql: str) -> dict:
        """Send an Overpass QL query and return parsed JSON response."""
        data = urllib.parse.urlencode({"data": ql}).encode()
        req = urllib.request.Request(self.endpoint, data=data, method="POST")
        req.add_header("User-Agent", "osmtag-explorer/1.0")
        try:
            start = time.monotonic()
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read().decode("utf-8")
            elapsed = round(time.monotonic() - start, 3)
            result = json.loads(raw)
            result["_elapsed"] = elapsed
            return result
        except urllib.error.HTTPError as exc:
            raise OverpassError(f"HTTP {exc.code}: {exc.reason}") from exc
        except urllib.error.URLError as exc:
            raise OverpassError(f"Request failed: {exc.reason}") from exc
        except json.JSONDecodeError as exc:
            raise OverpassError(f"Invalid JSON response: {exc}") from exc

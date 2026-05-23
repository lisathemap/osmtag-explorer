"""Flask route: annotate a tag report with category labels."""
from __future__ import annotations

from flask import Blueprint, jsonify, request

from tagstats.annotator import AnnotateOptions, annotate_report
from tagstats.validator import validate_key
from web.cache_registry import get_cache
from overpass.client import OverpassClient, OverpassError

bp = Blueprint("annotate", __name__)

_client = OverpassClient()


def _fetch_or_cached(key: str, value: str | None):
    cache = get_cache()
    cached = cache.get(key, value)
    if cached is not None:
        return cached
    report = _client.query_tag_count(key, value)
    cache.set(key, value, report)
    return report


def _parse_bool_param(param: str, default: bool = False) -> bool:
    """Parse a query string parameter as a boolean.

    Treats '1', 'true', and 'yes' (case-insensitive) as True.
    All other values (including empty string) fall back to *default*.
    """
    return param.strip().lower() in ("1", "true", "yes") if param else default


@bp.get("/api/annotate")
def annotate_tag_stats():
    """Return annotated tag stats for a given key (and optional value).

    Query params:
      - key (required)
      - value (optional)
      - default_category (optional, default 'other')
      - include_note (optional, '1' to enable)
    """
    key = request.args.get("key", "").strip()
    if not key:
        return jsonify({"error": "'key' parameter is required"}), 400

    validation = validate_key(key)
    if not validation:
        return jsonify({"error": validation.error}), 400

    value = request.args.get("value", "").strip() or None
    default_category = request.args.get("default_category", "other").strip() or "other"
    include_note = _parse_bool_param(request.args.get("include_note", ""))

    try:
        report = _fetch_or_cached(key, value)
    except OverpassError as exc:
        return jsonify({"error": str(exc)}), 502

    options = AnnotateOptions(
        default_category=default_category,
        include_note=include_note,
    )
    annotated = annotate_report(report, options=options)

    return jsonify({
        "key": key,
        "value": value,
        "default_category": default_category,
        "count": len(annotated),
        "results": [a.as_dict() for a in annotated],
    })

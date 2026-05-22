"""API route: highlight matching text in tag stats results."""
from flask import Blueprint, request, jsonify, current_app
from web.cache_registry import get_cache
from overpass.client import OverpassClient, OverpassError
from tagstats.highlighter import highlight_stat

bp = Blueprint("highlight", __name__)


def _fetch_or_cached(key: str, value: str | None, area: str | None):
    cache = get_cache()
    cached = cache.get(key, value or "", area or "")
    if cached is not None:
        return cached
    client = OverpassClient()
    try:
        report = client.query_tag_count(key, value, area)
    except OverpassError as exc:
        raise exc
    cache.set(key, value or "", area or "", report)
    return report


@bp.route("/api/highlight")
def highlight_tag_stats():
    """Return tag stats with highlight spans for a given query string.

    Query params:
      - key (required): OSM tag key
      - value (optional): OSM tag value
      - area (optional): area name filter
      - q (required): substring to highlight
    """
    key = request.args.get("key", "").strip()
    value = request.args.get("value", "").strip() or None
    area = request.args.get("area", "").strip() or None
    query = request.args.get("q", "").strip()

    if not key:
        return jsonify({"error": "'key' parameter is required"}), 400
    if not query:
        return jsonify({"error": "'q' parameter is required"}), 400

    try:
        report = _fetch_or_cached(key, value, area)
    except OverpassError as exc:
        return jsonify({"error": str(exc)}), 502

    rows = []
    for stat in report.stats:
        hl = highlight_stat(stat.key, stat.value, query)
        rows.append({
            "key": stat.key,
            "value": stat.value,
            "count": stat.count,
            "key_html": hl["key"].to_html(),
            "value_html": hl["value"].to_html() if hl["value"] is not None else None,
            "matched": hl["key"].has_match or (
                hl["value"].has_match if hl["value"] is not None else False
            ),
        })

    matched = [r for r in rows if r["matched"]]
    return jsonify({
        "query": query,
        "total": len(rows),
        "matched": len(matched),
        "results": rows,
    })

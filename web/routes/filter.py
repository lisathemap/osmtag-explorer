"""Filter route: apply FilterCriteria to a cached or freshly fetched TagReport."""
from flask import Blueprint, request, jsonify
from tagstats.filter import FilterCriteria, filter_report
from tagstats.formatter import TagReportFormatter
from tagstats.validator import validate_key, validate_value
from web.cache_registry import get_cache
from overpass.client import OverpassClient, OverpassError

filter_bp = Blueprint("filter", __name__)
_client = OverpassClient()


def _parse_int_param(name: str, default=None):
    raw = request.args.get(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return None


@filter_bp.route("/api/filter")
def filter_tag_stats():
    key = request.args.get("key", "").strip()
    value = request.args.get("value", "").strip() or None

    key_validation = validate_key(key)
    if not key_validation:
        return jsonify({"error": key_validation.error}), 400

    if value:
        val_validation = validate_value(value)
        if not val_validation:
            return jsonify({"error": val_validation.error}), 400

    criteria = FilterCriteria(
        min_count=_parse_int_param("min_count"),
        max_count=_parse_int_param("max_count"),
        key_contains=request.args.get("key_contains") or None,
        value_contains=request.args.get("value_contains") or None,
    )

    cache = get_cache()
    report = cache.get(key, value)
    if report is None:
        try:
            report = _client.query_tag_count(key, value)
        except OverpassError as exc:
            return jsonify({"error": str(exc)}), 502
        cache.set(key, value, report)

    filtered = filter_report(report, criteria)
    top_n = _parse_int_param("top_n", 10)
    formatter = TagReportFormatter(filtered, top_n=top_n)
    rows = [
        {"label": r.label, "count": r.count, "bar": r.bar}
        for r in formatter.top_rows()
    ]
    return jsonify({
        "key": key,
        "value": value,
        "total": filtered.total_count(),
        "rows": rows,
        "filtered": not criteria.is_empty(),
    })

"""Flask route: aggregate tag statistics by key, value, or key-prefix."""
from __future__ import annotations

from flask import Blueprint, jsonify, request, current_app

from overpass.client import OverpassClient, OverpassError
from tagstats.aggregator import AggregateOptions, aggregate_report
from tagstats.validator import validate_key
from web.cache_registry import get_cache

bp = Blueprint("aggregate", __name__)


def _fetch_or_cached(key: str, value: str | None):
    cache = get_cache()
    cached = cache.get(key, value)
    if cached is not None:
        return cached
    client = OverpassClient(
        url=current_app.config.get("OVERPASS_URL", "https://overpass-api.de/api/interpreter")
    )
    report = client.query_tag_count(key, value)
    cache.set(key, value, report)
    return report


def _parse_int(name: str, default: int, minimum: int = 1) -> tuple[int | None, str | None]:
    raw = request.args.get(name)
    if raw is None:
        return default, None
    try:
        val = int(raw)
    except ValueError:
        return None, f"'{name}' must be an integer"
    if val < minimum:
        return None, f"'{name}' must be >= {minimum}"
    return val, None


@bp.route("/api/aggregate")
def aggregate_tag_stats():
    key = request.args.get("key", "").strip()
    if not key:
        return jsonify({"error": "'key' parameter is required"}), 400

    validation = validate_key(key)
    if not validation:
        return jsonify({"error": validation.error}), 400

    value = request.args.get("value") or None
    bucket_by = request.args.get("bucket_by", "key")
    if bucket_by not in ("key", "value", "prefix"):
        return jsonify({"error": "'bucket_by' must be 'key', 'value', or 'prefix'"}), 400

    top_n, err = _parse_int("top_n", default=10)
    if err:
        return jsonify({"error": err}), 400

    min_count, err = _parse_int("min_count", default=0, minimum=0)
    if err:
        return jsonify({"error": err}), 400

    try:
        report = _fetch_or_cached(key, value)
    except OverpassError as exc:
        return jsonify({"error": str(exc)}), 502

    try:
        options = AggregateOptions(bucket_by=bucket_by, top_n=top_n, min_count=min_count)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    result = aggregate_report(report, options)
    return jsonify(result.as_dict())

"""Flask route: pivot a tag report into a 2-D table."""
from __future__ import annotations

from flask import Blueprint, jsonify, request

from overpass.client import OverpassClient, OverpassError
from tagstats.pivotter import PivotOptions, pivot_report
from tagstats.validator import validate_key
from web.cache_registry import get_cache

bp = Blueprint("pivot", __name__)


def _fetch_or_cached(key: str, area: str | None):
    cache = get_cache()
    cached = cache.get(key, area)
    if cached is not None:
        return cached
    client = OverpassClient()
    report = client.query_tag_count(key, area=area)
    cache.set(key, area, report)
    return report


def _parse_int(name: str, default: int, minimum: int = 1) -> tuple[int, str | None]:
    raw = request.args.get(name)
    if raw is None:
        return default, None
    try:
        value = int(raw)
    except ValueError:
        return default, f"'{name}' must be an integer"
    if value < minimum:
        return default, f"'{name}' must be >= {minimum}"
    return value, None


@bp.get("/api/pivot")
def pivot_tag_stats():
    key = request.args.get("key", "").strip()
    if not key:
        return jsonify({"error": "'key' parameter is required"}), 400

    validation = validate_key(key)
    if not validation:
        return jsonify({"error": validation.error}), 400

    area = request.args.get("area") or None

    top_keys, err = _parse_int("top_keys", default=10)
    if err:
        return jsonify({"error": err}), 400

    top_values, err = _parse_int("top_values", default=10)
    if err:
        return jsonify({"error": err}), 400

    try:
        report = _fetch_or_cached(key, area)
    except OverpassError as exc:
        return jsonify({"error": str(exc)}), 502

    options = PivotOptions(top_keys=top_keys, top_values=top_values)
    table = pivot_report(report, options)

    return jsonify({
        "key": key,
        "area": area,
        "top_keys": top_keys,
        "top_values": top_values,
        "pivot": table.as_dict(),
    })

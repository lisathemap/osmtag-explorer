"""HTTP route: flatten a tag report to a list of dicts."""
from __future__ import annotations

from flask import Blueprint, jsonify, request, current_app

from overpass.client import OverpassClient, OverpassError
from tagstats.flattener import FlattenOptions, flatten_report
from web.cache_registry import get_cache

bp = Blueprint("flatten", __name__)


def _fetch_or_cached(key: str, value: str | None, area: str | None):
    cache = get_cache()
    cached = cache.get(key, value, area)
    if cached is not None:
        return cached
    client: OverpassClient = current_app.config["OVERPASS_CLIENT"]
    report = client.query_tag_count(key, value, area)
    cache.set(key, value, area, report)
    return report


@bp.route("/api/flatten")
def flatten_tag_stats():
    key = request.args.get("key", "").strip()
    if not key:
        return jsonify({"error": "'key' parameter is required"}), 400

    value = request.args.get("value") or None
    area = request.args.get("area") or None

    # Optional query params
    include_rank = request.args.get("rank", "false").lower() == "true"
    top_n_raw = request.args.get("top_n")
    top_n: int | None = None
    if top_n_raw is not None:
        try:
            top_n = int(top_n_raw)
            if top_n < 1:
                raise ValueError
        except ValueError:
            return jsonify({"error": "'top_n' must be a positive integer"}), 400

    try:
        report = _fetch_or_cached(key, value, area)
    except OverpassError as exc:
        return jsonify({"error": str(exc)}), 502

    opts = FlattenOptions(include_rank=include_rank, top_n=top_n)
    rows = flatten_report(report, opts)

    return jsonify({
        "key": key,
        "value": value,
        "area": area,
        "count": len(rows),
        "rows": rows,
    })

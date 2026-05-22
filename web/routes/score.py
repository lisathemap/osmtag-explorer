"""Route: score tag stats by relevance."""
from __future__ import annotations

from flask import Blueprint, request, jsonify, current_app

from tagstats.scorer import ScoreOptions, score_report
from tagstats.validator import validate_key
from web.cache_registry import get_cache
from overpass.client import OverpassClient, OverpassError

bp = Blueprint("score", __name__)


def _fetch_or_cached(key: str, value: str | None, area: str | None):
    cache = get_cache()
    cached = cache.get(key, value)
    if cached is not None:
        return cached
    client = OverpassClient()
    report = client.query_tag_count(key, value, area)
    cache.set(key, value, report)
    return report


@bp.route("/api/score", methods=["GET"])
def score_tag_stats():
    key = request.args.get("key", "").strip()
    value = request.args.get("value", "").strip() or None
    area = request.args.get("area", "").strip() or None
    query = request.args.get("q", "").strip() or None

    if not key:
        return jsonify({"error": "'key' parameter is required"}), 400

    key_result = validate_key(key)
    if not key_result:
        return jsonify({"error": key_result.error}), 400

    try:
        count_w = float(request.args.get("count_weight", 1.0))
        match_w = float(request.args.get("match_weight", 2.0))
    except ValueError:
        return jsonify({"error": "weights must be numeric"}), 400

    try:
        opts = ScoreOptions(query=query, count_weight=count_w, match_weight=match_w)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    try:
        report = _fetch_or_cached(key, value, area)
    except OverpassError as exc:
        return jsonify({"error": str(exc)}), 502

    scored = score_report(report, opts)

    return jsonify({
        "key": key,
        "value": value,
        "query": query,
        "count": len(scored),
        "results": [
            {"label": s.label, "score": s.score, "count": s.stat.count}
            for s in scored
        ],
    })

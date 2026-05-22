"""Route: GET /api/summarize — return aggregate summary of a tag report."""
from __future__ import annotations

from flask import Blueprint, jsonify, request

from overpass.client import OverpassClient, OverpassError
from tagstats.analyzer import build_report
from tagstats.summarizer import summarize_report
from tagstats.validator import validate_key, validate_value
from web.cache_registry import get_cache

bp = Blueprint("summarize", __name__)


def _fetch_or_cached(key: str, value: str | None, area: str | None):
    cache = get_cache()
    cached = cache.get(key, value)
    if cached is not None:
        return cached
    client = OverpassClient()
    raw = client.query_tag_count(key, value=value, area=area)
    report = build_report(key, raw)
    cache.set(key, value, report)
    return report


@bp.route("/api/summarize", methods=["GET"])
def summarize_tag_stats():
    key = request.args.get("key", "").strip()
    value = request.args.get("value", "").strip() or None
    area = request.args.get("area", "").strip() or None

    key_result = validate_key(key)
    if not key_result:
        return jsonify({"error": key_result.error}), 400

    if value is not None:
        val_result = validate_value(value)
        if not val_result:
            return jsonify({"error": val_result.error}), 400

    try:
        report = _fetch_or_cached(key, value, area)
    except OverpassError as exc:
        return jsonify({"error": str(exc)}), 502

    summary = summarize_report(report)
    return jsonify(summary.as_dict()), 200

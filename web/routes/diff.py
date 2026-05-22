"""Web route for diffing two tag report snapshots."""
from __future__ import annotations

from flask import Blueprint, jsonify, request

from overpass.client import OverpassClient, OverpassError
from tagstats.analyzer import TagReport
from tagstats.differ import DiffEntry, diff_reports
from tagstats.validator import validate_key
from web.cache_registry import get_cache

diff_bp = Blueprint("diff", __name__)


def _fetch_or_cached(key: str, value: str | None, area: str | None) -> TagReport:
    cache = get_cache()
    cached = cache.get(key, value, area)
    if cached is not None:
        return cached
    client = OverpassClient()
    report = client.query_tag_count(key, value, area)
    cache.set(key, value, area, report)
    return report


def _entry_to_dict(e: DiffEntry) -> dict:
    return {
        "label": e.label,
        "key": e.key,
        "value": e.value,
        "count_a": e.count_a,
        "count_b": e.count_b,
        "delta": e.delta,
        "delta_pct": None if e.delta_pct == float("inf") else e.delta_pct,
    }


@diff_bp.route("/api/diff")
def diff_tag_stats():
    """Compare two OSM tags.

    Query params:
      - tag_a: key or key=value  (required)
      - tag_b: key or key=value  (required)
      - area:  optional area name
    """
    tag_a_raw = request.args.get("tag_a", "").strip()
    tag_b_raw = request.args.get("tag_b", "").strip()
    area = request.args.get("area") or None

    if not tag_a_raw or not tag_b_raw:
        return jsonify({"error": "Both tag_a and tag_b are required"}), 400

    def _parse(raw: str):
        if "=" in raw:
            k, v = raw.split("=", 1)
            return k.strip(), v.strip() or None
        return raw, None

    key_a, val_a = _parse(tag_a_raw)
    key_b, val_b = _parse(tag_b_raw)

    for key in (key_a, key_b):
        result = validate_key(key)
        if not result:
            return jsonify({"error": result.error}), 400

    try:
        report_a = _fetch_or_cached(key_a, val_a, area)
        report_b = _fetch_or_cached(key_b, val_b, area)
    except OverpassError as exc:
        return jsonify({"error": str(exc)}), 502

    dr = diff_reports(report_a, report_b)
    return jsonify({
        "added": [_entry_to_dict(e) for e in dr.added],
        "removed": [_entry_to_dict(e) for e in dr.removed],
        "changed": [_entry_to_dict(e) for e in dr.changed],
        "unchanged": [_entry_to_dict(e) for e in dr.unchanged],
    })

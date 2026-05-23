"""Flask route for random-sampling a TagReport via the Overpass API."""
from __future__ import annotations

from flask import Blueprint, jsonify, request

from tagstats.sampler import SampleOptions, sample_report
from tagstats.validator import validate_key
from web.cache_registry import get_cache
from overpass.client import OverpassClient, OverpassError
from tagstats.analyzer import TagReport

bp = Blueprint("sample", __name__)


def _fetch_or_cached(key: str, value: str | None, area: str | None) -> TagReport:
    cache = get_cache()
    cached = cache.get(key, value or "", area or "")
    if cached is not None:
        return cached
    client = OverpassClient()
    report = client.query_tag_count(key, value, area)
    cache.set(key, value or "", area or "", report)
    return report


@bp.route("/api/sample")
def sample_tag_stats():
    key = request.args.get("key", "").strip()
    if not key:
        return jsonify({"error": "'key' parameter is required"}), 400

    validation = validate_key(key)
    if not validation:
        return jsonify({"error": validation.error}), 400

    value = request.args.get("value") or None
    area = request.args.get("area") or None

    raw_size = request.args.get("size", "10")
    try:
        size = int(raw_size)
        if size <= 0:
            raise ValueError
    except ValueError:
        return jsonify({"error": "'size' must be a positive integer"}), 400

    raw_seed = request.args.get("seed")
    seed = None
    if raw_seed is not None:
        try:
            seed = int(raw_seed)
        except ValueError:
            return jsonify({"error": "'seed' must be an integer"}), 400

    with_replacement = request.args.get("with_replacement", "false").lower() == "true"

    try:
        report = _fetch_or_cached(key, value, area)
    except OverpassError as exc:
        return jsonify({"error": str(exc)}), 502

    opts = SampleOptions(size=size, seed=seed, with_replacement=with_replacement)
    result = sample_report(report, opts)
    return jsonify(result.as_dict()), 200

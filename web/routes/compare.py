from flask import Blueprint, jsonify, request
from tagstats.analyzer import TagReport, TagStat
from overpass.client import OverpassClient, OverpassError
from web.cache_registry import get_cache

compare_bp = Blueprint("compare", __name__)

_client = OverpassClient()


def _fetch_or_cached(key: str, value: str | None, area: str | None) -> TagReport:
    cache = get_cache()
    cached = cache.get(key, value, area)
    if cached is not None:
        return cached

    raw = _client.query_tag_count(key, value=value, area=area)
    stats = [
        TagStat(key=entry["key"], value=entry.get("value"), count=entry["count"])
        for entry in raw
    ]
    report = TagReport(stats=stats)
    cache.set(key, value, area, report)
    return report


@compare_bp.route("/api/compare", methods=["GET"])
def compare_tags():
    """Compare usage counts for up to 5 tag key[=value] pairs.

    Query params:
        tags  – comma-separated list of 'key' or 'key=value' strings (2-5)
        area  – optional area name filter passed to Overpass
    """
    raw_tags = request.args.get("tags", "")
    area = request.args.get("area") or None

    if not raw_tags:
        return jsonify({"error": "'tags' query parameter is required"}), 400

    tag_specs = [t.strip() for t in raw_tags.split(",") if t.strip()]

    if len(tag_specs) < 2:
        return jsonify({"error": "At least 2 tags are required for comparison"}), 400

    if len(tag_specs) > 5:
        return jsonify({"error": "At most 5 tags can be compared at once"}), 400

    results = []
    try:
        for spec in tag_specs:
            if "=" in spec:
                key, value = spec.split("=", 1)
            else:
                key, value = spec, None

            report = _fetch_or_cached(key, value, area)
            results.append(
                {
                    "tag": spec,
                    "total": report.total_count,
                    "top": [
                        {"key": s.key, "value": s.value, "count": s.count}
                        for s in sorted(report.stats, key=lambda x: x.count, reverse=True)[:5]
                    ],
                }
            )
    except OverpassError as exc:
        return jsonify({"error": str(exc)}), 502

    return jsonify({"area": area, "comparisons": results})

"""Route for merging tag statistics from multiple keys/values."""
from flask import Blueprint, request, jsonify
from overpass.client import OverpassClient, OverpassError
from tagstats.analyzer import TagReport
from tagstats.merger import MergeStrategy, merge_reports
from tagstats.validator import validate_tag
from web.cache_registry import get_cache

merge_bp = Blueprint("merge", __name__)


def _fetch_or_cached(client: OverpassClient, key: str, value: str | None) -> TagReport:
    cache = get_cache()
    cached = cache.get(key, value)
    if cached is not None:
        return cached
    report = client.query_tag_count(key, value)
    cache.set(key, value, report)
    return report


@merge_bp.route("/api/merge", methods=["GET"])
def merge_tag_stats():
    """Merge statistics for multiple tags.

    Query params:
        tags  (required, repeatable): e.g. ?tags=amenity=cafe&tags=shop=bakery
        mode  (optional): sum | average | max  (default: sum)
    """
    raw_tags = request.args.getlist("tags")
    if not raw_tags:
        return jsonify({"error": "At least one 'tags' parameter is required."}), 400

    mode = request.args.get("mode", "sum")
    if mode not in ("sum", "average", "max"):
        return jsonify({"error": f"Invalid mode {mode!r}. Choose sum, average, or max."}), 400

    # Parse and validate each tag
    parsed = []
    for raw in raw_tags:
        if "=" in raw:
            key, _, value = raw.partition("=")
            value = value or None
        else:
            key, value = raw, None

        result = validate_tag(key, value)
        if not result:
            return jsonify({"error": f"Invalid tag {raw!r}: {result.error}"}), 400
        parsed.append((key, value))

    client = OverpassClient()
    reports = []
    try:
        for key, value in parsed:
            reports.append(_fetch_or_cached(client, key, value))
    except OverpassError as exc:
        return jsonify({"error": str(exc)}), 502

    strategy = MergeStrategy(mode=mode)
    label = "+".join(raw_tags)
    merged = merge_reports(reports, strategy=strategy, label=label)

    return jsonify({
        "label": merged.label,
        "mode": mode,
        "total": merged.total_count,
        "stats": [
            {"key": s.key, "value": s.value, "count": s.count}
            for s in merged.stats
        ],
    })

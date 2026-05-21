from flask import Blueprint, jsonify, request, current_app
from web.cache_registry import get_cache
from tagstats.paginator import paginate, DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from tagstats.validator import validate_key
from overpass.client import OverpassClient, OverpassError
from tagstats.analyzer import TagReport

paginate_bp = Blueprint("paginate", __name__)


def _parse_int(value, default: int, min_val: int, max_val: int) -> int:
    try:
        v = int(value)
    except (TypeError, ValueError):
        return default
    return max(min_val, min(max_val, v))


@paginate_bp.route("/api/stats/page")
def paginated_tag_stats():
    key = request.args.get("key", "").strip()
    value = request.args.get("value", "").strip() or None

    validation = validate_key(key)
    if not validation:
        return jsonify({"error": validation.error}), 400

    page = _parse_int(request.args.get("page"), default=1, min_val=1, max_val=10_000)
    page_size = _parse_int(
        request.args.get("page_size"),
        default=DEFAULT_PAGE_SIZE,
        min_val=1,
        max_val=MAX_PAGE_SIZE,
    )

    cache = get_cache()
    report = cache.get(key, value)

    if report is None:
        try:
            client = OverpassClient()
            raw = client.query_tag_count(key, value)
            report = TagReport.from_overpass(key, value, raw)
            cache.set(key, value, report)
        except OverpassError as exc:
            current_app.logger.error("Overpass error: %s", exc)
            return jsonify({"error": str(exc)}), 502

    result = paginate(report.stats, page=page, page_size=page_size)

    return jsonify({
        "page": result.page,
        "page_size": result.page_size,
        "total": result.total,
        "total_pages": result.total_pages,
        "has_next": result.has_next,
        "has_prev": result.has_prev,
        "items": [
            {"key": s.key, "value": s.value, "count": s.count}
            for s in result.items
        ],
    })

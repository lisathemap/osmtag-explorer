"""Flask blueprint exposing /api/export for CSV and JSON downloads."""

from __future__ import annotations

from flask import Blueprint, Response, abort, request

from tagstats.exporter import TagReportExporter
from web.cache_registry import get_cache

export_bp = Blueprint("export", __name__)

_ALLOWED_FORMATS = {"csv", "json"}
_MIME = {
    "csv": "text/csv",
    "json": "application/json",
}


def _build_filename(key: str, value: str | None, fmt: str) -> str:
    """Build a safe download filename from the tag key, optional value, and format.

    Examples::

        _build_filename("amenity", None, "csv")      -> "amenity.csv"
        _build_filename("amenity", "cafe", "json")   -> "amenity_cafe.json"
    """
    stem = f"{key}_{value}" if value else key
    # Replace characters that are unsafe in filenames
    stem = stem.replace("/", "_").replace("\\", "_").replace(" ", "_")
    return f"{stem}.{fmt}"


@export_bp.route("/api/export")
def export_tag_stats() -> Response:
    """Export cached tag statistics.

    Query params:
      - key   (required) OSM key, e.g. ``amenity``
      - value (optional) OSM value filter
      - fmt   (optional) ``csv`` | ``json``  (default: ``json``)
      - top   (optional) integer, default 20
    """
    key = request.args.get("key", "").strip()
    if not key:
        abort(400, description="'key' query parameter is required")

    value = request.args.get("value", "").strip() or None
    fmt = request.args.get("fmt", "json").strip().lower()
    if fmt not in _ALLOWED_FORMATS:
        abort(400, description=f"'fmt' must be one of {sorted(_ALLOWED_FORMATS)}")

    try:
        top_n = int(request.args.get("top", 20))
        if top_n < 1:
            raise ValueError
    except ValueError:
        abort(400, description="'top' must be a positive integer")

    cache = get_cache()
    report = cache.get(key, value)
    if report is None:
        abort(
            404,
            description="No cached data for this tag. Fetch stats first via /api/stats.",
        )

    exporter = TagReportExporter(report)
    if fmt == "csv":
        body = exporter.to_csv(top_n=top_n)
    else:
        body = exporter.to_json(top_n=top_n)

    filename = _build_filename(key, value, fmt)

    return Response(
        body,
        mimetype=_MIME[fmt],
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

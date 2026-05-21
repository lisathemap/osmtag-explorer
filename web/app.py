"""Flask web application for osmtag-explorer."""

from flask import Flask, jsonify, render_template, request

from overpass.client import OverpassClient, OverpassError
from tagstats.analyzer import TagReport, TagStat
from tagstats.formatter import TagReportFormatter
from web.cache_registry import get_cache

app = Flask(__name__)
_overpass = OverpassClient()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/stats")
def tag_stats():
    key = request.args.get("key", "").strip()
    value = request.args.get("value", "").strip() or None
    area = request.args.get("area", "").strip() or None
    top_n = int(request.args.get("top_n", 10))

    if not key:
        return jsonify({"error": "'key' parameter is required"}), 400

    cache = get_cache()
    cached = cache.get(key, value=value, area=area)
    if cached is not None:
        report = cached
        from_cache = True
    else:
        try:
            raw = _overpass.query_tag_count(key, value=value, area=area)
        except OverpassError as exc:
            return jsonify({"error": str(exc)}), 502

        stats = [
            TagStat(key=key, value=v, count=c)
            for v, c in raw.items()
        ]
        report = TagReport(key=key, value=value, stats=stats)
        cache.set(report, key=key, value=value, area=area)
        from_cache = False

    formatter = TagReportFormatter(report, top_n=top_n)
    rows = [
        {"label": r.label, "count": r.count, "bar": r.bar, "pct": r.pct}
        for r in formatter.top_rows()
    ]
    return jsonify({
        "key": key,
        "value": value,
        "area": area,
        "total": report.total_count(),
        "rows": rows,
        "from_cache": from_cache,
    })


@app.route("/api/cache/stats")
def cache_stats():
    cache = get_cache()
    purged = cache.purge_expired()
    return jsonify({"size": cache.size(), "purged_expired": purged})


if __name__ == "__main__":
    app.run(debug=True)

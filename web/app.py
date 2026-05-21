"""Flask web application for OSM Tag Explorer."""

from flask import Flask, render_template, request, jsonify
from overpass.client import OverpassClient, OverpassError
from tagstats.analyzer import TagReport, TagStat
from tagstats.formatter import TagReportFormatter

app = Flask(__name__)
client = OverpassClient()


@app.route("/")
def index():
    """Render the main explorer page."""
    return render_template("index.html")


@app.route("/api/stats")
def tag_stats():
    """Return tag usage statistics as JSON.

    Query params:
        key (str): OSM tag key (required)
        value (str): OSM tag value (optional)
        area (str): Area name to restrict search (optional)
        top_n (int): Number of top results to return (default 10)
    """
    key = request.args.get("key", "").strip()
    value = request.args.get("value", "").strip() or None
    area = request.args.get("area", "").strip() or None
    top_n = int(request.args.get("top_n", 10))

    if not key:
        return jsonify({"error": "'key' parameter is required"}), 400

    try:
        raw = client.query_tag_count(key=key, value=value, area=area)
        stats = [
            TagStat(key=item["key"], value=item.get("value"), count=item["count"])
            for item in raw
        ]
        report = TagReport(stats=stats)
        formatter = TagReportFormatter(report, top_n=top_n)
        rows = formatter.top_rows()
        return jsonify({
            "key": key,
            "value": value,
            "area": area,
            "total": report.total_count,
            "results": [
                {"label": r.label, "count": r.count, "percent": r.percent}
                for r in rows
            ],
        })
    except OverpassError as exc:
        return jsonify({"error": str(exc)}), 502
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


if __name__ == "__main__":
    app.run(debug=True)

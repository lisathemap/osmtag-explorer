"""Flask route for tag suggestion / autocomplete endpoint."""
from flask import Blueprint, jsonify, request
from tagstats.tagger import suggest_tags, suggest_keys, suggest_values
from tagstats.validator import validate_key

suggest_bp = Blueprint("suggest", __name__)


@suggest_bp.route("/api/suggest", methods=["GET"])
def suggest_tag_completions():
    """Return tag suggestions for a given query string.

    Query params:
      - q: free-form query, e.g. 'amen' or 'amenity=ca'
      - key: restrict to value suggestions for this key
      - limit: max results (default 10, max 50)
    """
    q = request.args.get("q", "").strip()
    key = request.args.get("key", "").strip()
    try:
        limit = min(int(request.args.get("limit", 10)), 50)
    except (ValueError, TypeError):
        limit = 10

    if key:
        validation = validate_key(key)
        if not validation:
            return jsonify({"error": validation.error}), 400
        results = suggest_values(key, prefix=q, limit=limit)
    else:
        results = suggest_tags(q, limit=limit)

    payload = [
        {"label": s.label, "key": s.key, "value": s.value, "score": s.score}
        for s in results
    ]
    return jsonify({"suggestions": payload, "count": len(payload)})

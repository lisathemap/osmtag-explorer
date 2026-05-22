"""Tests for the /api/suggest route."""
import pytest
from unittest.mock import patch
from web.app import app


class TestSuggestRoute:
    def setup_method(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_suggest_returns_200(self):
        resp = self.client.get("/api/suggest?q=amen")
        assert resp.status_code == 200

    def test_suggest_json_has_suggestions_key(self):
        resp = self.client.get("/api/suggest?q=amen")
        data = resp.get_json()
        assert "suggestions" in data

    def test_suggest_json_has_count_key(self):
        resp = self.client.get("/api/suggest?q=amen")
        data = resp.get_json()
        assert "count" in data

    def test_suggest_amenity_in_results(self):
        resp = self.client.get("/api/suggest?q=amen")
        data = resp.get_json()
        labels = [s["label"] for s in data["suggestions"]]
        assert "amenity" in labels

    def test_suggest_with_key_returns_values(self):
        resp = self.client.get("/api/suggest?key=amenity&q=ca")
        data = resp.get_json()
        assert resp.status_code == 200
        for s in data["suggestions"]:
            assert s["key"] == "amenity"
            assert s["value"] is not None

    def test_suggest_invalid_key_returns_400(self):
        resp = self.client.get("/api/suggest?key=INVALID KEY!")
        assert resp.status_code == 400
        data = resp.get_json()
        assert "error" in data

    def test_limit_param_respected(self):
        resp = self.client.get("/api/suggest?q=&limit=3")
        data = resp.get_json()
        assert data["count"] <= 3

    def test_limit_capped_at_50(self):
        resp = self.client.get("/api/suggest?q=&limit=999")
        data = resp.get_json()
        assert data["count"] <= 50

    def test_invalid_limit_uses_default(self):
        resp = self.client.get("/api/suggest?q=a&limit=abc")
        assert resp.status_code == 200

    def test_empty_query_returns_keys(self):
        resp = self.client.get("/api/suggest")
        data = resp.get_json()
        assert data["count"] > 0
        for s in data["suggestions"]:
            assert s["value"] is None

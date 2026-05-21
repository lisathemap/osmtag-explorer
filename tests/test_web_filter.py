"""Tests for the /api/filter route."""
import pytest
from unittest.mock import patch, MagicMock
from web.app import app
from web.cache_registry import reset_cache
from tagstats.analyzer import TagStat, TagReport


def _make_report():
    return TagReport(stats=[
        TagStat(key="amenity", value="cafe", count=200),
        TagStat(key="amenity", value="pub", count=80),
        TagStat(key="amenity", value="restaurant", count=450),
    ])


class TestFilterRoute:
    def setup_method(self):
        app.config["TESTING"] = True
        self.client = app.test_client()
        reset_cache()

    def test_missing_key_returns_400(self):
        resp = self.client.get("/api/filter")
        assert resp.status_code == 400

    def test_invalid_key_returns_400(self):
        resp = self.client.get("/api/filter?key=!!bad")
        assert resp.status_code == 400

    @patch("web.routes.filter._client")
    def test_success_returns_200(self, mock_client):
        mock_client.query_tag_count.return_value = _make_report()
        resp = self.client.get("/api/filter?key=amenity")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "rows" in data
        assert data["key"] == "amenity"

    @patch("web.routes.filter._client")
    def test_min_count_filter_applied(self, mock_client):
        mock_client.query_tag_count.return_value = _make_report()
        resp = self.client.get("/api/filter?key=amenity&min_count=200")
        assert resp.status_code == 200
        data = resp.get_json()
        assert all(r["count"] >= 200 for r in data["rows"])

    @patch("web.routes.filter._client")
    def test_filtered_flag_true_with_criteria(self, mock_client):
        mock_client.query_tag_count.return_value = _make_report()
        resp = self.client.get("/api/filter?key=amenity&min_count=100")
        data = resp.get_json()
        assert data["filtered"] is True

    @patch("web.routes.filter._client")
    def test_filtered_flag_false_without_criteria(self, mock_client):
        mock_client.query_tag_count.return_value = _make_report()
        resp = self.client.get("/api/filter?key=amenity")
        data = resp.get_json()
        assert data["filtered"] is False

    @patch("web.routes.filter._client")
    def test_overpass_error_returns_502(self, mock_client):
        from overpass.client import OverpassError
        mock_client.query_tag_count.side_effect = OverpassError("timeout")
        resp = self.client.get("/api/filter?key=amenity")
        assert resp.status_code == 502

    @patch("web.routes.filter._client")
    def test_cache_used_on_second_request(self, mock_client):
        mock_client.query_tag_count.return_value = _make_report()
        self.client.get("/api/filter?key=amenity")
        self.client.get("/api/filter?key=amenity")
        assert mock_client.query_tag_count.call_count == 1

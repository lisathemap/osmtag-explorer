"""Tests for the Flask web application routes."""

import json
import unittest
from unittest.mock import MagicMock, patch

from web.app import app
from web.cache_registry import reset_cache
from tagstats.analyzer import TagReport, TagStat
from overpass.client import OverpassError


def _make_report(key="amenity"):
    stats = [
        TagStat(key=key, value="cafe", count=50),
        TagStat(key=key, value="restaurant", count=150),
    ]
    return TagReport(key=key, stats=stats)


class TestWebAppRoutes(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()
        reset_cache()

    def test_index_returns_200(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)

    @patch("web.app._overpass")
    def test_api_stats_success(self, mock_overpass):
        mock_overpass.query_tag_count.return_value = {"cafe": 50, "restaurant": 150}
        resp = self.client.get("/api/stats?key=amenity")
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertEqual(data["key"], "amenity")
        self.assertEqual(data["total"], 200)
        self.assertFalse(data["from_cache"])
        self.assertIsInstance(data["rows"], list)

    def test_api_stats_missing_key(self):
        resp = self.client.get("/api/stats")
        self.assertEqual(resp.status_code, 400)
        data = json.loads(resp.data)
        self.assertIn("error", data)

    @patch("web.app._overpass")
    def test_api_stats_overpass_error(self, mock_overpass):
        mock_overpass.query_tag_count.side_effect = OverpassError("timeout")
        resp = self.client.get("/api/stats?key=amenity")
        self.assertEqual(resp.status_code, 502)
        data = json.loads(resp.data)
        self.assertIn("error", data)

    @patch("web.app._overpass")
    def test_api_stats_served_from_cache(self, mock_overpass):
        mock_overpass.query_tag_count.return_value = {"cafe": 10}
        self.client.get("/api/stats?key=amenity")
        resp = self.client.get("/api/stats?key=amenity")
        data = json.loads(resp.data)
        self.assertTrue(data["from_cache"])
        mock_overpass.query_tag_count.assert_called_once()

    @patch("web.app._overpass")
    def test_api_stats_top_n_respected(self, mock_overpass):
        mock_overpass.query_tag_count.return_value = {
            f"v{i}": i * 10 for i in range(1, 20)
        }
        resp = self.client.get("/api/stats?key=amenity&top_n=5")
        data = json.loads(resp.data)
        self.assertLessEqual(len(data["rows"]), 5)

    def test_cache_stats_endpoint(self):
        resp = self.client.get("/api/cache/stats")
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertIn("size", data)
        self.assertIn("purged_expired", data)

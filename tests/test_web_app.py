"""Tests for the Flask web application routes."""

import json
import unittest
from unittest.mock import patch, MagicMock

from web.app import app
from overpass.client import OverpassError


RAW_STATS = [
    {"key": "amenity", "value": "cafe", "count": 500},
    {"key": "amenity", "value": "restaurant", "count": 300},
    {"key": "amenity", "value": "bar", "count": 200},
]


class TestWebAppRoutes(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_index_returns_200(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"OSM Tag Explorer", resp.data)

    @patch("web.app.client")
    def test_api_stats_success(self, mock_client):
        mock_client.query_tag_count.return_value = RAW_STATS
        resp = self.client.get("/api/stats?key=amenity")
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertEqual(data["key"], "amenity")
        self.assertEqual(data["total"], 1000)
        self.assertEqual(len(data["results"]), 3)

    def test_api_stats_missing_key(self):
        resp = self.client.get("/api/stats")
        self.assertEqual(resp.status_code, 400)
        data = json.loads(resp.data)
        self.assertIn("error", data)

    @patch("web.app.client")
    def test_api_stats_overpass_error(self, mock_client):
        mock_client.query_tag_count.side_effect = OverpassError("timeout")
        resp = self.client.get("/api/stats?key=amenity")
        self.assertEqual(resp.status_code, 502)
        data = json.loads(resp.data)
        self.assertIn("error", data)

    @patch("web.app.client")
    def test_api_stats_top_n_respected(self, mock_client):
        mock_client.query_tag_count.return_value = RAW_STATS
        resp = self.client.get("/api/stats?key=amenity&top_n=2")
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertLessEqual(len(data["results"]), 2)

    @patch("web.app.client")
    def test_api_stats_results_sorted_descending(self, mock_client):
        mock_client.query_tag_count.return_value = RAW_STATS
        resp = self.client.get("/api/stats?key=amenity")
        data = json.loads(resp.data)
        counts = [r["count"] for r in data["results"]]
        self.assertEqual(counts, sorted(counts, reverse=True))

    @patch("web.app.client")
    def test_api_stats_percent_sums_to_100(self, mock_client):
        mock_client.query_tag_count.return_value = RAW_STATS
        resp = self.client.get("/api/stats?key=amenity")
        data = json.loads(resp.data)
        total_pct = sum(r["percent"] for r in data["results"])
        self.assertAlmostEqual(total_pct, 100.0, places=1)


if __name__ == "__main__":
    unittest.main()

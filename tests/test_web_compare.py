import json
import unittest
from unittest.mock import patch, MagicMock

from flask import Flask
from tagstats.analyzer import TagReport, TagStat
from web.routes.compare import compare_bp


def _make_report(*pairs):
    stats = [TagStat(key=k, value=v, count=c) for k, v, c in pairs]
    return TagReport(stats=stats)


class TestCompareRoute(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__)
        app.register_blueprint(compare_bp)
        app.config["TESTING"] = True
        self.client = app.test_client()

        cache_mock = MagicMock()
        cache_mock.get.return_value = None
        self.cache_patcher = patch("web.routes.compare.get_cache", return_value=cache_mock)
        self.cache_patcher.start()

        self.report_highway = _make_report(
            ("highway", "residential", 1200),
            ("highway", "primary", 800),
        )
        self.report_amenity = _make_report(
            ("amenity", "parking", 500),
        )

    def tearDown(self):
        self.cache_patcher.stop()

    def test_missing_tags_param_returns_400(self):
        resp = self.client.get("/api/compare")
        self.assertEqual(resp.status_code, 400)
        data = json.loads(resp.data)
        self.assertIn("error", data)

    def test_single_tag_returns_400(self):
        resp = self.client.get("/api/compare?tags=highway")
        self.assertEqual(resp.status_code, 400)

    def test_too_many_tags_returns_400(self):
        tags = ",".join(["k" + str(i) for i in range(6)])
        resp = self.client.get(f"/api/compare?tags={tags}")
        self.assertEqual(resp.status_code, 400)

    @patch("web.routes.compare._fetch_or_cached")
    def test_valid_comparison_returns_200(self, mock_fetch):
        mock_fetch.side_effect = [self.report_highway, self.report_amenity]
        resp = self.client.get("/api/compare?tags=highway,amenity")
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertIn("comparisons", data)
        self.assertEqual(len(data["comparisons"]), 2)

    @patch("web.routes.compare._fetch_or_cached")
    def test_comparison_totals_are_correct(self, mock_fetch):
        mock_fetch.side_effect = [self.report_highway, self.report_amenity]
        resp = self.client.get("/api/compare?tags=highway,amenity")
        data = json.loads(resp.data)
        totals = {c["tag"]: c["total"] for c in data["comparisons"]}
        self.assertEqual(totals["highway"], 2000)
        self.assertEqual(totals["amenity"], 500)

    @patch("web.routes.compare._fetch_or_cached")
    def test_key_value_spec_parsed_correctly(self, mock_fetch):
        mock_fetch.return_value = self.report_highway
        self.client.get("/api/compare?tags=highway=residential,highway=primary")
        calls = mock_fetch.call_args_list
        self.assertEqual(calls[0][0], ("highway", "residential", None))
        self.assertEqual(calls[1][0], ("highway", "primary", None))

    @patch("web.routes.compare._fetch_or_cached")
    def test_area_param_forwarded(self, mock_fetch):
        mock_fetch.return_value = self.report_highway
        self.client.get("/api/compare?tags=highway,amenity&area=Berlin")
        for call in mock_fetch.call_args_list:
            self.assertEqual(call[0][2], "Berlin")

    @patch("web.routes.compare._fetch_or_cached")
    def test_overpass_error_returns_502(self, mock_fetch):
        from overpass.client import OverpassError
        mock_fetch.side_effect = OverpassError("timeout")
        resp = self.client.get("/api/compare?tags=highway,amenity")
        self.assertEqual(resp.status_code, 502)


if __name__ == "__main__":
    unittest.main()

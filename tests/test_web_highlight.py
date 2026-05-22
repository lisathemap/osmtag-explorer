import pytest
from unittest.mock import patch, MagicMock
from web.app import app
from tagstats.analyzer import TagStat, TagReport
from web.cache_registry import reset_cache


def _make_report(*stats):
    return TagReport(stats=list(stats))


class TestHighlightRoute:
    def setup_method(self):
        app.config["TESTING"] = True
        self.client = app.test_client()
        reset_cache()

    def teardown_method(self):
        reset_cache()

    def _mock_fetch(self, report):
        return patch(
            "web.routes.highlight._fetch_or_cached",
            return_value=report,
        )

    def test_missing_key_returns_400(self):
        resp = self.client.get("/api/highlight?q=high")
        assert resp.status_code == 400
        assert b"key" in resp.data

    def test_missing_q_returns_400(self):
        resp = self.client.get("/api/highlight?key=highway")
        assert resp.status_code == 400
        assert b"q" in resp.data

    def test_success_returns_200(self):
        report = _make_report(TagStat(key="highway", value="primary", count=10))
        with self._mock_fetch(report):
            resp = self.client.get("/api/highlight?key=highway&q=high")
        assert resp.status_code == 200

    def test_response_has_expected_keys(self):
        report = _make_report(TagStat(key="highway", value="primary", count=10))
        with self._mock_fetch(report):
            resp = self.client.get("/api/highlight?key=highway&q=high")
        data = resp.get_json()
        assert "query" in data
        assert "total" in data
        assert "matched" in data
        assert "results" in data

    def test_matched_count_correct(self):
        report = _make_report(
            TagStat(key="highway", value="primary", count=10),
            TagStat(key="name", value="Main St", count=5),
        )
        with self._mock_fetch(report):
            resp = self.client.get("/api/highlight?key=highway&q=high")
        data = resp.get_json()
        assert data["matched"] == 1

    def test_row_contains_html_fields(self):
        report = _make_report(TagStat(key="highway", value="primary", count=7))
        with self._mock_fetch(report):
            resp = self.client.get("/api/highlight?key=highway&q=high")
        row = resp.get_json()["results"][0]
        assert "key_html" in row
        assert "value_html" in row
        assert "<mark>" in row["key_html"]

    def test_overpass_error_returns_502(self):
        from overpass.client import OverpassError
        with patch(
            "web.routes.highlight._fetch_or_cached",
            side_effect=OverpassError("timeout"),
        ):
            resp = self.client.get("/api/highlight?key=highway&q=high")
        assert resp.status_code == 502

"""Tests for web/routes/diff.py."""
from unittest.mock import MagicMock, patch

import pytest

from tagstats.analyzer import TagReport, TagStat
from web.app import app
from web.cache_registry import reset_cache


def _make_report(*pairs) -> TagReport:
    return TagReport(stats=[TagStat(key=k, value=v, count=c) for k, v, c in pairs])


class TestDiffRoute:
    def setup_method(self):
        app.config["TESTING"] = True
        reset_cache()
        self.client = app.test_client()

    def teardown_method(self):
        reset_cache()

    def _mock_fetch(self, report_a, report_b):
        reports = iter([report_a, report_b])
        return patch(
            "web.routes.diff._fetch_or_cached",
            side_effect=lambda *a, **kw: next(reports),
        )

    def test_missing_tag_a_returns_400(self):
        resp = self.client.get("/api/diff?tag_b=shop")
        assert resp.status_code == 400
        assert b"tag_a" in resp.data or b"required" in resp.data

    def test_missing_tag_b_returns_400(self):
        resp = self.client.get("/api/diff?tag_a=highway")
        assert resp.status_code == 400

    def test_invalid_key_returns_400(self):
        resp = self.client.get("/api/diff?tag_a=!!bad&tag_b=shop")
        assert resp.status_code == 400

    def test_successful_diff_returns_200(self):
        ra = _make_report(("highway", None, 500))
        rb = _make_report(("highway", None, 600))
        with self._mock_fetch(ra, rb):
            resp = self.client.get("/api/diff?tag_a=highway&tag_b=highway")
        assert resp.status_code == 200

    def test_response_contains_diff_sections(self):
        ra = _make_report(("highway", None, 500))
        rb = _make_report(("highway", None, 600))
        with self._mock_fetch(ra, rb):
            resp = self.client.get("/api/diff?tag_a=highway&tag_b=highway")
        data = resp.get_json()
        assert "added" in data
        assert "removed" in data
        assert "changed" in data
        assert "unchanged" in data

    def test_changed_entry_has_delta(self):
        ra = _make_report(("highway", None, 500))
        rb = _make_report(("highway", None, 600))
        with self._mock_fetch(ra, rb):
            resp = self.client.get("/api/diff?tag_a=highway&tag_b=highway")
        data = resp.get_json()
        assert len(data["changed"]) == 1
        assert data["changed"][0]["delta"] == 100

    def test_overpass_error_returns_502(self):
        from overpass.client import OverpassError
        with patch("web.routes.diff._fetch_or_cached", side_effect=OverpassError("timeout")):
            resp = self.client.get("/api/diff?tag_a=highway&tag_b=shop")
        assert resp.status_code == 502

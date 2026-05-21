"""Unit tests for the Overpass API client."""

import json
import unittest
from unittest.mock import patch, MagicMock
from io import BytesIO

from overpass.client import OverpassClient, OverpassError


SAMPLE_RESPONSE = {
    "elements": [
        {
            "type": "count",
            "id": 0,
            "tags": {"nodes": "42", "ways": "7", "relations": "1", "total": "50"},
        }
    ]
}


class TestOverpassClientBuildQuery(unittest.TestCase):
    def setUp(self):
        self.client = OverpassClient()

    def test_query_key_only(self):
        ql = self.client._build_query("amenity")
        self.assertIn('["amenity"]', ql)
        self.assertNotIn('area', ql)

    def test_query_key_value(self):
        ql = self.client._build_query("amenity", "cafe")
        self.assertIn('["amenity"="cafe"]', ql)

    def test_query_with_area(self):
        ql = self.client._build_query("shop", area="Berlin")
        self.assertIn('area[name="Berlin"]', ql)
        self.assertIn('(area.searchArea)', ql)

    def test_query_timeout_embedded(self):
        client = OverpassClient(timeout=30)
        ql = client._build_query("highway")
        self.assertIn('[timeout:30]', ql)

    def test_query_key_value_no_area_filter(self):
        """Ensure area filter is absent when no area is specified."""
        ql = self.client._build_query("amenity", "cafe")
        self.assertNotIn('area', ql)
        self.assertNotIn('searchArea', ql)


class TestOverpassClientExecute(unittest.TestCase):
    def setUp(self):
        self.client = OverpassClient()

    def _mock_urlopen(self, payload: dict):
        """Return a mock urlopen context manager that yields the given payload."""
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(payload).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        return mock_resp

    @patch("overpass.client.urllib.request.urlopen")
    def test_successful_query(self, mock_urlopen):
        mock_urlopen.return_value = self._mock_urlopen(SAMPLE_RESPONSE)
        result = self.client.query_tag_count("amenity", "cafe")
        self.assertIn("elements", result)
        self.assertIn("_elapsed", result)
        self.assertEqual(result["elements"][0]["tags"]["total"], "50")

    @patch("overpass.client.urllib.request.urlopen")
    def test_elapsed_is_non_negative(self, mock_urlopen):
        """Verify that the _elapsed timing value is a non-negative number."""
        mock_urlopen.return_value = self._mock_urlopen(SAMPLE_RESPONSE)
        result = self.client.query_tag_count("amenity", "cafe")
        self.assertGreaterEqual(result["_elapsed"], 0)

    @patch("overpass.client.urllib.request.urlopen")
    def test_http_error_raises_overpass_error(self, mock_urlopen):
        import urllib.error
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url=None, code=429, msg="Too Many Requests", hdrs=None, fp=None
        )
        with self.assertRaises(OverpassError) as ctx:
            self.client.query_tag_count("shop")
        self.assertIn("429", str(ctx.exception))

    @patch("overpass.client.urllib.request.urlopen")
    def test_invalid_json_raises_overpass_error(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = b"not json"
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp
        with self.assertRaises(OverpassError):
            self.client._execute("[out:json]; nwr[amenity]; out count;")


if __name__ == "__main__":
    unittest.main()

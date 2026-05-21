"""Tests for tagstats.exporter.TagReportExporter."""

from __future__ import annotations

import csv
import io
import json
import unittest

from tagstats.analyzer import TagReport, TagStat
from tagstats.exporter import TagReportExporter


def _make_report() -> TagReport:
    stats = [
        TagStat(key="amenity", value="restaurant", count=500),
        TagStat(key="amenity", value="cafe", count=300),
        TagStat(key="amenity", value="bar", count=200),
    ]
    return TagReport(key="amenity", stats=stats)


class TestTagReportExporterCSV(unittest.TestCase):
    def setUp(self):
        self.exporter = TagReportExporter(_make_report())

    def test_csv_has_header(self):
        output = self.exporter.to_csv()
        self.assertTrue(output.startswith("tag,count,percentage"))

    def test_csv_row_count_respects_top_n(self):
        output = self.exporter.to_csv(top_n=2)
        reader = csv.DictReader(io.StringIO(output))
        rows = list(reader)
        self.assertEqual(len(rows), 2)

    def test_csv_sorted_descending(self):
        output = self.exporter.to_csv()
        reader = csv.DictReader(io.StringIO(output))
        counts = [int(r["count"]) for r in reader]
        self.assertEqual(counts, sorted(counts, reverse=True))

    def test_csv_percentage_sums_to_100(self):
        output = self.exporter.to_csv()
        reader = csv.DictReader(io.StringIO(output))
        total_pct = sum(float(r["percentage"]) for r in reader)
        self.assertAlmostEqual(total_pct, 100.0, places=2)

    def test_csv_invalid_top_n_raises(self):
        with self.assertRaises(ValueError):
            self.exporter.to_csv(top_n=0)


class TestTagReportExporterJSON(unittest.TestCase):
    def setUp(self):
        self.exporter = TagReportExporter(_make_report())

    def test_json_is_valid(self):
        output = self.exporter.to_json()
        parsed = json.loads(output)
        self.assertIn("entries", parsed)

    def test_json_contains_key(self):
        parsed = json.loads(self.exporter.to_json())
        self.assertEqual(parsed["key"], "amenity")

    def test_json_total_matches_report(self):
        report = _make_report()
        exporter = TagReportExporter(report)
        parsed = json.loads(exporter.to_json())
        self.assertEqual(parsed["total"], report.total_count)

    def test_json_top_n_limits_entries(self):
        parsed = json.loads(self.exporter.to_json(top_n=1))
        self.assertEqual(len(parsed["entries"]), 1)

    def test_json_entries_sorted_descending(self):
        parsed = json.loads(self.exporter.to_json())
        counts = [e["count"] for e in parsed["entries"]]
        self.assertEqual(counts, sorted(counts, reverse=True))


class TestTagReportExporterInit(unittest.TestCase):
    def test_invalid_type_raises(self):
        with self.assertRaises(TypeError):
            TagReportExporter("not a report")  # type: ignore


if __name__ == "__main__":
    unittest.main()

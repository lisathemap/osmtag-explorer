"""Tests for tagstats.formatter module."""

import unittest
from tagstats.analyzer import TagReport, TagStat
from tagstats.formatter import FormattedRow, TagReportFormatter, BAR_WIDTH


def _make_report(*pairs) -> TagReport:
    """Helper: create a TagReport from (key, value_or_None, count) tuples."""
    stats = [
        TagStat(key=k, value=v, count=c)
        for k, v, c in pairs
    ]
    return TagReport(stats=stats)


class TestTagReportFormatter(unittest.TestCase):

    def setUp(self):
        self.report = _make_report(
            ("highway", "residential", 500),
            ("highway", "primary", 300),
            ("amenity", "parking", 150),
            ("building", None, 50),
        )
        self.formatter = TagReportFormatter(self.report, top_n=3)

    def test_top_rows_length_respects_top_n(self):
        rows = self.formatter.top_rows()
        self.assertEqual(len(rows), 3)

    def test_top_rows_are_sorted_descending(self):
        rows = self.formatter.top_rows()
        counts = [r.count for r in rows]
        self.assertEqual(counts, sorted(counts, reverse=True))

    def test_formatted_row_label_matches_tag_label(self):
        rows = self.formatter.top_rows()
        self.assertEqual(rows[0].label, "highway=residential")
        self.assertEqual(rows[2].label, "amenity=parking")

    def test_percentage_sums_near_100_for_full_report(self):
        f = TagReportFormatter(self.report, top_n=4)
        total_pct = sum(r.percentage for r in f.top_rows())
        self.assertAlmostEqual(total_pct, 100.0, places=5)

    def test_bar_length_equals_bar_width(self):
        for row in self.formatter.top_rows():
            self.assertEqual(len(row.bar), BAR_WIDTH)

    def test_summary_line_contains_total(self):
        summary = self.formatter.summary_line()
        self.assertIn("1,000", summary)

    def test_render_text_contains_header(self):
        text = self.formatter.render_text()
        self.assertIn("Tag", text)
        self.assertIn("Count", text)

    def test_render_csv_header(self):
        csv = self.formatter.render_csv(include_header=True)
        first_line = csv.splitlines()[0]
        self.assertEqual(first_line, "tag,count,percentage")

    def test_render_csv_no_header(self):
        csv = self.formatter.render_csv(include_header=False)
        first_line = csv.splitlines()[0]
        self.assertNotEqual(first_line, "tag,count,percentage")

    def test_render_csv_row_count(self):
        csv = self.formatter.render_csv(include_header=False)
        self.assertEqual(len(csv.splitlines()), 3)

    def test_invalid_top_n_raises(self):
        with self.assertRaises(ValueError):
            TagReportFormatter(self.report, top_n=0)

    def test_top_n_larger_than_stats(self):
        f = TagReportFormatter(self.report, top_n=100)
        rows = f.top_rows()
        self.assertEqual(len(rows), len(self.report.stats))


if __name__ == "__main__":
    unittest.main()

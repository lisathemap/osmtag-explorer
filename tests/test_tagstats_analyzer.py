"""Tests for the TagStatsAnalyzer and related dataclasses."""

import pytest
from tagstats.analyzer import TagStat, TagReport, TagStatsAnalyzer


class TestTagStat:
    def test_tag_label_key_only(self):
        stat = TagStat(key="amenity", value=None, count=10)
        assert stat.tag_label == "amenity"

    def test_tag_label_key_value(self):
        stat = TagStat(key="amenity", value="cafe", count=5)
        assert stat.tag_label == "amenity=cafe"

    def test_negative_count_raises(self):
        with pytest.raises(ValueError):
            TagStat(key="amenity", value=None, count=-1)


class TestTagReport:
    def _make_report(self):
        return TagReport(stats=[
            TagStat(key="amenity", value="cafe", count=40),
            TagStat(key="amenity", value="restaurant", count=60),
        ])

    def test_total_count(self):
        report = self._make_report()
        assert report.total_count == 100

    def test_with_percentages(self):
        report = self._make_report()
        report.with_percentages()
        percentages = {s.value: s.percentage for s in report.stats}
        assert percentages["cafe"] == 40.0
        assert percentages["restaurant"] == 60.0

    def test_sorted_by_count(self):
        report = self._make_report()
        sorted_stats = report.sorted_by_count()
        assert sorted_stats[0].value == "restaurant"
        assert sorted_stats[1].value == "cafe"

    def test_top(self):
        report = self._make_report()
        top1 = report.top(1)
        assert len(top1) == 1
        assert top1[0].value == "restaurant"

    def test_empty_report_percentages(self):
        report = TagReport(stats=[])
        report.with_percentages()
        assert report.total_count == 0


class TestTagStatsAnalyzer:
    def setup_method(self):
        self.analyzer = TagStatsAnalyzer()

    def test_build_report_basic(self):
        raw = [{"value": "cafe", "count": "42"}, {"value": "pub", "count": "18"}]
        report = self.analyzer.build_report(raw, key="amenity")
        assert report.total_count == 60
        labels = [s.tag_label for s in report.stats]
        assert "amenity=cafe" in labels
        assert "amenity=pub" in labels

    def test_build_report_sets_area(self):
        raw = [{"value": "cafe", "count": "10"}]
        report = self.analyzer.build_report(raw, key="amenity", area="Berlin")
        assert report.stats[0].area == "Berlin"

    def test_merge_reports(self):
        r1 = TagReport(stats=[TagStat(key="amenity", value="cafe", count=30)])
        r2 = TagReport(stats=[TagStat(key="amenity", value="cafe", count=20),
                               TagStat(key="amenity", value="pub", count=10)])
        merged = self.analyzer.merge_reports([r1, r2])
        counts = {s.value: s.count for s in merged.stats}
        assert counts["cafe"] == 50
        assert counts["pub"] == 10

    def test_merge_empty(self):
        merged = self.analyzer.merge_reports([])
        assert merged.total_count == 0

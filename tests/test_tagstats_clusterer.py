"""Tests for tagstats.clusterer."""
import pytest

from tagstats.analyzer import TagReport, TagStat
from tagstats.clusterer import (
    Cluster,
    ClusterOptions,
    ClusterResult,
    cluster_report,
)


def _make_report(*pairs) -> TagReport:
    stats = [TagStat(key=k, value=v, count=c) for k, v, c in pairs]
    return TagReport(stats=stats)


class TestClusterOptions:
    def test_defaults(self):
        opts = ClusterOptions()
        assert opts.separator == ":"
        assert opts.max_depth == 1
        assert opts.min_cluster_size == 1

    def test_invalid_max_depth_raises(self):
        with pytest.raises(ValueError, match="max_depth"):
            ClusterOptions(max_depth=0)

    def test_invalid_min_cluster_size_raises(self):
        with pytest.raises(ValueError, match="min_cluster_size"):
            ClusterOptions(min_cluster_size=0)


class TestCluster:
    def test_total_count(self):
        c = Cluster(prefix="addr", stats=[TagStat("addr:city", None, 10), TagStat("addr:street", None, 20)])
        assert c.total_count == 30

    def test_size(self):
        c = Cluster(prefix="addr", stats=[TagStat("addr:city", None, 5)])
        assert c.size == 1

    def test_as_dict_keys(self):
        c = Cluster(prefix="addr", stats=[TagStat("addr:city", None, 5)])
        d = c.as_dict()
        assert "prefix" in d
        assert "size" in d
        assert "total_count" in d
        assert "stats" in d


class TestClusterReport:
    def test_groups_by_prefix(self):
        report = _make_report(
            ("addr:city", None, 10),
            ("addr:street", None, 20),
            ("name", None, 50),
        )
        result = cluster_report(report)
        assert result.get("addr") is not None
        assert result.get("addr").size == 2

    def test_ungrouped_when_below_min_size(self):
        report = _make_report(
            ("addr:city", None, 10),
            ("addr:street", None, 20),
            ("name", None, 50),
        )
        opts = ClusterOptions(min_cluster_size=2)
        result = cluster_report(report, opts)
        # "name" has only 1 entry => ungrouped
        assert any(s.key == "name" for s in result.ungrouped)

    def test_total_clusters(self):
        report = _make_report(
            ("addr:city", None, 10),
            ("addr:street", None, 5),
            ("highway", "primary", 100),
            ("highway", "secondary", 80),
        )
        result = cluster_report(report)
        assert result.total_clusters == 2

    def test_get_returns_none_for_missing(self):
        report = _make_report(("name", None, 1))
        result = cluster_report(report)
        assert result.get("nonexistent") is None

    def test_max_depth_two(self):
        report = _make_report(
            ("addr:city:name", None, 5),
            ("addr:city:code", None, 3),
            ("addr:street", None, 8),
        )
        opts = ClusterOptions(separator=":", max_depth=2)
        result = cluster_report(report, opts)
        city_cluster = result.get("addr:city")
        assert city_cluster is not None
        assert city_cluster.size == 2

    def test_as_dict_structure(self):
        report = _make_report(("name", None, 10))
        result = cluster_report(report)
        d = result.as_dict()
        assert "total_clusters" in d
        assert "ungrouped_count" in d
        assert "clusters" in d

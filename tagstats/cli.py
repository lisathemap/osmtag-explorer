"""Simple CLI entry point for rendering tag statistics."""

import argparse
import sys
from typing import List, Optional

from tagstats.analyzer import TagReport, TagStat
from tagstats.formatter import TagReportFormatter


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="osmtag-explorer",
        description="Display OpenStreetMap tag usage statistics.",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        metavar="N",
        help="Number of top tags to display (default: 10)",
    )
    parser.add_argument(
        "--format",
        choices=["text", "csv"],
        default="text",
        dest="output_format",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--no-header",
        action="store_true",
        default=False,
        help="Suppress CSV header row (only applies to --format csv)",
    )
    return parser.parse_args(argv)


def build_sample_report() -> TagReport:
    """Return a hard-coded sample report for demo / smoke-test purposes."""
    sample_data = [
        ("highway", "residential", 142_300),
        ("highway", "service", 98_750),
        ("building", "yes", 87_400),
        ("amenity", "parking", 34_100),
        ("highway", "footway", 29_800),
        ("landuse", "residential", 21_500),
        ("natural", "tree", 18_900),
        ("barrier", "fence", 15_200),
        ("surface", "asphalt", 12_400),
        ("access", "private", 9_850),
        ("leisure", "park", 7_300),
        ("shop", "convenience", 5_600),
    ]
    stats = [TagStat(key=k, value=v, count=c) for k, v, c in sample_data]
    return TagReport(stats=stats)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)

    report = build_sample_report()

    try:
        formatter = TagReportFormatter(report, top_n=args.top)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.output_format == "csv":
        print(formatter.render_csv(include_header=not args.no_header))
    else:
        print(formatter.render_text())

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())

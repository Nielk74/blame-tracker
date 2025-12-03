"""Command-line interface for blame tracker."""

import argparse
import sys
from pathlib import Path

from blame_tracker.core.blame_tracker import BlamTracker
from blame_tracker.reporters.html_reporter import HtmlReporter


def main() -> int:
    """Main CLI entry point.

    Returns:
        Exit code
    """
    parser = argparse.ArgumentParser(
        description="Track code coverage gaps intersected with recent git changes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  blame-tracker coverage.xml /path/to/repo --days 30

  # With custom output
  blame-tracker coverage.xml /path/to/repo --days 7 --output report.html

  # With multiple threads
  blame-tracker coverage.xml /path/to/repo --days 30 --workers 8
        """,
    )

    parser.add_argument(
        "coverage",
        help="Path to Cobertura coverage XML file",
    )

    parser.add_argument(
        "repo",
        help="Path to git repository",
    )

    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Number of days to look back for changes (default: 30)",
    )

    parser.add_argument(
        "--output",
        "-o",
        default="blame_report.html",
        help="Output HTML report path (default: blame_report.html)",
    )

    parser.add_argument(
        "--workers",
        "-w",
        type=int,
        default=4,
        help="Number of worker threads for git analysis (default: 4)",
    )

    args = parser.parse_args()

    # Validate inputs
    coverage_path = Path(args.coverage)
    if not coverage_path.exists():
        print(f"❌ Error: Coverage file not found: {args.coverage}", file=sys.stderr)
        return 1

    repo_path = Path(args.repo)
    if not repo_path.exists():
        print(f"❌ Error: Repository path not found: {args.repo}", file=sys.stderr)
        return 1

    if not (repo_path / ".git").exists():
        print(
            f"❌ Error: Not a git repository: {args.repo}",
            file=sys.stderr,
        )
        return 1

    if args.days <= 0:
        print("❌ Error: Days must be a positive number", file=sys.stderr)
        return 1

    if args.workers <= 0:
        print("❌ Error: Workers must be a positive number", file=sys.stderr)
        return 1

    try:
        # Run blame tracker
        print("🚀 Starting blame tracker analysis...")
        print(f"   Coverage file: {args.coverage}")
        print(f"   Repository: {args.repo}")
        print(f"   Lookback period: {args.days} days")
        print(f"   Worker threads: {args.workers}")
        print()

        tracker = BlamTracker(
            coverage_file=str(coverage_path),
            repo_path=str(repo_path),
            days=args.days,
        )

        analysis = tracker.run()

        # Generate report
        print()
        print(f"📝 Generating HTML report: {args.output}")
        reporter = HtmlReporter(args.output)
        reporter.generate(analysis)

        # Print summary
        print()
        print("=" * 60)
        print("📊 ANALYSIS SUMMARY")
        print("=" * 60)
        print(f"Total uncovered lines: {analysis.total_uncovered}")
        print(f"Culprit lines: {analysis.total_culprit}")
        print(f"Culprit percentage: {analysis.culprit_percentage:.1f}%")
        print(f"Files analyzed: {len(analysis.results)}")
        print()
        print(f"✓ Report generated: {args.output}")
        print("=" * 60)

        return 0

    except FileNotFoundError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

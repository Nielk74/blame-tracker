"""Main orchestrator for blame tracking."""

from datetime import datetime

from blame_tracker.core.blame_intersector import BlameIntersector
from blame_tracker.core.cobertura_parser import CoberturaParser
from blame_tracker.core.git_analyzer import GitAnalyzer
from blame_tracker.models import BlameAnalysis


class BlamTracker:
    """Main orchestrator for blame tracking."""

    def __init__(
        self,
        coverage_file: str,
        repo_path: str,
        days: int,
    ) -> None:
        """Initialize blame tracker.

        Args:
            coverage_file: Path to Cobertura coverage XML file
            repo_path: Path to git repository
            days: Number of days to look back for changes
        """
        self.coverage_file = coverage_file
        self.repo_path = repo_path
        self.days = days

    def run(self) -> BlameAnalysis:
        """Run complete blame tracking analysis.

        Returns:
            BlameAnalysis with results

        Raises:
            FileNotFoundError: If coverage file doesn't exist
            ValueError: If repo_path is not a valid git repository
        """
        # Parse coverage data
        print(f"📁 Parsing coverage file: {self.coverage_file}")
        parser = CoberturaParser(self.coverage_file, repo_root=self.repo_path)
        coverage_data = parser.parse()
        print(f"✓ Found coverage data for {len(coverage_data)} files")

        # Analyze git changes
        print(f"📊 Analyzing git changes (last {self.days} days)")
        git_analyzer = GitAnalyzer(self.repo_path)
        git_changes = git_analyzer.get_recent_changes(self.days)
        print(f"✓ Found {len(git_changes)} files with recent changes")

        # Intersect coverage with changes
        print("🔍 Intersecting coverage with recent changes")
        intersector = BlameIntersector(self.repo_path)
        results = intersector.intersect(coverage_data, git_changes)
        print(f"✓ Found {len(results)} files with culprit uncovered lines")

        # Create analysis result
        analysis = BlameAnalysis(
            analysis_date=datetime.now().isoformat(),
            days_lookback=self.days,
            coverage_file=self.coverage_file,
            repo_path=self.repo_path,
            results=results,
        )

        return analysis

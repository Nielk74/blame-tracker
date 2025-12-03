"""Tests for data models."""

import pytest

from blame_tracker.models import (
    BlameAnalysis,
    BlameLineGroup,
    BlameResult,
    FileCoverage,
    GitChange,
    LineInfo,
    LineStatus,
)


class TestLineInfo:
    """Tests for LineInfo model."""

    def test_line_info_creation(self) -> None:
        """Test creating a LineInfo object."""
        line = LineInfo(
            line_number=10,
            status=LineStatus.UNCOVERED,
            hits=0,
        )
        assert line.line_number == 10
        assert line.status == LineStatus.UNCOVERED
        assert line.hits == 0

    def test_line_info_hash(self) -> None:
        """Test LineInfo is hashable."""
        line1 = LineInfo(1, LineStatus.COVERED)
        line2 = LineInfo(1, LineStatus.UNCOVERED)
        assert hash(line1) == hash(line2)

    def test_line_info_equality(self) -> None:
        """Test LineInfo equality based on line number."""
        line1 = LineInfo(1, LineStatus.COVERED)
        line2 = LineInfo(1, LineStatus.UNCOVERED)
        assert line1 == line2


class TestFileCoverage:
    """Tests for FileCoverage model."""

    def test_file_coverage_creation(self) -> None:
        """Test creating FileCoverage."""
        coverage = FileCoverage(file_path="test.py")
        assert coverage.file_path == "test.py"
        assert coverage.lines == []

    def test_get_uncovered_lines(self) -> None:
        """Test getting uncovered lines."""
        coverage = FileCoverage(
            file_path="test.py",
            lines=[
                LineInfo(1, LineStatus.COVERED),
                LineInfo(2, LineStatus.UNCOVERED),
                LineInfo(3, LineStatus.UNCOVERED),
                LineInfo(4, LineStatus.COVERED),
            ],
        )
        uncovered = coverage.get_uncovered_lines()
        assert uncovered == {2, 3}

    def test_get_covered_lines(self) -> None:
        """Test getting covered lines."""
        coverage = FileCoverage(
            file_path="test.py",
            lines=[
                LineInfo(1, LineStatus.COVERED),
                LineInfo(2, LineStatus.UNCOVERED),
                LineInfo(3, LineStatus.COVERED),
            ],
        )
        covered = coverage.get_covered_lines()
        assert covered == {1, 3}


class TestGitChange:
    """Tests for GitChange model."""

    def test_git_change_creation(self) -> None:
        """Test creating GitChange."""
        change = GitChange(
            file_path="src/main.py",
            line_numbers={10, 11, 12},
            author="John Doe",
            commit_hash="abc1234",
        )
        assert change.file_path == "src/main.py"
        assert change.line_numbers == {10, 11, 12}
        assert change.author == "John Doe"


class TestBlameLineGroup:
    """Tests for BlameLineGroup model."""

    def test_blame_line_group_creation(self) -> None:
        """Test creating BlameLineGroup."""
        group = BlameLineGroup(
            start_line=10,
            end_line=12,
            context_before=["line 8", "line 9"],
            culprit_lines=["line 10", "line 11", "line 12"],
            context_after=["line 13", "line 14"],
            language="python",
        )
        assert group.start_line == 10
        assert group.end_line == 12
        assert group.line_count == 7

    def test_all_lines(self) -> None:
        """Test all_lines property."""
        group = BlameLineGroup(
            start_line=10,
            end_line=12,
            context_before=["line 8", "line 9"],
            culprit_lines=["line 10", "line 11"],
            context_after=["line 13"],
        )
        assert len(group.all_lines) == 5


class TestBlameResult:
    """Tests for BlameResult model."""

    def test_blame_result_creation(self) -> None:
        """Test creating BlameResult."""
        result = BlameResult(
            file_path="src/main.py",
            total_uncovered_lines=10,
            uncovered_in_changes=5,
        )
        assert result.file_path == "src/main.py"
        assert result.culprit_percentage == 50.0

    def test_culprit_percentage_zero_uncovered(self) -> None:
        """Test culprit percentage when there are no uncovered lines."""
        result = BlameResult(
            file_path="src/main.py",
            total_uncovered_lines=0,
            uncovered_in_changes=0,
        )
        assert result.culprit_percentage == 0.0


class TestBlameAnalysis:
    """Tests for BlameAnalysis model."""

    def test_blame_analysis_creation(self) -> None:
        """Test creating BlameAnalysis."""
        analysis = BlameAnalysis(
            analysis_date="2024-01-01T00:00:00",
            days_lookback=30,
            coverage_file="coverage.xml",
            repo_path="/repo",
        )
        assert analysis.days_lookback == 30
        assert analysis.total_uncovered == 0

    def test_total_uncovered(self) -> None:
        """Test total uncovered calculation."""
        results = [
            BlameResult("file1.py", 10, 5),
            BlameResult("file2.py", 20, 10),
        ]
        analysis = BlameAnalysis(
            analysis_date="2024-01-01T00:00:00",
            days_lookback=30,
            coverage_file="coverage.xml",
            repo_path="/repo",
            results=results,
        )
        assert analysis.total_uncovered == 30

    def test_total_culprit(self) -> None:
        """Test total culprit calculation."""
        results = [
            BlameResult("file1.py", 10, 5),
            BlameResult("file2.py", 20, 10),
        ]
        analysis = BlameAnalysis(
            analysis_date="2024-01-01T00:00:00",
            days_lookback=30,
            coverage_file="coverage.xml",
            repo_path="/repo",
            results=results,
        )
        assert analysis.total_culprit == 15

    def test_culprit_percentage(self) -> None:
        """Test overall culprit percentage."""
        results = [
            BlameResult("file1.py", 10, 5),
            BlameResult("file2.py", 20, 10),
        ]
        analysis = BlameAnalysis(
            analysis_date="2024-01-01T00:00:00",
            days_lookback=30,
            coverage_file="coverage.xml",
            repo_path="/repo",
            results=results,
        )
        assert analysis.culprit_percentage == 50.0

    def test_get_top_culprits(self) -> None:
        """Test getting top culprits."""
        results = [
            BlameResult("file1.py", 10, 5),
            BlameResult("file2.py", 20, 15),
            BlameResult("file3.py", 30, 10),
        ]
        analysis = BlameAnalysis(
            analysis_date="2024-01-01T00:00:00",
            days_lookback=30,
            coverage_file="coverage.xml",
            repo_path="/repo",
            results=results,
        )
        top = analysis.get_top_culprits(2)
        assert len(top) == 2
        assert top[0].file_path == "file2.py"
        assert top[1].file_path == "file3.py"

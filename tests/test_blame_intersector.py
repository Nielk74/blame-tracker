"""Tests for blame intersector."""

from pathlib import Path

import pytest

from blame_tracker.core.blame_intersector import BlameIntersector
from blame_tracker.models import (
    FileCoverage,
    GitChange,
    LineInfo,
    LineStatus,
)


class TestBlameIntersector:
    """Tests for BlameIntersector."""

    def test_intersect_no_changes(self, tmp_path: Path) -> None:
        """Test intersection when no git changes exist."""
        # Create test file
        repo_path = tmp_path
        test_file = repo_path / "test.py"
        test_file.write_text("line 1\nline 2\nline 3\n")

        # Coverage data without git changes
        coverage_data = {
            "test.py": FileCoverage(
                file_path="test.py",
                lines=[
                    LineInfo(1, LineStatus.COVERED),
                    LineInfo(2, LineStatus.UNCOVERED),
                    LineInfo(3, LineStatus.COVERED),
                ],
            ),
        }

        intersector = BlameIntersector(str(repo_path))
        results = intersector.intersect(coverage_data, {})

        assert len(results) == 0

    def test_intersect_with_changes(self, tmp_path: Path) -> None:
        """Test intersection with git changes."""
        # Create test file
        repo_path = tmp_path
        test_file = repo_path / "test.py"
        test_file.write_text("line 1\nline 2\nline 3\nline 4\nline 5\n")

        # Coverage data
        coverage_data = {
            "test.py": FileCoverage(
                file_path="test.py",
                lines=[
                    LineInfo(1, LineStatus.COVERED),
                    LineInfo(2, LineStatus.UNCOVERED),
                    LineInfo(3, LineStatus.UNCOVERED),
                    LineInfo(4, LineStatus.UNCOVERED),
                    LineInfo(5, LineStatus.COVERED),
                ],
            ),
        }

        # Git changes
        git_changes = {
            "test.py": GitChange(
                file_path="test.py",
                line_numbers={2, 4},
                author="Test Author",
                commit_hash="abc123",
            ),
        }

        intersector = BlameIntersector(str(repo_path))
        results = intersector.intersect(coverage_data, git_changes)

        assert len(results) == 1
        result = results[0]
        assert result.file_path == "test.py"
        assert result.total_uncovered_lines == 3
        assert result.uncovered_in_changes == 2

    def test_detect_language(self) -> None:
        """Test language detection from file extension."""
        intersector = BlameIntersector("/repo")

        assert intersector._detect_language("test.py") == "python"
        assert intersector._detect_language("test.js") == "javascript"
        assert intersector._detect_language("test.ts") == "typescript"
        assert intersector._detect_language("test.cpp") == "cpp"
        assert intersector._detect_language("test.cs") == "csharp"
        assert intersector._detect_language("test.go") == "go"
        assert intersector._detect_language("test.rs") == "rust"
        assert intersector._detect_language("test.txt") == "text"

    def test_get_line_safe(self) -> None:
        """Test safe line retrieval."""
        lines = ["line 1", "line 2", "line 3"]

        # Valid lines (1-based indexing)
        assert BlameIntersector._get_line_safe(lines, 1) == "line 1"
        assert BlameIntersector._get_line_safe(lines, 2) == "line 2"
        assert BlameIntersector._get_line_safe(lines, 3) == "line 3"

        # Out of bounds
        assert BlameIntersector._get_line_safe(lines, 0) == ""
        assert BlameIntersector._get_line_safe(lines, 4) == ""
        assert BlameIntersector._get_line_safe(lines, 10) == ""

    def test_create_blame_groups(self, tmp_path: Path) -> None:
        """Test creation of blame groups with context."""
        repo_path = tmp_path
        test_file = repo_path / "test.py"

        # Create file with 15 lines
        lines = [f"line {i}\n" for i in range(1, 16)]
        test_file.write_text("".join(lines))

        with open(test_file, "r") as f:
            file_lines = f.readlines()

        intersector = BlameIntersector(str(repo_path))
        change = GitChange(
            file_path="test.py",
            line_numbers={5, 6, 7},
            author="Test",
            commit_hash="abc123",
        )

        groups = intersector._create_blame_groups(
            {5, 6, 7},
            file_lines,
            change,
            "test.py",
        )

        assert len(groups) == 1
        group = groups[0]
        assert group.start_line == 5
        assert group.end_line == 7
        # Context before: lines 1-4 (limited by start of file)
        assert len(group.context_before) == 4
        assert len(group.culprit_lines) == 3   # 3 culprit lines
        # Context after: lines 8-12 (5 context lines)
        assert len(group.context_after) == 5

    def test_group_consecutive_lines(self, tmp_path: Path) -> None:
        """Test grouping of consecutive culprit lines."""
        repo_path = tmp_path
        test_file = repo_path / "test.py"

        # Create file with 30 lines
        lines = [f"line {i}\n" for i in range(1, 31)]
        test_file.write_text("".join(lines))

        with open(test_file, "r") as f:
            file_lines = f.readlines()

        intersector = BlameIntersector(str(repo_path))
        change = GitChange(
            file_path="test.py",
            line_numbers={5, 6, 7, 25, 26},  # Much further apart now
            author="Test",
            commit_hash="abc123",
        )

        # Lines 5-7 and 25-26 are far apart (more than 2*CONTEXT_LINES = 10)
        groups = intersector._create_blame_groups(
            {5, 6, 7, 25, 26},
            file_lines,
            change,
            "test.py",
        )

        # Should create two groups
        assert len(groups) == 2
        assert groups[0].start_line == 5
        assert groups[0].end_line == 7
        assert groups[1].start_line == 25
        assert groups[1].end_line == 26

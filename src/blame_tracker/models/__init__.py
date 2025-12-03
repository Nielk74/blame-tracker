"""Data models for blame tracking."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Set


class LineStatus(Enum):
    """Coverage status of a line."""

    COVERED = "covered"
    UNCOVERED = "uncovered"
    PARTIAL = "partial"


@dataclass
class LineInfo:
    """Information about a single line in coverage data."""

    line_number: int
    status: LineStatus
    hits: int = 0

    def __hash__(self) -> int:
        return hash(self.line_number)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, LineInfo):
            return NotImplemented
        return self.line_number == other.line_number


@dataclass
class FileCoverage:
    """Coverage information for a single file."""

    file_path: str
    lines: List[LineInfo] = field(default_factory=list)

    def get_uncovered_lines(self) -> Set[int]:
        """Get set of uncovered line numbers."""
        return {
            line.line_number
            for line in self.lines
            if line.status == LineStatus.UNCOVERED
        }

    def get_covered_lines(self) -> Set[int]:
        """Get set of covered line numbers."""
        return {
            line.line_number
            for line in self.lines
            if line.status == LineStatus.COVERED
        }


@dataclass
class GitChange:
    """Information about a git change."""

    file_path: str
    line_numbers: Set[int] = field(default_factory=set)
    author: str = ""
    commit_hash: str = ""
    commit_date: str = ""
    commit_message: str = ""

    def __hash__(self) -> int:
        return hash(self.file_path)


@dataclass
class BlameLineGroup:
    """Group of consecutive lines with blame information."""

    start_line: int
    end_line: int
    context_before: List[str] = field(default_factory=list)
    culprit_lines: List[str] = field(default_factory=list)
    context_after: List[str] = field(default_factory=list)
    git_changes: List[GitChange] = field(default_factory=list)
    language: str = "text"

    @property
    def all_lines(self) -> List[str]:
        """Get all lines including context."""
        return self.context_before + self.culprit_lines + self.context_after

    @property
    def line_count(self) -> int:
        """Total number of lines in this group."""
        return len(self.all_lines)


@dataclass
class BlameResult:
    """Result of blame analysis for a file.

    Shows which uncovered lines (coverage gaps) were recently modified,
    helping identify which commits likely broke the tests.
    """

    file_path: str
    total_uncovered_lines: int  # Total lines not covered by tests
    uncovered_in_changes: int  # Of those, how many were recently changed
    blame_groups: List[BlameLineGroup] = field(default_factory=list)

    @property
    def culprit_percentage(self) -> float:
        """Percentage of uncovered lines that were recently changed.

        Higher percentage means more recent code is not tested,
        suggesting a recent commit likely broke tests.
        """
        if self.total_uncovered_lines == 0:
            return 0.0
        return (self.uncovered_in_changes / self.total_uncovered_lines) * 100


@dataclass
class BlameAnalysis:
    """Complete blame analysis result."""

    analysis_date: str
    days_lookback: int
    coverage_file: str
    repo_path: str
    results: List[BlameResult] = field(default_factory=list)

    @property
    def total_uncovered(self) -> int:
        """Total uncovered lines across all files."""
        return sum(r.total_uncovered_lines for r in self.results)

    @property
    def total_culprit(self) -> int:
        """Total uncovered lines that are in recent changes."""
        return sum(r.uncovered_in_changes for r in self.results)

    @property
    def culprit_percentage(self) -> float:
        """Overall culprit percentage."""
        if self.total_uncovered == 0:
            return 0.0
        return (self.total_culprit / self.total_uncovered) * 100

    def get_top_culprits(self, limit: int = 10) -> List[BlameResult]:
        """Get files with highest culprit percentage."""
        return sorted(
            self.results,
            key=lambda r: r.uncovered_in_changes,
            reverse=True,
        )[:limit]

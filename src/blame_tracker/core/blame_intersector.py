"""Blame intersector - finds intersection of coverage gaps and recent changes."""

from pathlib import Path
from typing import Dict, List, Set

from tqdm import tqdm

from blame_tracker.models import (
    BlameLineGroup,
    BlameResult,
    FileCoverage,
    GitChange,
)


class BlameIntersector:
    """Intersect coverage data with git changes."""

    CONTEXT_LINES = 5  # Lines before and after culprit

    def __init__(self, repo_path: str) -> None:
        """Initialize blame intersector.

        Args:
            repo_path: Path to git repository
        """
        self.repo_path = Path(repo_path)

    def intersect(
        self,
        coverage_data: Dict[str, FileCoverage],
        git_changes: Dict[str, GitChange],
    ) -> List[BlameResult]:
        """Intersect coverage with git changes.

        Args:
            coverage_data: Coverage data by file path
            git_changes: Git changes by file path

        Returns:
            List of BlameResult objects
        """
        results: List[BlameResult] = []

        for file_path, file_coverage in tqdm(
            coverage_data.items(),
            desc="Intersecting coverage with changes",
            unit="file",
        ):
            uncovered_lines = file_coverage.get_uncovered_lines()

            if not uncovered_lines:
                continue

            # Get changes for this file (if any)
            change = git_changes.get(file_path)
            culprit_lines = (
                uncovered_lines & change.line_numbers
                if change
                else set()
            )

            if culprit_lines:
                # Read file content for context
                try:
                    file_full_path = self.repo_path / file_path
                    if file_full_path.exists():
                        with open(file_full_path, "r", encoding="utf-8", errors="ignore") as f:
                            file_lines = f.readlines()
                    else:
                        file_lines = []
                except Exception:
                    file_lines = []

                # Create blame groups
                groups = self._create_blame_groups(
                    culprit_lines,
                    file_lines,
                    change,
                    file_path,
                )

                result = BlameResult(
                    file_path=file_path,
                    total_uncovered_lines=len(uncovered_lines),
                    uncovered_in_changes=len(culprit_lines),
                    blame_groups=groups,
                )

                results.append(result)

        return sorted(
            results,
            key=lambda r: r.uncovered_in_changes,
            reverse=True,
        )

    def _create_blame_groups(
        self,
        culprit_lines: Set[int],
        file_lines: List[str],
        change: GitChange,
        file_path: str,
    ) -> List[BlameLineGroup]:
        """Create grouped blame lines with context.

        Args:
            culprit_lines: Set of uncovered lines that were recently changed
            file_lines: All lines from the file
            change: Git change information
            file_path: Path to the file

        Returns:
            List of BlameLineGroup objects
        """
        if not culprit_lines:
            return []

        # Sort culprit lines
        sorted_culprits = sorted(culprit_lines)

        # Group consecutive lines
        groups: List[BlameLineGroup] = []
        current_group_start = sorted_culprits[0]
        current_group_lines = [current_group_start]

        for line_num in sorted_culprits[1:]:
            # If line is within context distance, continue group
            if line_num <= current_group_lines[-1] + (2 * self.CONTEXT_LINES):
                current_group_lines.append(line_num)
            else:
                # Create group for current sequence
                group = self._create_single_group(
                    current_group_lines,
                    file_lines,
                    change,
                    file_path,
                )
                groups.append(group)

                # Start new group
                current_group_start = line_num
                current_group_lines = [line_num]

        # Don't forget last group
        if current_group_lines:
            group = self._create_single_group(
                current_group_lines,
                file_lines,
                change,
                file_path,
            )
            groups.append(group)

        return groups

    def _create_single_group(
        self,
        culprit_lines: List[int],
        file_lines: List[str],
        change: GitChange,
        file_path: str,
    ) -> BlameLineGroup:
        """Create a single blame group with context.

        Args:
            culprit_lines: List of culprit line numbers
            file_lines: All lines from the file
            change: Git change information
            file_path: Path to the file

        Returns:
            BlameLineGroup object
        """
        if not culprit_lines:
            raise ValueError("culprit_lines cannot be empty")

        # Determine context range
        start_line = culprit_lines[0]
        end_line = culprit_lines[-1]

        context_start = max(1, start_line - self.CONTEXT_LINES)
        context_end = min(len(file_lines), end_line + self.CONTEXT_LINES)

        # Extract lines with 1-based indexing
        context_before = []
        culprit_content = []
        context_after = []

        for line_num in range(context_start, context_end + 1):
            if line_num < start_line:
                context_before.append(
                    self._get_line_safe(file_lines, line_num)
                )
            elif line_num <= end_line:
                culprit_content.append(
                    self._get_line_safe(file_lines, line_num)
                )
            else:
                context_after.append(
                    self._get_line_safe(file_lines, line_num)
                )

        # Detect language from file extension
        language = self._detect_language(file_path)

        return BlameLineGroup(
            start_line=start_line,
            end_line=end_line,
            context_before=context_before,
            culprit_lines=culprit_content,
            context_after=context_after,
            git_changes=[change],
            language=language,
        )

    @staticmethod
    def _get_line_safe(file_lines: List[str], line_num: int) -> str:
        """Get line from file safely (1-based indexing).

        Args:
            file_lines: List of all file lines
            line_num: 1-based line number

        Returns:
            Line content or empty string if out of bounds
        """
        if 1 <= line_num <= len(file_lines):
            return file_lines[line_num - 1].rstrip("\n\r")
        return ""

    @staticmethod
    def _detect_language(file_path: str) -> str:
        """Detect programming language from file extension.

        Args:
            file_path: Path to the file

        Returns:
            Language identifier for syntax highlighting
        """
        extension_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".jsx": "javascript",
            ".cpp": "cpp",
            ".cc": "cpp",
            ".cxx": "cpp",
            ".h": "cpp",
            ".hpp": "cpp",
            ".cs": "csharp",
            ".php": "php",
            ".rs": "rust",
            ".go": "go",
            ".java": "java",
            ".c": "c",
            ".swift": "swift",
            ".kt": "kotlin",
            ".rb": "ruby",
            ".sh": "bash",
            ".bash": "bash",
        }

        file_ext = Path(file_path).suffix.lower()
        return extension_map.get(file_ext, "text")

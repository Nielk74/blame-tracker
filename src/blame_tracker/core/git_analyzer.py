"""Git analyzer for extracting recent changes."""

import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set

from git import Repo
from git.objects.commit import Commit
from tqdm import tqdm

from blame_tracker.models import GitChange


class GitAnalyzer:
    """Analyze git repository for recent changes."""

    def __init__(self, repo_path: str) -> None:
        """Initialize git analyzer.

        Args:
            repo_path: Path to git repository

        Raises:
            ValueError: If path is not a valid git repository
        """
        try:
            self.repo = Repo(repo_path)
        except Exception as e:
            raise ValueError(f"Invalid git repository: {repo_path}") from e

        self.repo_path = Path(repo_path)

    def get_recent_changes(
        self,
        days: int,
        max_workers: int = 4,
    ) -> Dict[str, GitChange]:
        """Extract all changes from the past N days using multithreading.

        Args:
            days: Number of days to look back
            max_workers: Number of threads to use for processing commits

        Returns:
            Dictionary mapping file paths to GitChange objects
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        # Get all commits in the date range
        commits = self._get_commits_since(cutoff_date)

        changes: Dict[str, GitChange] = {}

        # Use ThreadPoolExecutor for parallel processing
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all commit processing tasks
            futures = {
                executor.submit(self._process_commit, commit): commit
                for commit in commits
            }

            # Process results as they complete with progress bar
            for future in tqdm(
                as_completed(futures),
                total=len(futures),
                desc="Analyzing git changes",
                unit="commit",
            ):
                commit = futures[future]
                try:
                    commit_changes = future.result()
                    # Merge changes for each file
                    for file_path, change in commit_changes.items():
                        if file_path not in changes:
                            changes[file_path] = change
                        else:
                            # Merge line numbers from multiple commits
                            changes[file_path].line_numbers.update(
                                change.line_numbers
                            )
                except Exception:
                    # Skip commits that cause errors
                    continue

        return changes

    def _get_commits_since(self, cutoff_date: datetime) -> List[Commit]:
        """Get all commits since a given date.

        Args:
            cutoff_date: Only commits after this date are returned

        Returns:
            List of commits
        """
        commits = []
        try:
            for commit in self.repo.iter_commits():
                commit_date = datetime.fromtimestamp(commit.committed_date)
                if commit_date < cutoff_date:
                    break
                commits.append(commit)
        except Exception:
            pass

        return commits

    def _process_commit(self, commit: Commit) -> Dict[str, GitChange]:
        """Process a single commit and extract changed lines.

        Args:
            commit: Commit object to process

        Returns:
            Dictionary mapping file paths to GitChange objects
        """
        changes: Dict[str, GitChange] = {}

        try:
            # Get the diff against parent
            if commit.parents:
                diffs = commit.parents[0].diff(commit)
            else:
                # For the first commit, compare against empty tree
                diffs = commit.tree.diff(None)

            for diff in diffs:
                file_path = diff.b_path or diff.a_path
                if not file_path:
                    continue

                # Extract changed line numbers from the diff
                changed_lines = self._extract_changed_lines(diff)

                if changed_lines:
                    changes[file_path] = GitChange(
                        file_path=file_path,
                        line_numbers=changed_lines,
                        author=commit.author.name,
                        commit_hash=commit.hexsha[:7],
                        commit_date=datetime.fromtimestamp(
                            commit.committed_date
                        ).isoformat(),
                        commit_message=commit.message.split("\n")[0],
                    )

        except Exception:
            pass

        return changes

    def _extract_changed_lines(self, diff) -> Set[int]:
        """Extract line numbers that were changed in a diff.

        Args:
            diff: GitPython diff object

        Returns:
            Set of line numbers that were added or modified
        """
        changed_lines: Set[int] = set()

        try:
            if not diff.diff:
                return changed_lines

            # Parse the unified diff format
            diff_text = diff.diff.decode("utf-8", errors="ignore")
            lines = diff_text.split("\n")

            current_line_num = 0
            for line in lines:
                # Match hunk headers like @@ -10,5 +10,6 @@
                hunk_match = re.match(r"@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", line)
                if hunk_match:
                    current_line_num = int(hunk_match.group(1))
                    continue

                # Only track added/modified lines (starting with +)
                # Skip file markers and context lines
                if line.startswith("+") and not line.startswith("+++"):
                    changed_lines.add(current_line_num)
                    current_line_num += 1
                elif not line.startswith("-"):
                    # Context lines and other content
                    if not line.startswith("\\"):  # Skip "\ No newline" markers
                        current_line_num += 1

        except Exception:
            pass

        return changed_lines

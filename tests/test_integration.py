"""Integration tests for the full blame tracker workflow."""

import subprocess
import tempfile
from pathlib import Path

import pytest

from blame_tracker.core.blame_intersector import BlameIntersector
from blame_tracker.core.blame_tracker import BlamTracker
from blame_tracker.core.cobertura_parser import CoberturaParser
from blame_tracker.core.git_analyzer import GitAnalyzer


class TestIntegration:
    """Integration tests for the complete workflow."""

    def test_full_workflow_with_real_git_repo(self, tmp_path: Path) -> None:
        """Test the complete blame tracker workflow with a real git repository.

        This test:
        1. Creates a real git repository
        2. Makes initial commit
        3. Adds new code in a second commit
        4. Creates matching coverage file
        5. Runs blame tracker
        6. Verifies results are accurate
        """
        # Setup git repo
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()

        # Initialize git
        subprocess.run(
            ["git", "init"],
            cwd=repo_path,
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=repo_path,
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=repo_path,
            capture_output=True,
            check=True,
        )

        # Create initial file and commit
        module_file = repo_path / "module.py"
        module_file.write_text("""def func1():
    print("one")
    return 1

def func2():
    print("two")
    return 2
""")
        subprocess.run(
            ["git", "add", "module.py"],
            cwd=repo_path,
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=repo_path,
            capture_output=True,
            check=True,
        )

        # Add more code in second commit (this will be "recent changes")
        module_file.write_text("""def func1():
    print("one")
    return 1

def func2():
    print("two")
    return 2

def func3():
    x = 1
    y = 2
    z = 3
    return x + y + z
""")
        subprocess.run(
            ["git", "add", "module.py"],
            cwd=repo_path,
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "Add func3"],
            cwd=repo_path,
            capture_output=True,
            check=True,
        )

        # Create coverage file with uncovered lines
        coverage_file = repo_path / "coverage.xml"
        coverage_file.write_text("""<?xml version="1.0" ?>
<coverage version="5.4" timestamp="1701619200">
    <packages>
        <package name=".">
            <classes>
                <class name="module" filename="module.py">
                    <lines>
                        <line number="1" hits="1"/>
                        <line number="2" hits="1"/>
                        <line number="3" hits="1"/>
                        <line number="4" hits="0"/>
                        <line number="5" hits="1"/>
                        <line number="6" hits="1"/>
                        <line number="7" hits="0"/>
                        <line number="8" hits="0"/>
                        <line number="9" hits="0"/>
                        <line number="10" hits="0"/>
                        <line number="11" hits="0"/>
                        <line number="12" hits="0"/>
                        <line number="13" hits="0"/>
                    </lines>
                </class>
            </classes>
        </package>
    </packages>
</coverage>""")

        # Run blame tracker
        tracker = BlamTracker(
            coverage_file=str(coverage_file),
            repo_path=str(repo_path),
            days=30,
        )
        analysis = tracker.run()

        # Verify results
        assert len(analysis.results) == 1, f"Expected 1 file, got {len(analysis.results)}"
        result = analysis.results[0]
        assert result.file_path == "module.py"
        # Uncovered: lines 4, 7, 8, 9, 10, 11, 12, 13 (8 total including blank lines)
        assert result.total_uncovered_lines == 8
        # All of those lines are in recent changes (the second commit added all content)
        assert result.uncovered_in_changes == 8
        assert len(result.blame_groups) > 0
        # Verify blame group has correct structure
        blame_group = result.blame_groups[0]
        assert blame_group.start_line == 4
        assert blame_group.end_line == 13

    def test_git_analyzer_detects_real_changes(self, tmp_path: Path) -> None:
        """Test that git analyzer correctly detects real file changes."""
        # Create a repo with actual commits
        repo_path = tmp_path / "real_repo"
        repo_path.mkdir()

        # Initialize
        subprocess.run(["git", "init"], cwd=repo_path, capture_output=True, check=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=repo_path,
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=repo_path,
            capture_output=True,
            check=True,
        )

        # Commit 1: Create file
        (repo_path / "file1.py").write_text("def a():\n    pass\n")
        subprocess.run(
            ["git", "add", "file1.py"],
            cwd=repo_path,
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "Add file1"],
            cwd=repo_path,
            capture_output=True,
            check=True,
        )

        # Commit 2: Add lines to file
        (repo_path / "file1.py").write_text("def a():\n    pass\n\ndef b():\n    return 42\n")
        subprocess.run(
            ["git", "add", "file1.py"],
            cwd=repo_path,
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "Add function b"],
            cwd=repo_path,
            capture_output=True,
            check=True,
        )

        # Analyze
        analyzer = GitAnalyzer(str(repo_path))
        changes = analyzer.get_recent_changes(days=30, max_workers=2)

        # Should find file1.py with changes
        assert "file1.py" in changes, f"Expected file1.py in {list(changes.keys())}"
        assert len(changes["file1.py"].line_numbers) > 0
        # Lines 4-5 are the new function
        assert 4 in changes["file1.py"].line_numbers or 5 in changes["file1.py"].line_numbers

    def test_coverage_file(self, tmp_path: Path) -> None:
        """Test the complete blame tracker workflow."""
        # Create a temporary coverage file
        coverage_xml = """<?xml version="1.0" ?>
<coverage version="5.4" timestamp="1701619200">
    <packages>
        <package name="src">
            <classes>
                <class name="test" filename="src/test.py">
                    <lines>
                        <line number="1" hits="1"/>
                        <line number="2" hits="0"/>
                        <line number="3" hits="0"/>
                        <line number="4" hits="1"/>
                    </lines>
                </class>
            </classes>
        </package>
    </packages>
</coverage>"""

        coverage_file = tmp_path / "coverage.xml"
        coverage_file.write_text(coverage_xml)

        # Test parser
        parser = CoberturaParser(str(coverage_file))
        coverage_data = parser.parse()

        assert "src/test.py" in coverage_data
        assert len(coverage_data["src/test.py"].lines) == 4
        assert coverage_data["src/test.py"].get_uncovered_lines() == {2, 3}

    def test_git_analyzer_on_current_repo(self) -> None:
        """Test git analyzer on the current repository."""
        analyzer = GitAnalyzer(".")

        # Get recent changes
        changes = analyzer.get_recent_changes(days=30, max_workers=2)

        # Should find some changes in our repo
        assert len(changes) > 0

        # Check structure
        for file_path, change in changes.items():
            assert isinstance(file_path, str)
            assert len(change.line_numbers) > 0
            assert change.author
            assert change.commit_hash
            assert change.commit_date
            assert change.commit_message

    def test_git_analyzer_respects_lookback_period(self) -> None:
        """Test that git analyzer respects the lookback period."""
        analyzer = GitAnalyzer(".")

        # Get changes from a very short period
        changes_1day = analyzer.get_recent_changes(days=1, max_workers=2)
        changes_30day = analyzer.get_recent_changes(days=30, max_workers=2)

        # 30 days should have at least as many files as 1 day
        assert len(changes_30day) >= len(changes_1day)

    def test_parse_unified_diff(self) -> None:
        """Test unified diff parsing."""
        analyzer = GitAnalyzer(".")

        # Create a sample unified diff
        diff_text = """diff --git a/test.py b/test.py
index 1234567..abcdefg 100644
--- a/test.py
+++ b/test.py
@@ -5,6 +5,7 @@
 line 5
 line 6
 line 7
+line 8 (new)
 line 9
 line 10
 line 11
@@ -15,5 +16,6 @@
 line 15
 line 16
-line 17 (deleted)
 line 18
+line 19 (new)
 line 20"""

        result = analyzer._parse_unified_diff(diff_text)

        assert "test.py" in result
        # Line 8 was added at position 8
        assert 8 in result["test.py"]
        # Line 19 was added (after deletion on line 17)
        assert 19 in result["test.py"]

    def test_parse_diff_multiple_files(self) -> None:
        """Test parsing diff with multiple files."""
        analyzer = GitAnalyzer(".")

        diff_text = """diff --git a/file1.py b/file1.py
index 1234567..abcdefg 100644
--- a/file1.py
+++ b/file1.py
@@ -1,3 +1,4 @@
+new line 1
 line 1
 line 2
 line 3
diff --git a/file2.py b/file2.py
index 2345678..bcdefgh 100644
--- a/file2.py
+++ b/file2.py
@@ -5,2 +5,3 @@
 line 5
+new line 6
 line 7"""

        result = analyzer._parse_unified_diff(diff_text)

        assert len(result) == 2
        assert "file1.py" in result
        assert "file2.py" in result
        assert 1 in result["file1.py"]
        assert 6 in result["file2.py"]

    def test_parse_diff_new_file(self) -> None:
        """Test parsing diff for a completely new file."""
        analyzer = GitAnalyzer(".")

        diff_text = """diff --git a/newfile.py b/newfile.py
new file mode 100644
index 0000000..abcdefg
--- /dev/null
+++ b/newfile.py
@@ -0,0 +1,3 @@
+def hello():
+    print("hello")
+    return True"""

        result = analyzer._parse_unified_diff(diff_text)

        assert "newfile.py" in result
        # All lines are new
        assert len(result["newfile.py"]) == 3
        assert result["newfile.py"] == {1, 2, 3}

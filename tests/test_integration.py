"""Integration tests for the full blame tracker workflow."""

import tempfile
from pathlib import Path

import pytest

from blame_tracker.core.blame_tracker import BlamTracker
from blame_tracker.core.cobertura_parser import CoberturaParser
from blame_tracker.core.git_analyzer import GitAnalyzer


class TestIntegration:
    """Integration tests for the complete workflow."""

    def test_full_workflow(self, tmp_path: Path) -> None:
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

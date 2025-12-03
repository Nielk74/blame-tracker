"""Tests for Cobertura parser."""

import tempfile
from pathlib import Path

import pytest

from blame_tracker.core.cobertura_parser import CoberturaParser
from blame_tracker.models import LineStatus


class TestCoberturaParser:
    """Tests for CoberturaParser."""

    def test_parse_simple_coverage(self) -> None:
        """Test parsing a simple Cobertura file."""
        xml_content = """<?xml version="1.0" ?>
<coverage version="5.4" timestamp="1234567890" lines-valid="10" lines-covered="5">
    <packages>
        <package name="src" line-rate="0.5">
            <classes>
                <class name="main" filename="src/main.py" line-rate="0.5">
                    <methods/>
                    <lines>
                        <line number="1" hits="1"/>
                        <line number="2" hits="0"/>
                        <line number="3" hits="1"/>
                        <line number="4" hits="0"/>
                        <line number="5" hits="1"/>
                    </lines>
                </class>
            </classes>
        </package>
    </packages>
</coverage>"""

        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".xml",
            delete=False,
        ) as f:
            f.write(xml_content)
            temp_path = f.name

        try:
            parser = CoberturaParser(temp_path)
            coverage_data = parser.parse()

            assert "src/main.py" in coverage_data
            file_coverage = coverage_data["src/main.py"]
            assert len(file_coverage.lines) == 5

            uncovered = file_coverage.get_uncovered_lines()
            assert uncovered == {2, 4}

            covered = file_coverage.get_covered_lines()
            assert covered == {1, 3, 5}

        finally:
            Path(temp_path).unlink()

    def test_parse_file_not_found(self) -> None:
        """Test parsing non-existent file."""
        parser = CoberturaParser("/non/existent/file.xml")
        with pytest.raises(FileNotFoundError):
            parser.parse()

    def test_parse_malformed_xml(self) -> None:
        """Test parsing malformed XML."""
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".xml",
            delete=False,
        ) as f:
            f.write("<coverage>invalid xml")
            temp_path = f.name

        try:
            parser = CoberturaParser(temp_path)
            with pytest.raises(Exception):
                parser.parse()

        finally:
            Path(temp_path).unlink()

    def test_parse_multiple_files(self) -> None:
        """Test parsing coverage with multiple files."""
        xml_content = """<?xml version="1.0" ?>
<coverage version="5.4" timestamp="1234567890">
    <packages>
        <package name="src">
            <classes>
                <class name="main" filename="src/main.py">
                    <lines>
                        <line number="1" hits="1"/>
                        <line number="2" hits="0"/>
                    </lines>
                </class>
                <class name="utils" filename="src/utils.py">
                    <lines>
                        <line number="1" hits="1"/>
                    </lines>
                </class>
            </classes>
        </package>
    </packages>
</coverage>"""

        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".xml",
            delete=False,
        ) as f:
            f.write(xml_content)
            temp_path = f.name

        try:
            parser = CoberturaParser(temp_path)
            coverage_data = parser.parse()

            assert len(coverage_data) == 2
            assert "src/main.py" in coverage_data
            assert "src/utils.py" in coverage_data

        finally:
            Path(temp_path).unlink()

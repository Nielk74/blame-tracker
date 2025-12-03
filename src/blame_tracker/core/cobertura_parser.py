"""Parser for Cobertura XML coverage format."""

from pathlib import Path
from typing import Dict, List

from lxml import etree

from blame_tracker.models import FileCoverage, LineInfo, LineStatus


class CoberturaParser:
    """Parse Cobertura XML coverage files."""

    def __init__(self, coverage_file: str) -> None:
        """Initialize parser with coverage file path.

        Args:
            coverage_file: Path to Cobertura XML file
        """
        self.coverage_file = Path(coverage_file)

    def parse(self) -> Dict[str, FileCoverage]:
        """Parse coverage file and return coverage data by file.

        Returns:
            Dictionary mapping file paths to FileCoverage objects

        Raises:
            FileNotFoundError: If coverage file doesn't exist
            etree.XMLSyntaxError: If XML is malformed
        """
        if not self.coverage_file.exists():
            raise FileNotFoundError(f"Coverage file not found: {self.coverage_file}")

        tree = etree.parse(str(self.coverage_file))
        root = tree.getroot()

        coverage_by_file: Dict[str, FileCoverage] = {}

        # Iterate through all class elements
        for class_elem in root.findall(".//class"):
            file_path = class_elem.get("filename")
            if not file_path:
                continue

            file_coverage = FileCoverage(file_path=file_path)

            # Parse line elements
            for line_elem in class_elem.findall("lines/line"):
                try:
                    line_number = int(line_elem.get("number", "0"))
                    hits = int(line_elem.get("hits", "0"))

                    # Determine coverage status
                    if hits > 0:
                        status = LineStatus.COVERED
                    else:
                        # Check if line is branch (partial coverage)
                        branch_rate = line_elem.get("branch-rate")
                        if branch_rate and float(branch_rate) > 0:
                            status = LineStatus.PARTIAL
                        else:
                            status = LineStatus.UNCOVERED

                    line_info = LineInfo(
                        line_number=line_number,
                        status=status,
                        hits=hits,
                    )
                    file_coverage.lines.append(line_info)

                except (ValueError, AttributeError):
                    continue

            if file_coverage.lines:
                coverage_by_file[file_path] = file_coverage

        return coverage_by_file

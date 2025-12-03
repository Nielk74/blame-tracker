"""Parser for Cobertura XML coverage format."""

from pathlib import Path
from typing import Dict, List, Optional

from lxml import etree

from blame_tracker.models import FileCoverage, LineInfo, LineStatus


class CoberturaParser:
    """Parse Cobertura XML coverage files."""

    def __init__(self, coverage_file: str, repo_root: Optional[str] = None) -> None:
        """Initialize parser with coverage file path.

        Args:
            coverage_file: Path to Cobertura XML file
            repo_root: Root of repository (for normalizing absolute paths).
                      If None, will use directory containing coverage_file.
        """
        self.coverage_file = Path(coverage_file)

        # Auto-detect repo root if not provided
        if repo_root is None:
            # Use the directory containing the coverage file as repo root
            repo_root = str(self.coverage_file.parent)

        self.repo_root = Path(repo_root).resolve()

    def _normalize_path(self, file_path: str) -> str:
        """Normalize file path to be relative to repo root.

        Handles both absolute and relative paths, converting Windows paths
        to Unix-style paths for consistency with git.

        Args:
            file_path: File path from Cobertura XML (may be absolute or relative)

        Returns:
            Normalized relative path using forward slashes
        """
        path = Path(file_path)

        # If absolute path, try to make it relative to repo_root
        if path.is_absolute():
            try:
                relative = path.relative_to(self.repo_root)
                return str(relative).replace("\\", "/")
            except ValueError:
                # Path is not under repo_root, just use the filename
                return path.name

        # Already relative, just normalize slashes
        return str(path).replace("\\", "/")

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

            # Prepend workspace prefix if not already present
            if not file_path.startswith("C:\\workspace\\"):
                file_path = "C:\\workspace\\" + file_path

            # Normalize path to be relative to repo root
            file_path = self._normalize_path(file_path)

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

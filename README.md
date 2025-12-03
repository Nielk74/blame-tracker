# Blame Tracker

Find which recent commits likely **broke your tests**.

This tool identifies uncovered code (coverage gaps) that were recently modified, helping you quickly identify the culprit commits that introduced test failures.

## Features

- **Coverage Gap Detection**: Parse Cobertura XML to find uncovered code
- **Git Blame Integration**: Identify which commits changed the uncovered code
- **Multithreaded Analysis**: Fast processing with configurable worker threads
- **Smart Line Grouping**: Groups consecutive uncovered lines with 5 lines of context before/after
- **Professional Reports**: Beautiful HTML reports showing code with git blame information
- **14+ Language Support**: Syntax highlighting for Python, JavaScript, C++, C#, Java, PHP, Rust, Go, and more

## Installation

### From Source

```bash
# Clone the repository
git clone <repo-url>
cd blame-tracker

# Install in development mode
pip install -e ".[dev]"
```

### Production Install

```bash
pip install .
```

## Usage

### Basic Usage

```bash
blame-tracker coverage.xml /path/to/repo --days 30
```

This will:
1. Parse the Cobertura coverage XML file
2. Analyze git changes from the last 30 days
3. Find intersection of uncovered lines with recent changes
4. Generate an HTML report (`blame_report.html`)

### Advanced Options

```bash
blame-tracker coverage.xml /path/to/repo \
  --days 30 \
  --output my_report.html \
  --workers 8
```

- `--days`: Number of days to look back (default: 30)
- `--output` / `-o`: Output HTML report path (default: blame_report.html)
- `--workers` / `-w`: Number of worker threads for git analysis (default: 4)

## How It Works

### 1. Coverage Parsing
Reads Cobertura XML format and identifies all **uncovered lines** (coverage gaps).

### 2. Git Analysis
- Extracts commits from the specified time period (e.g., last 30 days)
- Uses multithreading to analyze changes in parallel
- Identifies which lines were **added or modified** in each commit
- Shows real-time progress with progress bars

### 3. Blame Intersection
- Finds uncovered lines that were **recently changed**
- Groups consecutive uncovered lines together
- Extracts context: 5 lines before and after each group
- Associates git commit information with each suspicious code block

### 4. HTML Report Generation
Creates a professional report showing:
- **Summary**: Total uncovered lines and how many are recent
- **Top Culprits**: Files with most suspicious recent changes
- **Detailed Blame Groups**: Each uncovered code block with:
  - Context before/after
  - Git blame (author, commit hash, date, message)
  - Syntax-highlighted code
- **Actionable Info**: Quickly identify which commits to investigate

## Project Structure

```
blame-tracker/
├── src/blame_tracker/
│   ├── __init__.py
│   ├── cli.py                 # Command-line interface
│   ├── core/
│   │   ├── blame_tracker.py   # Main orchestrator
│   │   ├── cobertura_parser.py  # Cobertura XML parsing
│   │   ├── git_analyzer.py    # Git change analysis with threading
│   │   └── blame_intersector.py # Intersection logic
│   ├── models/
│   │   └── __init__.py        # Data models
│   └── reporters/
│       └── html_reporter.py   # HTML report generation
├── tests/
│   ├── test_models.py
│   ├── test_cobertura_parser.py
│   └── test_blame_intersector.py
├── pyproject.toml
└── README.md
```

## Architecture Highlights

### Clean Code Practices

- **Type Hints**: Full type annotations for better IDE support and documentation
- **Data Models**: Using dataclasses for type-safe data structures
- **Separation of Concerns**: Each component has a single responsibility
- **No Free Functions**: All logic encapsulated in classes
- **Comprehensive Tests**: Unit tests for all major components

### Performance

- **Multithreading**: Git analysis uses `concurrent.futures.ThreadPoolExecutor`
- **Progress Tracking**: Beautiful progress bars with `tqdm`
- **Efficient Parsing**: Uses `lxml` for fast XML processing
- **Memory Efficient**: Processes files incrementally

### Extensibility

- **Language Detection**: Automatically detects programming language for syntax highlighting
- **Modular Design**: Easy to add new reporters or analysis modules
- **Configurable**: Command-line options for flexibility

## Dependencies

- **pygments**: Syntax highlighting
- **jinja2**: HTML templating
- **tqdm**: Progress bars
- **GitPython**: Git operations
- **lxml**: XML parsing

## Development

### Running Tests

```bash
pytest
pytest --cov=src/blame_tracker tests/
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint
ruff check src/ tests/

# Type checking
mypy src/
```

## Example Output

The HTML report includes:
- **Summary Cards**: Total uncovered lines, culprits, and percentages
- **Top Culprits Section**: Files with the most recent uncovered lines
- **Detailed Analysis**: Each file with its blame groups
- **Code Display**: Syntax-highlighted code with context
- **Blame Information**: Author, commit hash, date, and message for each change

## Supported Languages

The reporter provides syntax highlighting for:
- Python (.py)
- JavaScript (.js)
- TypeScript (.ts, .tsx)
- C++ (.cpp, .cc, .cxx, .h, .hpp)
- C# (.cs)
- PHP (.php)
- Rust (.rs)
- Go (.go)
- Java (.java)
- C (.c)
- Swift (.swift)
- Kotlin (.kt)
- Ruby (.rb)
- Bash (.sh, .bash)

## License

MIT

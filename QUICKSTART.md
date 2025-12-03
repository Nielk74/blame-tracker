# Blame Tracker - Quick Start Guide

## Installation

```bash
cd /home/antoine/projects/blame-tracker
source venv/bin/activate
pip install -e .
```

## Basic Usage

```bash
# Analyze your repository
blame-tracker coverage.xml /path/to/repo --days 30

# This generates: blame_report.html
```

## Understanding the Report

The HTML report shows:

1. **Summary Cards** - Quick metrics overview
   - Total uncovered lines in your codebase
   - How many were recently changed ("culprits")
   - Percentage of uncovered lines that are recent

2. **Top Culprits** - Files needing testing attention
   - Files with most uncovered recent changes
   - Sorted by impact

3. **Detailed Analysis** - Deep dive per file
   - Code with syntax highlighting
   - 5 lines of context before and after
   - Git blame info (author, commit, date)
   - Makes it easy to find the culprit commit

## Command-Line Options

```bash
blame-tracker <coverage_file> <repo_path> [OPTIONS]

Options:
  --days DAYS              Days to look back (default: 30)
  --output FILE, -o        Output HTML file (default: blame_report.html)
  --workers N, -w          Worker threads (default: 4)
  --help, -h               Show help
```

## Examples

### Last week's changes only
```bash
blame-tracker coverage.xml . --days 7 -o recent.html
```

### Faster analysis with more workers
```bash
blame-tracker coverage.xml . --days 30 --workers 8
```

### Last 24 hours
```bash
blame-tracker coverage.xml . --days 1 -o today.html
```

## Workflow

### 1. Generate Coverage
```bash
# With your test framework (e.g., pytest)
pytest --cov=src --cov-report=xml
```

### 2. Run Blame Tracker
```bash
blame-tracker coverage.xml . --days 30 -o blame.html
```

### 3. Review Report
```bash
# Open in browser
open blame.html  # macOS
xdg-open blame.html  # Linux
start blame.html  # Windows
```

### 4. Take Action
- Identify files with high culprit percentages
- Review commits for new code
- Add tests for uncovered lines
- Track testing coverage over time

## CI/CD Integration

### GitHub Actions Example
```yaml
- name: Generate blame report
  run: |
    pip install blame-tracker
    blame-tracker coverage.xml . --days 30 -o blame_report.html

- name: Upload artifact
  uses: actions/upload-artifact@v3
  with:
    name: blame-report
    path: blame_report.html
```

### GitLab CI Example
```yaml
blame_report:
  script:
    - pip install blame-tracker
    - blame-tracker coverage.xml . --days 30 -o blame_report.html
  artifacts:
    paths:
      - blame_report.html
```

## Interpreting Culprit Percentage

| Percentage | Meaning |
|------------|---------|
| 0% | No recent code is uncovered - great! |
| 1-25% | Good - most recent code is tested |
| 25-50% | Warning - significant recent code untested |
| 50-75% | Alert - most recent code untested |
| 75%+ | Critical - almost all new code is untested |

## Tips

1. **Use shorter lookback for quick feedback**
   - Daily: `--days 1` - what did we add today?
   - Weekly: `--days 7` - weekly coverage review
   - Monthly: `--days 30` - project assessment

2. **More workers for large repos**
   - Small repos: `--workers 2-4`
   - Large repos: `--workers 8-12`

3. **Regular reports**
   - Schedule daily/weekly in CI/CD
   - Track trends over time
   - Identify patterns

4. **Context helps debugging**
   - 5 lines before/after provides context
   - Look at commit messages in report
   - Find what changed with git blame

## Troubleshooting

### "Coverage file not found"
```bash
# Make sure coverage file exists
ls coverage.xml
# If not, generate it with your test framework
pytest --cov=src --cov-report=xml
```

### "Not a git repository"
```bash
# Make sure you're in a git repo
git status
```

### "No coverage gaps found"
Congratulations! All code is tested. Report will be generated with 0 culprits.

### "Report generation slow"
- Use `--workers 8` or more
- Reduce `--days` to narrow scope
- Larger repos take longer naturally

## Example Output Structure

```
blame_report.html
├── Header (title, description)
├── Summary Cards
│   ├── Total uncovered lines
│   ├── Culprit lines
│   ├── Culprit percentage
│   └── Analysis parameters
├── Top Culprits Section
│   ├── Top 10 files by impact
│   └── Statistics per file
├── Detailed Analysis Section
│   ├── Per-file breakdown
│   └── For each file:
│       ├── Coverage statistics
│       └── Blame groups (uncovered code)
│           ├── Context before
│           ├── Culprit lines (highlighted)
│           ├── Context after
│           └── Git information
└── Footer (generation date, metrics)
```

## Testing Locally

```bash
# Run all tests
source venv/bin/activate
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src/blame_tracker

# Test specific module
pytest tests/test_models.py -v
```

## What's Next?

1. Generate your first report
2. Identify files with high culprit percentages
3. Review and add tests for uncovered code
4. Integrate into your CI/CD pipeline
5. Track improvements over time

## Support

For detailed information:
- See `README.md` for full documentation
- See `IMPLEMENTATION.md` for architecture details
- Review docstrings in source code: `src/blame_tracker/**/*.py`

---

**Happy Testing!** 🧪

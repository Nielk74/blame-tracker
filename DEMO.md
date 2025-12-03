# Blame Tracker - Live Demonstration

## Problem Statement

Your unit tests are failing. You need to find **which recent commit broke them**.

Traditional approach:
```bash
$ pytest
FAILED test_main.py::test_divide_by_zero - ValueError: Cannot divide by zero
```

Then you search git history manually... and it takes hours!

## Solution: Blame Tracker

Blame Tracker finds the culprit **automatically**.

## How It Works

### Step 1: Generate Coverage Report (After Tests Fail)

```bash
# Run pytest with coverage - this shows what's NOT tested
pytest --cov=. --cov-report=xml coverage.xml
```

Result: `coverage.xml` shows which lines are **not covered by tests**.

### Step 2: Run Blame Tracker

```bash
blame-tracker coverage.xml . --days 7 -o report.html
```

This:
1. Parses coverage.xml → finds **uncovered lines** (gaps)
2. Analyzes git history (last 7 days) → finds **recently changed lines**
3. **Intersects** them → finds **uncovered lines that were recently changed**
4. Generates **HTML report** with git blame info

### Step 3: Review Report

Open `report.html` and you'll see:

```
📊 ANALYSIS SUMMARY
Total uncovered lines: 3
Culprit lines: 3
Culprit percentage: 100.0%

🔍 DETAILED ANALYSIS
main.py
├── Lines 8-10 are uncovered
├── Author: Test Developer
├── Commit: 8026fc1
├── Date: 2025-12-03
└── Message: BUG: Remove zero check from divide - BREAKS test_divide_by_zero
```

**Result:** You found the breaking commit in seconds!

## Live Example

### Create Test Repository

```bash
# Run the example script
bash examples/create_test_repo.sh

# This creates a test repo with:
# - Commit 1: Initial working code with tests
# - Commit 2: Add square() function (good)
# - Commit 3: Break divide() by removing zero check (BAD!)
# - coverage.xml showing divide() uncovered
```

### Run Blame Tracker

```bash
cd test_repo
blame-tracker coverage.xml . --days 7 -o report.html
open report.html
```

### What You'll See

The report shows:

1. **Summary**: 3 uncovered lines, 100% are recent
2. **Top Culprits**: main.py with all 3 lines
3. **Detailed Analysis**:
   ```
   Lines 8-10
   Author: Test Developer
   Commit: 8026fc1
   Date: 2025-12-03
   Message: BUG: Remove zero check from divide - BREAKS test_divide_by_zero

   Code:
   ┌─ def divide(a, b):
   │     """Divide two numbers - BROKEN."""
   │     # Someone removed the zero check!
   │     return a / b  ← CULPRIT!
   └─
   ```

## Real-World Usage

### Scenario: CI/CD Pipeline

```bash
#!/bin/bash

# Run tests
pytest --cov=src --cov-report=xml coverage.xml

if [ $? -ne 0 ]; then
    echo "Tests failed! Finding culprit..."

    # Generate blame report
    blame-tracker coverage.xml . --days 3 -o blame_report.html

    # Upload report to CI artifact
    cp blame_report.html build/

    echo "Blame report generated: build/blame_report.html"
    exit 1
fi
```

### Scenario: Local Development

```bash
# After test failure
$ pytest
FAILED tests/test_main.py::test_divide_by_zero

# Quick blame
$ blame-tracker coverage.xml . --days 1 -o report.html && open report.html

# ✓ Immediately see: "Commit X broke divide()"
```

## Understanding the Output

### Summary Cards

- **Total Uncovered Lines**: All lines not covered by tests
- **Culprit Lines**: Of those, how many were recently changed?
- **Culprit Percentage**: Percentage = (Culprit Lines / Total Uncovered) × 100%

### Blame Groups

Each group shows:

1. **Line Range**: e.g., "Lines 8-10"
2. **Context Before**: 5 lines before the problem (helps understand context)
3. **Culprit Code**: The actual uncovered lines (highlighted in red)
4. **Context After**: 5 lines after (helps understand context)
5. **Git Blame**:
   - Author name
   - Commit hash (short)
   - Commit date
   - Commit message

### Interpretation

```
Lines 8-10 with 100% culprit percentage
└── All 3 uncovered lines were recently changed
└── These changes LIKELY BROKE THE TESTS
└── Investigate this commit!
```

## Key Insight

The tool doesn't just show **which code is uncovered**.

It shows **which RECENTLY CHANGED code is uncovered**.

This is the **smoking gun** for broken tests!

### Before Blame Tracker
```
$ git log --oneline | head -20
8026fc1 BUG: Remove zero check from divide
53f8649 Feature: Add square function
abc1234 Feature: Add multiply function
...
# Which one broke tests?? Hours of searching...
```

### With Blame Tracker
```
$ blame-tracker coverage.xml . --days 7 -o report.html
✓ Found 3 uncovered lines modified in commit 8026fc1
✓ That's the culprit!
```

## Parameters

- `--days N`: Look back N days (default: 30)
  - Use `--days 1` for recent failures
  - Use `--days 30` for deeper investigation

- `--workers N`: Use N worker threads (default: 4)
  - More workers = faster for large repos
  - `--workers 8` for repos with 1000+ commits

- `--output FILE`: Save report to this path (default: blame_report.html)

## Tips

1. **Run immediately after test failure**
   - Before more commits are made
   - Use `--days 1` for narrow scope

2. **Look at git commit message**
   - "WIP: experimenting..." = suspicious
   - "Fix bug in divide()" = likely culprit

3. **Check the code diff**
   ```bash
   git show <commit_hash>  # See what changed
   ```

4. **Verify with git blame**
   ```bash
   git blame main.py | grep "divide"  # See line-by-line authors
   ```

## Success Criteria

When blame-tracker shows:
- ✓ Files with high culprit percentage
- ✓ Recent git commits
- ✓ Clear code context

**You've found your culprit! Fix that commit and tests will pass.**

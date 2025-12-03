# Blame Tracker - Testing & Verification

## How to Test the Tool

### Option 1: Test with Current Repository

The blame-tracker repository itself has a test module that demonstrates the tool working:

```bash
# Run blame tracker on the current repo
blame-tracker coverage_test.xml . --days 30 -o blame_report.html
```

This will:
1. Parse `coverage_test.xml` (which references `src/blame_tracker/test_module.py`)
2. Analyze git changes in the last 30 days
3. Find that `src/blame_tracker/test_module.py` was changed recently
4. Detect 11 uncovered lines in that file
5. Generate an HTML report showing all 11 lines as "culprits"

**Expected Results:**
```
✓ Found 23 files with recent changes
✓ Found 1 files with culprit uncovered lines
✓ Culprit lines: 11
✓ Culprit percentage: 100.0%
```

### Option 2: Create Your Own Test Repository

```bash
#!/bin/bash

# Create test directory
mkdir /tmp/test_repo && cd /tmp/test_repo
git init
git config user.email "test@example.com"
git config user.name "Test User"

# Commit 1: Initial code
cat > main.py << 'EOF'
def hello():
    print("hello")
    return True

def world():
    print("world")
    return False
EOF

git add main.py
git commit -m "Initial code"

# Commit 2: Add new function (THIS WILL BE UNCOVERED)
cat > main.py << 'EOF'
def hello():
    print("hello")
    return True

def world():
    print("world")
    return False

def new_function():
    x = 1
    y = 2
    z = 3
    return x + y + z
EOF

git add main.py
git commit -m "Add new_function"

# Create coverage file marking new function as uncovered
cat > coverage.xml << 'EOF'
<?xml version="1.0" ?>
<coverage version="5.4" timestamp="1701619200">
    <packages>
        <package name=".">
            <classes>
                <class name="main" filename="main.py">
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
</coverage>
EOF

# Run blame tracker
blame-tracker coverage.xml . --days 30 -o report.html

# Should show:
# ✓ Found 1 file with culprit uncovered lines
# ✓ Culprit lines: 8
# ✓ Culprit percentage: 100.0%
```

## Test Suite

Run all tests:

```bash
pytest tests/ -v
```

The test suite includes:

### Unit Tests (26 tests)
- **test_models.py** (16 tests): Data structure integrity
- **test_cobertura_parser.py** (4 tests): XML parsing
- **test_blame_intersector.py** (6 tests): Line intersection logic

### Integration Tests (8 tests)
- **test_full_workflow_with_real_git_repo**: Creates git repo, commits code, runs full analysis
- **test_git_analyzer_detects_real_changes**: Tests git change detection
- **test_parse_unified_diff**: Tests diff parsing accuracy
- And more...

**All 34 tests pass:**
```
============================= 34 passed in 0.13s ==============================
```

## Understanding the Output

When you run blame-tracker, you'll see:

```
🚀 Starting blame tracker analysis...
   Coverage file: coverage_test.xml
   Repository: .
   Lookback period: 30 days

📁 Parsing coverage file: coverage_test.xml
✓ Found coverage data for 1 files

📊 Analyzing git changes (last 30 days)
Analyzing git changes: 100%|██████████| 7/7 [00:00<00:00, 1962.05commit/s]
✓ Found 23 files with recent changes

🔍 Intersecting coverage with recent changes
Intersecting coverage with changes: 100%|█████| 1/1
✓ Found 1 files with culprit uncovered lines

📝 Generating HTML report: blame_report.html

📊 ANALYSIS SUMMARY
=====================================
Total uncovered lines: 11
Culprit lines: 11
Culprit percentage: 100.0%
✓ Report generated: blame_report.html
```

## HTML Report Features

The generated HTML report shows:

1. **Summary Cards**
   - Total uncovered lines
   - Culprit lines (uncovered in recent changes)
   - Culprit percentage
   - Analysis parameters

2. **Top Culprits Section**
   - Files with most uncovered recent code
   - Quick statistics

3. **Detailed Analysis**
   - Per-file breakdown
   - For each uncovered section:
     - 5 lines of context before
     - Uncovered lines (highlighted in red)
     - 5 lines of context after
     - Git blame information:
       - Author name
       - Commit hash
       - Commit date
       - Commit message

## Key Points to Understand

### Why "Found 0 files with recent changes"?

This happens when:
1. The coverage XML references files that don't exist in the git repo
2. Those files were never modified in the time period specified

**Solution:** Make sure coverage file paths match actual repository file paths.

### File Path Matching

Coverage file references files with their repository relative paths:

```xml
<class name="module" filename="src/main.py">
```

Git analyzer detects changes in those same paths:

```python
git.diff() -> "src/main.py: 10 lines changed"
```

If they don't match, there's no intersection!

## Verification Checklist

- [x] Git analyzer correctly extracts changed lines
- [x] Coverage parser correctly identifies uncovered lines
- [x] Intersection logic finds matching files
- [x] HTML reports generate with all details
- [x] Blame information is accurate
- [x] All 34 tests pass
- [x] Works with real repositories
- [x] Works with synthetic test repositories

## Troubleshooting

### Problem: Still getting 0 files with changes

1. Check coverage file path references actual files:
   ```bash
   ls -la path/to/files
   ```

2. Verify git has changes in those files:
   ```bash
   git log --oneline --follow path/to/file
   ```

3. Check commit dates are within lookback period:
   ```bash
   git log --since="30 days ago" --oneline
   ```

### Problem: Report is empty

This is correct! It means:
- All uncovered lines are OLD (not in recent changes)
- No testing deficiency in recent code

This is actually a good thing - it means your recent commits are well-tested!

## Performance

- Small repos (< 100 commits): < 1 second
- Medium repos (< 1000 commits): 1-5 seconds
- Large repos: Use `--days` to narrow scope or `--workers` to increase threads

```bash
# For large repos, reduce lookback period
blame-tracker coverage.xml . --days 7 --workers 8
```

#!/bin/bash

# Script to create a test repository with realistic code and test failures
# This demonstrates how blame-tracker finds which commits broke tests

set -e

REPO_DIR="${1:-.}/test_repo"
echo "Creating test repository at: $REPO_DIR"

mkdir -p "$REPO_DIR"
cd "$REPO_DIR"

# Initialize git
git init
git config user.email "developer@example.com"
git config user.name "Test Developer"

# ============================================================================
# Commit 1: Initial working code with tests
# ============================================================================
echo "Commit 1: Initial working code..."

cat > main.py << 'PYEOF'
def add(a, b):
    """Add two numbers."""
    return a + b

def multiply(a, b):
    """Multiply two numbers."""
    return a * b

def divide(a, b):
    """Divide two numbers."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
PYEOF

cat > test_main.py << 'PYEOF'
import pytest
from main import add, multiply, divide

def test_add():
    assert add(2, 3) == 5
    assert add(-1, 1) == 0

def test_multiply():
    assert multiply(2, 3) == 6
    assert multiply(0, 5) == 0

def test_divide():
    assert divide(10, 2) == 5
    assert divide(8, 4) == 2

def test_divide_by_zero():
    with pytest.raises(ValueError):
        divide(10, 0)
PYEOF

git add main.py test_main.py
git commit -m "Initial: Add math functions with tests"

# ============================================================================
# Commit 2: Add new function (GOOD - with tests)
# ============================================================================
echo "Commit 2: Add square function with tests..."

cat > main.py << 'PYEOF'
def add(a, b):
    """Add two numbers."""
    return a + b

def multiply(a, b):
    """Multiply two numbers."""
    return a * b

def divide(a, b):
    """Divide two numbers."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

def square(a):
    """Return square of a number."""
    return a * a
PYEOF

cat > test_main.py << 'PYEOF'
import pytest
from main import add, multiply, divide, square

def test_add():
    assert add(2, 3) == 5
    assert add(-1, 1) == 0

def test_multiply():
    assert multiply(2, 3) == 6
    assert multiply(0, 5) == 0

def test_divide():
    assert divide(10, 2) == 5
    assert divide(8, 4) == 2

def test_divide_by_zero():
    with pytest.raises(ValueError):
        divide(10, 0)

def test_square():
    assert square(3) == 9
    assert square(-2) == 4
PYEOF

git add main.py test_main.py
git commit -m "Feature: Add square function with tests"

# ============================================================================
# Commit 3: Modify divide function (BAD - breaks test, code not covered)
# ============================================================================
echo "Commit 3: Modify divide - BREAKS TESTS..."

cat > main.py << 'PYEOF'
def add(a, b):
    """Add two numbers."""
    return a + b

def multiply(a, b):
    """Multiply two numbers."""
    return a * b

def divide(a, b):
    """Divide two numbers - BROKEN."""
    # Someone removed the zero check!
    return a / b

def square(a):
    """Return square of a number."""
    return a * a
PYEOF

# Note: test_main.py not updated, so test_divide_by_zero will fail

git add main.py
git commit -m "BUG: Remove zero check from divide - BREAKS test_divide_by_zero"

# ============================================================================
# Create Coverage File
# ============================================================================
echo "Creating coverage.xml..."

cat > coverage.xml << 'XMLEOF'
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
                        <line number="4" hits="1"/>
                        <line number="5" hits="1"/>
                        <line number="6" hits="1"/>
                        <line number="7" hits="1"/>
                        <line number="8" hits="0"/>
                        <line number="9" hits="0"/>
                        <line number="10" hits="0"/>
                        <line number="11" hits="1"/>
                        <line number="12" hits="1"/>
                        <line number="13" hits="1"/>
                        <line number="14" hits="1"/>
                    </lines>
                </class>
            </classes>
        </package>
    </packages>
</coverage>
XMLEOF

git add coverage.xml
git commit -m "Coverage report - shows divide() is now uncovered"

echo ""
echo "✓ Test repository created at: $REPO_DIR"
echo ""
echo "To analyze with blame-tracker:"
echo "  cd $REPO_DIR"
echo "  blame-tracker coverage.xml . --days 7 -o report.html"
echo ""
echo "Expected result:"
echo "  - Found 3 lines uncovered in main.py (lines 8-10)"
echo "  - All 3 lines were modified in commit 3"
echo "  - Report shows: 'BUG: Remove zero check' - THIS BROKE THE TESTS!"

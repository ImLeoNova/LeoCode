#!/bin/bash
#
# Final verification - runs quick tests to confirm everything works
#

set -e

cd "$(dirname "$0")"

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                 LEOCODE TESTING - VERIFICATION                 ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check 1: Files exist
echo "[1/5] Checking test files..."
files=(
    "tests/__init__.py"
    "tests/test_unit.py"
    "tests/test_agent_real.py"
    "tests/test_interactive.py"
    "run_tests.sh"
    "demo_tests.sh"
    "TESTING.md"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✓ $file"
    else
        echo "  ✗ $file - MISSING"
        exit 1
    fi
done

# Check 2: Scripts are executable
echo ""
echo "[2/5] Checking permissions..."
for script in run_tests.sh demo_tests.sh tests/test_unit.py tests/test_agent_real.py tests/test_interactive.py; do
    if [ -x "$script" ]; then
        echo "  ✓ $script is executable"
    else
        echo "  ✗ $script is not executable"
        chmod +x "$script"
        echo "    → Fixed: chmod +x $script"
    fi
done

# Check 3: 9Router connection
echo ""
echo "[3/5] Checking 9Router connection..."
if curl -s -f "http://localhost:20128/v1/models" > /dev/null 2>&1; then
    echo "  ✓ 9Router is accessible"
else
    echo "  ✗ 9Router not running at http://localhost:20128/v1"
    echo "    Note: Real agent tests require 9Router to be running"
fi

# Check 4: Run unit tests
echo ""
echo "[4/5] Running unit tests..."
if python3 tests/test_unit.py > /dev/null 2>&1; then
    echo "  ✓ Unit tests passed"
else
    echo "  ✗ Unit tests failed"
    exit 1
fi

# Check 5: Test list
echo ""
echo "[5/5] Checking test suite..."
count=$(python3 tests/test_agent_real.py --list 2>/dev/null | grep -c "^  [0-9]" || echo "0")
if [ "$count" -gt 0 ]; then
    echo "  ✓ Found $count test cases"
else
    echo "  ✗ No test cases found"
    exit 1
fi

# Summary
echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                    ✓ VERIFICATION PASSED                       ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "Testing system is ready to use!"
echo ""
echo "Quick commands:"
echo "  ./run_tests.sh --list        # List all tests"
echo "  ./run_tests.sh               # Run all tests"
echo "  ./run_tests.sh -i            # Interactive mode"
echo "  ./demo_tests.sh              # Run demo"
echo "  python3 tests/test_unit.py   # Unit tests only"
echo ""
echo "Documentation:"
echo "  TESTING.md           # Complete testing guide"
echo "  REFACTOR_SUMMARY.md  # What changed"
echo ""

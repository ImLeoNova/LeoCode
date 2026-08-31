#!/bin/bash
#
# Quick demo of the Leocode testing system
#

set -e

cd "$(dirname "$0")"

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║          LEOCODE AGENT TESTING SYSTEM - QUICK DEMO             ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# 1. Unit tests
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 1: Running Unit Tests (Fast, No API)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

python3 tests/test_unit.py

echo ""
echo "Press Enter to continue to real agent tests..."
read

# 2. Real agent test - simple
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 2: Testing Real Agent - Simple Chat"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

python3 tests/test_agent_real.py --test "Simple math"

echo ""
echo "Press Enter to continue to tool calling test..."
read

# 3. Real agent test - tool calling
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 3: Testing Real Agent - Tool Calling"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

python3 tests/test_agent_real.py --test "List directory"

echo ""
echo "Press Enter to continue to multi-step test..."
read

# 4. Complex test
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 4: Testing Real Agent - Multi-Step Task"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

python3 tests/test_agent_real.py --test "Multi-step"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "DEMO COMPLETE!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "What's next?"
echo ""
echo "  1. Run all tests:"
echo "     ./run_tests.sh"
echo ""
echo "  2. Run interactive mode:"
echo "     ./run_tests.sh --interactive"
echo ""
echo "  3. Save results to JSON:"
echo "     ./run_tests.sh --output results.json"
echo ""
echo "  4. See full documentation:"
echo "     cat TESTING.md"
echo ""

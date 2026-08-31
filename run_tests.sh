#!/bin/bash
#
# Leocode Agent Test Runner
# Runs real tests against the agent with actual 9Router responses
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║${NC}                  ${GREEN}LEOCODE AGENT TEST SUITE${NC}                      ${BLUE}║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if virtual environment exists and activate it
if [ -d ".venv" ] && [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    echo -e "${GREEN}✓${NC} Virtual environment activated"
else
    echo -e "${YELLOW}⚠${NC} No virtual environment found, using system Python"
fi

# Parse arguments
MODE="all"
OUTPUT=""
WORKING_DIR="/tmp"

while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--interactive)
            MODE="interactive"
            shift
            ;;
        -l|--list)
            MODE="list"
            shift
            ;;
        -t|--test)
            MODE="single"
            TEST_NAME="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT="$2"
            shift 2
            ;;
        -d|--dir)
            WORKING_DIR="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: ./run_tests.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -i, --interactive         Run interactive testing mode"
            echo "  -l, --list                List available tests"
            echo "  -t, --test NAME           Run specific test"
            echo "  -o, --output FILE         Save results to JSON file"
            echo "  -d, --dir DIR             Set working directory (default: /tmp)"
            echo "  -h, --help                Show this help"
            echo ""
            echo "Examples:"
            echo "  ./run_tests.sh                    # Run all tests"
            echo "  ./run_tests.sh -i                 # Interactive mode"
            echo "  ./run_tests.sh -l                 # List tests"
            echo "  ./run_tests.sh -t 'Basic greeting' # Run specific test"
            echo "  ./run_tests.sh -o results.json    # Save results"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Check 9Router connection
echo -e "${BLUE}[1/3]${NC} Checking 9Router connection..."
if curl -s -f "http://localhost:20128/v1/models" > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} 9Router is running"
else
    echo -e "${RED}✗${NC} 9Router is not accessible at http://localhost:20128/v1"
    echo -e "${YELLOW}  Please start 9Router first${NC}"
    exit 1
fi

# Check configuration
echo -e "${BLUE}[2/3]${NC} Checking configuration..."
if [ -f "$HOME/.config/leocode/config.json" ]; then
    MODEL=$(python3 -c "import json; print(json.load(open('$HOME/.config/leocode/config.json'))['model'])" 2>/dev/null || echo "unknown")
    echo -e "${GREEN}✓${NC} Config found (model: $MODEL)"
else
    echo -e "${YELLOW}⚠${NC} Config not found, using defaults"
fi

# Run tests based on mode
echo -e "${BLUE}[3/3]${NC} Running tests..."
echo ""

case $MODE in
    interactive)
        echo -e "${GREEN}Starting interactive mode...${NC}"
        echo ""
        python3 tests/test_interactive.py -d "$WORKING_DIR"
        ;;
    list)
        python3 tests/test_agent_real.py --list
        ;;
    single)
        python3 tests/test_agent_real.py -d "$WORKING_DIR" -t "$TEST_NAME" ${OUTPUT:+-o "$OUTPUT"}
        ;;
    all)
        if [ -n "$OUTPUT" ]; then
            python3 tests/test_agent_real.py -d "$WORKING_DIR" -o "$OUTPUT"
        else
            python3 tests/test_agent_real.py -d "$WORKING_DIR"
        fi
        ;;
esac

EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║${NC}                    ${GREEN}✓ ALL TESTS PASSED${NC}                         ${GREEN}║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
else
    echo -e "${RED}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║${NC}                    ${RED}✗ SOME TESTS FAILED${NC}                        ${RED}║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════════════════════════╝${NC}"
fi

echo ""
exit $EXIT_CODE

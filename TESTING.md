# Leocode Testing Guide

Comprehensive testing system for the Leocode AI agent with real command-line testing and validation.

## Test Types

### 1. Unit Tests (Fast, Isolated)
Tests individual agent tools without making API calls.

```bash
python3 tests/test_unit.py
```

Tests:
- `read_file` - File reading
- `write_file` - File writing
- `edit_file` - File editing
- `list_dir` - Directory listing
- `run_command` - Shell command execution
- `search_files` - File pattern search
- `search_content` - Content regex search

### 2. Real Agent Tests (Full Integration)
Tests complete agent behavior with actual 9Router API calls.

```bash
# Run all tests
./run_tests.sh

# List available tests
./run_tests.sh --list

# Run specific test
./run_tests.sh --test "Basic greeting"

# Save results to JSON
./run_tests.sh --output results.json

# Use custom working directory
./run_tests.sh --dir /path/to/project
```

Or use Python directly:
```bash
python3 tests/test_agent_real.py
python3 tests/test_agent_real.py --list
python3 tests/test_agent_real.py --test "List directory"
python3 tests/test_agent_real.py --output results.json
```

Test Cases:
- **Basic greeting** - Simple chat without tools
- **Simple math** - Basic reasoning
- **List directory** - Tool calling with `list_dir`
- **Read file** - Tool calling with `read_file`
- **Run command** - Shell command execution
- **Search files** - File pattern matching
- **Multi-step task** - Complex workflow (write + read)
- **Code generation** - Code writing capability

### 3. Interactive Testing
Real-time interactive testing with command-line interface.

```bash
# Start interactive mode
./run_tests.sh --interactive

# Or directly
python3 tests/test_interactive.py
python3 tests/test_interactive.py --dir /path/to/project
```

Commands in interactive mode:
- `/help` - Show help
- `/tools` - Toggle tool calling on/off
- `/clear` - Clear conversation history
- `/info` - Show session information
- `/save` - Save conversation to JSON
- `/exit` - Exit tester

## Quick Start

### 1. Run Unit Tests (No API required)
```bash
cd /run/media/leonova/Leonova/Tafrih/ChatBot
python3 tests/test_unit.py
```

### 2. Run Full Agent Tests (Requires 9Router)
```bash
# Make sure 9Router is running
curl http://localhost:20128/v1/models

# Run tests
./run_tests.sh
```

### 3. Interactive Testing
```bash
./run_tests.sh -i
```

Then type your queries:
```
You: List files in /tmp using list_dir tool
You: Create a Python function that sorts a list
You: /tools  # Toggle tools off
You: What is 2+2?
You: /exit
```

## Test Output

### Console Output
Each test shows:
- Input message
- Tool usage (if applicable)
- Tool execution details
- Agent response
- Validation results
- Duration

Example:
```
======================================================================
TEST: List directory
======================================================================
INPUT: List files in /tmp directory using list_dir tool
TOOLS: Enabled
TIMEOUT: 30s
----------------------------------------------------------------------
REQUESTING...
I'll list the files in the /tmp directory for you.

======================================================================
TOOL CALLS DETECTED
======================================================================

TOOL: list_dir
ARGS: {
  "path": "/tmp"
}
RESULT: d          0 systemd-private-abc/
-       1024 test.txt
...

======================================================================
FOLLOW-UP RESPONSE
======================================================================
Here are the files in /tmp directory. There are 15 files and 3 directories.

======================================================================
VALIDATION
======================================================================
Expected keywords: ['tmp']
Found: ['tmp']
Duration: 2.45s
Result: ✓ PASS
```

### JSON Output
Save structured results:
```bash
./run_tests.sh --output results.json
```

Format:
```json
{
  "summary": {
    "total": 8,
    "passed": 7,
    "failed": 1,
    "success_rate": 87.5,
    "total_duration": 45.23
  },
  "tests": [
    {
      "name": "Basic greeting",
      "input": "Say 'Hello from test'",
      "passed": true,
      "duration": 1.23,
      "result": "Hello from test! How can I help you?",
      "error": null
    }
  ]
}
```

## Writing Custom Tests

Add tests to `tests/test_agent_real.py`:

```python
from tests.test_agent_real import TestCase

# Simple keyword validation
test = TestCase(
    name="My test",
    input_text="Do something",
    expected_keywords=["keyword1", "keyword2"],
    use_tools=True,
)

# Custom validation function
def validate_response(response: str) -> bool:
    return "expected" in response and len(response) > 50

test = TestCase(
    name="Custom validation",
    input_text="Generate code",
    validate_func=validate_response,
    use_tools=False,
    timeout=60,
)
```

Add to test suite in `create_test_suite()` function.

## CI/CD Integration

### Exit Codes
- `0` - All tests passed
- `1` - Some tests failed
- `130` - Interrupted by user

### GitHub Actions Example
```yaml
name: Test Agent
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run unit tests
        run: python3 tests/test_unit.py
      - name: Run agent tests
        run: ./run_tests.sh --output results.json
      - name: Upload results
        uses: actions/upload-artifact@v2
        with:
          name: test-results
          path: results.json
```

## Troubleshooting

### 9Router Not Running
```
✗ 9Router is not accessible at http://localhost:20128/v1
```
**Solution:** Start 9Router before running tests.

### Authentication Failed
```
Error: 401 Unauthorized
```
**Solution:** Check API key in `~/.config/leocode/config.json`

### Tool Not Called
If agent doesn't use tools when expected:
- Check `use_tools=True` in test case
- Verify model supports function calling (use `kr/claude-sonnet-4.5`)
- Make prompt more explicit: "using the list_dir tool"

### Test Timeout
```
✗ TIMEOUT: Timeout after 30s
```
**Solution:** Increase timeout in test case or check model performance.

## Performance Benchmarks

Typical durations:
- **Unit tests**: < 1 second total
- **Basic chat test**: 1-3 seconds
- **Tool calling test**: 2-5 seconds
- **Multi-step test**: 5-10 seconds
- **Full test suite**: 30-60 seconds

## Advanced Usage

### Custom Working Directory
```bash
./run_tests.sh --dir ~/myproject
```

### Filter Tests by Name
```bash
./run_tests.sh --test "tool"  # Runs all tests with "tool" in name
```

### Debug Mode
Add print statements in test code or run with Python debugger:
```bash
python3 -m pdb tests/test_agent_real.py
```

### Parallel Testing
Run multiple test suites in parallel:
```bash
./run_tests.sh --test "Basic" --output results1.json &
./run_tests.sh --test "Tool" --output results2.json &
wait
```

## Test Coverage

Current coverage:
- ✓ Basic chat (no tools)
- ✓ Tool calling (all 7 tools)
- ✓ Multi-turn conversation
- ✓ Streaming responses
- ✓ Error handling
- ✓ File operations
- ✓ Shell commands
- ✓ Code generation

## Support

For issues or questions:
1. Check test output for error details
2. Verify 9Router connection
3. Run unit tests first to isolate issues
4. Use interactive mode for debugging

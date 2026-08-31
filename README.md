# Leocode - AI Coding Agent powered by 9Router

Professional AI coding agent with tool calling, RAG, web search, and MCP support.

## Features

- **9Router Integration**: Access 224+ AI models through a unified OpenAI-compatible API
- **Agent Tools**: File operations, shell commands, code search, directory listing
- **RAG Support**: Retrieval-augmented generation with ChromaDB
- **Web Search**: Built-in web search capabilities
- **MCP Support**: Model Context Protocol for tool integration
- **TUI Interface**: Beautiful terminal UI built with Textual

## Quick Start

### 1. Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Or install as package
pip install -e .
```

### 2. Configuration

The agent is pre-configured to work with 9Router running on `http://localhost:20128/v1`.

**Default settings:**
- Endpoint: `http://localhost:20128/v1`
- API Key: `sk-895537f63fde664f-0vwekv-d61ce87b`
- Model: `kr/claude-sonnet-4.5`

Config is stored at: `~/.config/leocode/config.json`

### 3. Run the Agent

```bash
# Launch the TUI
leocode

# Or run from source
python -m leocode

# Specify working directory
leocode -d /path/to/project

# Override model
leocode -m "kr/auto"
```

## Available 9Router Models

The agent can access 224+ models across multiple providers:

### KR Provider (34 models)
- `kr/auto` - Auto-select best model
- `kr/claude-sonnet-4.5` - Claude Sonnet 4.5 (default)
- `kr/claude-sonnet-4.5-thinking` - With reasoning
- `kr/claude-sonnet-4.5-agentic` - Optimized for agents
- `kr/deepseek-3.2` - DeepSeek reasoning model
- And many more...

### Other Providers
- **kc/** - KiloCode (8 models): Claude, Gemini, GPT, DeepSeek
- **ag/** - AntiGravity (16 models): Gemini Flash variants
- **cl/** - CloudLab (8 models): High-end models
- **groq/** - Groq (4 models): Fast inference
- **xai/** - xAI (4 models): Grok models
- **cerebras/** - Cerebras (6 models): Ultra-fast
- **ds/** - DeepSeek (6 models): Reasoning models
- **ollama/** - Ollama (7 models): Local models
- And more...

## Usage

### Basic Commands

- `/help` - Show help
- `ctrl+n` - New session
- `ctrl+x` - Switch model
- `ctrl+o` - Change agent directory
- `ctrl+f` - Attach file
- `ctrl+r` - Toggle RAG
- `ctrl+w` - Web search
- `ctrl+t` - Settings

### Agent Tools

The agent has access to:
- `read_file` - Read file contents with line numbers
- `write_file` - Write/create files
- `edit_file` - Replace text in files
- `list_dir` - List directory contents
- `run_command` - Execute shell commands
- `search_files` - Find files by glob pattern
- `search_content` - Search file contents with regex

## Examples

### Ask the agent to write code:

```
Create a Python script that fetches weather data from an API
```

### Let the agent explore and modify your codebase:

```
Find all TODO comments in the src/ directory and create issues for them
```

### Use RAG for context-aware responses:

```
Based on the codebase, how is authentication implemented?
```

## Architecture

```
leocode/
├── __main__.py       # CLI entry point
├── app.py            # Main Textual application
├── config.py         # Configuration management
├── client.py         # 9Router API client
├── agent.py          # Agent tools implementation
├── rag.py            # RAG with ChromaDB
├── search.py         # Web search
├── mcp_client.py     # MCP protocol support
├── file_ops.py       # File operations
└── ui/
    ├── widgets.py    # UI components
    └── sidebar.py    # Sidebar layout
```

## Testing

The project includes a comprehensive testing system with real agent validation.

### Quick Start

```bash
# 1. Verify testing system
./verify_tests.sh

# 2. Run unit tests (fast, no API)
python3 tests/test_unit.py

# 3. Run all agent tests (with real 9Router)
./run_tests.sh

# 4. Run specific test
./run_tests.sh --test "Basic greeting"

# 5. Interactive testing mode
./run_tests.sh --interactive

# 6. Save results to JSON
./run_tests.sh --output results.json
```

### Test Types

**Unit Tests** - Fast, isolated tests for agent tools:
- Tests: read_file, write_file, edit_file, list_dir, run_command, search_files, search_content
- Duration: < 1 second

**Real Agent Tests** - Full integration with actual 9Router responses:
- 8 test cases covering chat, tool calling, multi-step tasks, code generation
- Validates actual agent responses against expected outputs
- Duration: 30-60 seconds for full suite

**Interactive Mode** - Command-line interface for manual testing:
- Real-time agent interaction
- Tool calling toggle
- Conversation history
- Save/load sessions

### Example Test Output

```bash
$ ./run_tests.sh --test "Run command"

======================================================================
TEST: Run command
======================================================================
INPUT: Run 'echo test123' using run_command tool
TOOLS: Enabled
----------------------------------------------------------------------
REQUESTING...

======================================================================
TOOL CALLS DETECTED
======================================================================

TOOL: run_command
ARGS: {"command": "echo test123"}
RESULT: test123

======================================================================
FOLLOW-UP RESPONSE
======================================================================
Command executed successfully. Output: `test123`

======================================================================
VALIDATION
======================================================================
Expected keywords: ['test123']
Found: ['test123']
Duration: 6.48s
Result: ✓ PASS
```

### Documentation

- **TESTING.md** - Complete testing documentation
- **REFACTOR_SUMMARY.md** - What was refactored and how it works

### Demo

```bash
./demo_tests.sh  # Step-by-step testing demo
```

## Configuration Options

Edit `~/.config/leocode/config.json`:

```json
{
  "base_url": "http://localhost:20128/v1",
  "api_key": "sk-895537f63fde664f-0vwekv-d61ce87b",
  "model": "kr/claude-sonnet-4.5",
  "temperature": 0.7,
  "max_tokens": 4096,
  "system_prompt": "You are Leocode...",
  "rag_enabled": true,
  "web_search_enabled": true,
  "mcp_enabled": true,
  "agent_mode": true,
  "theme": "dark",
  "mcp_servers": [],
  "rag_chunks": 5,
  "rag_chunk_size": 1000
}
```

## 9Router Best Practices

1. **Use kr/ models for general agent work** - They're optimized for tool calling
2. **Try -agentic variants** - Specifically tuned for autonomous agents
3. **Enable -thinking for complex tasks** - Adds reasoning capabilities
4. **Use kr/auto** - Automatically selects the best model for each request
5. **Check rate limits** - Some free models have usage caps

## Troubleshooting

### Connection Issues
```bash
# Check 9Router is running
curl http://localhost:20128/v1/models

# Test with direct curl
curl -X POST http://localhost:20128/v1/chat/completions \
  -H "Authorization: Bearer sk-895537f63fde664f-0vwekv-d61ce87b" \
  -H "Content-Type: application/json" \
  -d '{"model":"kr/claude-sonnet-4.5","messages":[{"role":"user","content":"Hello"}]}'
```

### Model Not Found
- Verify model ID with: `curl -H "Authorization: Bearer <key>" http://localhost:20128/v1/models`
- Check if model requires credits (kc/ models are paid)

### Rate Limiting
- Switch to a different provider (e.g., kr/ instead of openrouter/)
- Use paid models for higher limits
- Add retry logic with exponential backoff

## License

MIT

## Contributing

Contributions welcome! This is a demonstration project showing how to integrate 9Router with an AI coding agent.

# Leocode - Quick Start Guide

Get your AI coding agent running in 60 seconds!

## Prerequisites

- Python 3.10+
- 9Router running on `http://localhost:20128/v1`
- API Key: `sk-895537f63fde664f-0vwekv-d61ce87b`

## Installation

```bash
# Navigate to project
cd /run/media/leonova/Leonova/Tafrih/ChatBot

# Install dependencies
pip install -r requirements.txt

# Install as package (optional)
pip install -e .
```

## Launch

```bash
# Start the agent
leocode

# Or run from source
python -m leocode
```

## First Steps

1. **The agent will launch in TUI mode** with a beautiful terminal interface
2. **Type your request** in the input box at the bottom
3. **Press Enter** to send your message
4. **The agent will respond** using the kr/claude-sonnet-4.5 model

## Common Tasks

### Switch Models
Press `ctrl+x` to browse 224+ available models

### Attach Files
Press `ctrl+f` and enter a file path

### Change Working Directory
Press `ctrl+o` and enter a directory path

### New Session
Press `ctrl+n` to start fresh

### Help
Press `?` or type `/help`

## Example Interactions

### Code Generation
```
You: Create a Python function to calculate fibonacci numbers

Agent: [Creates the function with proper docstring and tests]
```

### File Operations
```
You: Read the contents of config.py and explain it

Agent: [Uses read_file tool, then explains the configuration]
```

### Shell Commands
```
You: What Python version am I using?

Agent: [Uses run_command to execute `python --version`]
```

### Codebase Analysis
```
You: Find all TODO comments in the project

Agent: [Uses search_content tool with regex pattern]
```

## Configuration

Config file: `~/.config/leocode/config.json`

Change model:
```bash
leocode -m "kr/auto"
```

Change endpoint:
```bash
leocode -u "http://localhost:20128/v1" -k "your-key"
```

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `ctrl+q` | Quit |
| `ctrl+n` | New chat |
| `ctrl+s` | Save chat |
| `ctrl+l` | Clear chat |
| `ctrl+m` | Toggle sidebar |
| `ctrl+o` | Change agent directory |
| `ctrl+f` | Attach file |
| `ctrl+r` | Toggle RAG |
| `ctrl+w` | Web search |
| `ctrl+t` | Settings |
| `ctrl+x` | Switch model |
| `shift+tab` | Cycle focus |
| `?` | Help |

## Available Models

The agent has access to 224+ models. Some highlights:

**Fast & Reliable:**
- `kr/claude-sonnet-4.5` (default)
- `kr/auto` (auto-routing)
- `cerebras/llama-3.3-70b`

**For Agents:**
- `kr/claude-sonnet-4.5-agentic`
- `ag/gemini-3-flash-agent`

**With Reasoning:**
- `kr/claude-sonnet-4.5-thinking`
- `kr/deepseek-3.2-thinking`
- `xai/grok-4-fast-reasoning`

**Free Tier:**
- `bzl/auto:free`
- `openrouter/z-ai/glm-5.2:free` (rate limited)

Press `ctrl+x` to browse all models in the app!

## Troubleshooting

### Can't connect to 9Router
```bash
# Check if 9Router is running
curl http://localhost:20128/v1/models
```

### Model not working
Try a different model:
```bash
leocode -m "kr/auto"
```

### Rate limited
Switch to a paid model or kr/ provider models

### Import errors
```bash
pip install -r requirements.txt
```

## Need Help?

- Full documentation: `README.md`
- Setup details: `SETUP_COMPLETE.md`
- Type `/help` in the agent

---

**Ready!** Run `leocode` to start coding with AI assistance! 🚀

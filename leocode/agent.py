"""Agent system — legacy compatibility wrapper over the new Tool Registry."""

import os
from typing import Optional


class AgentTools:
    """Backward-compatible wrapper. Registers tools via the new registry system."""

    def __init__(self, working_dir: str | None = None):
        self.working_dir = working_dir or os.getcwd()
        self.tool_definitions = [
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Read file contents. Returns the full text of the file.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "File path (absolute or relative to working dir)"},
                            "offset": {"type": "integer", "description": "Line number to start from (0-indexed)", "default": 0},
                            "limit": {"type": "integer", "description": "Max lines to read", "default": 500},
                        },
                        "required": ["path"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "write_file",
                    "description": "Write content to a file. Creates or overwrites.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "File path"},
                            "content": {"type": "string", "description": "Content to write"},
                        },
                        "required": ["path", "content"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "edit_file",
                    "description": "Replace exact string in file.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "File path"},
                            "old": {"type": "string", "description": "Exact string to find"},
                            "new": {"type": "string", "description": "Replacement string"},
                        },
                        "required": ["path", "old", "new"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "list_dir",
                    "description": "List directory contents.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Directory path", "default": "."},
                        },
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "run_command",
                    "description": "Execute a shell command. Use for git, npm, python, etc.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {"type": "string", "description": "Shell command to execute"},
                            "timeout": {"type": "integer", "description": "Timeout in seconds", "default": 30},
                        },
                        "required": ["command"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "search_files",
                    "description": "Search for files by name pattern (glob).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "pattern": {"type": "string", "description": "Glob pattern, e.g. **/*.py"},
                            "path": {"type": "string", "description": "Base directory", "default": "."},
                        },
                        "required": ["pattern"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "search_content",
                    "description": "Search file contents with regex.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "pattern": {"type": "string", "description": "Regex pattern to search"},
                            "path": {"type": "string", "description": "Directory to search in", "default": "."},
                            "include": {"type": "string", "description": "File pattern to include, e.g. *.py"},
                        },
                        "required": ["pattern"],
                    },
                },
            },
        ]

    def _resolve(self, path: str) -> "Path":
        from pathlib import Path
        p = Path(path)
        if not p.is_absolute():
            p = Path(self.working_dir) / p
        return p.resolve()

    def execute(self, tool_name: str, args: dict) -> str:
        try:
            fn = getattr(self, f"_tool_{tool_name}", None)
            if fn:
                return fn(**args)
            return f"Unknown tool: {tool_name}"
        except Exception as e:
            return f"Error: {e}"

    def _tool_read_file(self, path: str, offset: int = 0, limit: int = 500) -> str:
        from pathlib import Path
        p = self._resolve(path)
        if not p.exists():
            return f"File not found: {path}"
        if not p.is_file():
            return f"Not a file: {path}"
        lines = p.read_text(errors="ignore").splitlines()
        selected = lines[offset:offset + limit]
        result = []
        for i, line in enumerate(selected, start=offset + 1):
            result.append(f"{i:>6}\t{line}")
        return "\n".join(result)

    def _tool_write_file(self, path: str, content: str) -> str:
        from pathlib import Path
        p = self._resolve(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        return f"Written {len(content)} bytes to {path}"

    def _tool_edit_file(self, path: str, old: str, new: str) -> str:
        from pathlib import Path
        p = self._resolve(path)
        if not p.exists():
            return f"File not found: {path}"
        text = p.read_text(errors="ignore")
        if old not in text:
            return f"String not found in {path}"
        count = text.count(old)
        new_text = text.replace(old, new, 1)
        p.write_text(new_text)
        return f"Replaced {count} occurrence(s) in {path}"

    def _tool_list_dir(self, path: str = ".") -> str:
        from pathlib import Path
        p = self._resolve(path)
        if not p.exists():
            return f"Directory not found: {path}"
        entries = sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
        result = []
        for entry in entries:
            prefix = "d" if entry.is_dir() else "-"
            size = entry.stat().st_size if entry.is_file() else 0
            name = entry.name + "/" if entry.is_dir() else entry.name
            result.append(f"{prefix} {size:>10} {name}")
        return "\n".join(result)

    def _tool_run_command(self, command: str, timeout: int = 30) -> str:
        import subprocess
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True,
                timeout=timeout, cwd=self.working_dir,
            )
            output = result.stdout
            if result.stderr:
                output += f"\n[stderr]\n{result.stderr}"
            if result.returncode != 0:
                output += f"\n[exit code: {result.returncode}]"
            return output[:10000] if output else "(no output)"
        except subprocess.TimeoutExpired:
            return f"Command timed out after {timeout}s"
        except Exception as e:
            return f"Error: {e}"

    def _tool_search_files(self, pattern: str, path: str = ".") -> str:
        from pathlib import Path
        p = self._resolve(path)
        matches = []
        try:
            for match in p.rglob(pattern):
                if match.is_file():
                    rel = match.relative_to(self.working_dir) if str(self.working_dir) in str(match) else match
                    matches.append(str(rel))
                    if len(matches) >= 100:
                        break
        except Exception:
            pass
        return "\n".join(matches) if matches else "No files found"

    def _tool_search_content(self, pattern: str, path: str = ".", include: str = "") -> str:
        import re
        from pathlib import Path
        p = self._resolve(path)
        try:
            regex = re.compile(pattern)
        except re.error:
            return f"Invalid regex: {pattern}"
        results = []
        glob_pattern = include if include else "**/*"
        for f in p.rglob(glob_pattern):
            if f.is_file() and f.stat().st_size < 1_000_000:
                try:
                    for i, line in enumerate(f.read_text(errors="ignore").splitlines(), 1):
                        if regex.search(line):
                            rel = f.relative_to(self.working_dir) if str(self.working_dir) in str(f) else f
                            results.append(f"{rel}:{i}: {line.strip()}")
                            if len(results) >= 50:
                                return "\n".join(results)
                except Exception:
                    continue
        return "\n".join(results) if results else "No matches found"

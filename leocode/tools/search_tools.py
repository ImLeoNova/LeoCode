"""Search tools — grep (content search) and web search."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .registry import ToolMetadata, ToolCategory, ToolSource, RetryPolicy
from ..permissions import RiskLevel


def register_search_tools(registry, working_dir: str):
    """Register search tools into the registry."""

    async def execute_grep(tool_id: str, args: dict) -> str:
        return _tool_grep(working_dir, args)

    async def execute_search(tool_id: str, args: dict) -> str:
        return await _tool_search(registry, tool_id, args)

    tools = [
        ToolMetadata(
            id="grep",
            name="Grep",
            description="Search file contents using regex patterns across the project.",
            category=ToolCategory.SEARCH,
            input_schema={
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Regex pattern to search"},
                    "path": {"type": "string", "description": "Directory to search in", "default": "."},
                    "include": {"type": "string", "description": "File glob to include (e.g. *.py)"},
                    "max_results": {"type": "integer", "description": "Max results", "default": 50},
                },
                "required": ["pattern"],
            },
            risk_level=RiskLevel.SAFE,
            timeout=15.0,
        ),
        ToolMetadata(
            id="search",
            name="Web Search",
            description="Search the web for information.",
            category=ToolCategory.WEB,
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                },
                "required": ["query"],
            },
            risk_level=RiskLevel.LOW,
            timeout=15.0,
        ),
    ]

    executors = [execute_grep, execute_search]
    for meta, executor in zip(tools, executors):
        registry.register(meta, executor)


def _resolve(working_dir: str, path: str) -> Path:
    p = Path(path)
    if not p.is_absolute():
        p = Path(working_dir) / p
    return p.resolve()


def _tool_grep(working_dir: str, args: dict) -> str:
    pattern = args["pattern"]
    path = _resolve(working_dir, args.get("path", "."))
    include = args.get("include", "")
    max_results = args.get("max_results", 50)

    if not path.exists():
        return f"Error: Directory not found: {args.get('path', '.')}"
    try:
        regex = re.compile(pattern)
    except re.error as e:
        return f"Error: Invalid regex: {e}"

    results = []
    glob_pattern = include if include else "**/*"
    for f in path.rglob(glob_pattern):
        if not f.is_file():
            continue
        try:
            if f.stat().st_size > 1_000_000:
                continue
            for i, line in enumerate(f.read_text(errors="ignore").splitlines(), 1):
                if regex.search(line):
                    rel = str(f.relative_to(Path(working_dir))) if str(Path(working_dir)) in str(f) else str(f)
                    results.append(f"{rel}:{i}: {line.strip()}")
                    if len(results) >= max_results:
                        return f"Found {max_results}+ results (showing first {max_results}):\n" + "\n".join(results)
        except Exception:
            continue

    if not results:
        return f"No matches found for '{pattern}'"
    return f"Found {len(results)} results:\n" + "\n".join(results)


async def _tool_search(registry, tool_id: str, args: dict) -> str:
    """Web search — delegated to the WebSearch instance if available."""
    query = args.get("query", "")
    if not query:
        return "Error: No search query provided"

    search = getattr(registry, "_web_search", None)
    if not search:
        return f"Web search not configured. Query was: {query}"

    try:
        results = await search.search(query)
        if not results:
            return f"No results found for: {query}"
        lines = [f"Search results for: {query}", ""]
        for i, r in enumerate(results, 1):
            title = r.get("title", "N/A")
            url = r.get("url", "")
            snippet = r.get("snippet", "")
            lines.append(f"{i}. {title}")
            lines.append(f"   {url}")
            lines.append(f"   {snippet}")
            lines.append("")
        return "\n".join(lines)
    except Exception as e:
        return f"Search error: {e}"

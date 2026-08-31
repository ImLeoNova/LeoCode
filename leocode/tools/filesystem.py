"""Filesystem tools — read, write, edit, patch, delete, list_dir, glob."""

from __future__ import annotations

import os
import fnmatch
import difflib
import subprocess
from pathlib import Path
from typing import Any

from .registry import ToolMetadata, ToolCategory, ToolSource, RetryPolicy
from ..permissions import RiskLevel


def register_filesystem_tools(registry, working_dir: str):
    """Register all filesystem tools into the registry."""

    async def execute_read(tool_id: str, args: dict) -> str:
        return _tool_read(working_dir, args)

    async def execute_write(tool_id: str, args: dict) -> str:
        return _tool_write(working_dir, args)

    async def execute_edit(tool_id: str, args: dict) -> str:
        return _tool_edit(working_dir, args)

    async def execute_patch(tool_id: str, args: dict) -> str:
        return _tool_patch(working_dir, args)

    async def execute_delete(tool_id: str, args: dict) -> str:
        return _tool_delete(working_dir, args)

    async def execute_list_dir(tool_id: str, args: dict) -> str:
        return _tool_list_dir(working_dir, args)

    async def execute_glob(tool_id: str, args: dict) -> str:
        return _tool_glob(working_dir, args)

    tools = [
        ToolMetadata(
            id="read",
            name="Read",
            description="Read file contents with optional line range. Returns numbered lines.",
            category=ToolCategory.FILESYSTEM,
            input_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path (absolute or relative to working dir)"},
                    "offset": {"type": "integer", "description": "Line to start from (0-indexed)", "default": 0},
                    "limit": {"type": "integer", "description": "Max lines to read", "default": 500},
                },
                "required": ["path"],
            },
            risk_level=RiskLevel.SAFE,
            timeout=10.0,
        ),
        ToolMetadata(
            id="write",
            name="Write",
            description="Create a new file or replace its entire contents.",
            category=ToolCategory.FILESYSTEM,
            input_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path"},
                    "content": {"type": "string", "description": "Content to write"},
                },
                "required": ["path", "content"],
            },
            risk_level=RiskLevel.MEDIUM,
            timeout=10.0,
        ),
        ToolMetadata(
            id="edit",
            name="Edit",
            description="Replace an exact string in an existing file. Use for precise modifications.",
            category=ToolCategory.FILESYSTEM,
            input_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path"},
                    "old_string": {"type": "string", "description": "Exact string to find and replace"},
                    "new_string": {"type": "string", "description": "Replacement string"},
                },
                "required": ["path", "old_string", "new_string"],
            },
            risk_level=RiskLevel.MEDIUM,
            timeout=10.0,
        ),
        ToolMetadata(
            id="patch",
            name="Patch",
            description="Apply a unified diff patch to a file.",
            category=ToolCategory.FILESYSTEM,
            input_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path"},
                    "diff": {"type": "string", "description": "Unified diff content"},
                },
                "required": ["path", "diff"],
            },
            risk_level=RiskLevel.MEDIUM,
            timeout=10.0,
        ),
        ToolMetadata(
            id="delete",
            name="Delete",
            description="Delete a single file. Refuses directories and paths outside the working directory.",
            category=ToolCategory.FILESYSTEM,
            input_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path to delete"},
                },
                "required": ["path"],
            },
            risk_level=RiskLevel.HIGH,
            timeout=10.0,
        ),
        ToolMetadata(
            id="list_dir",
            name="List Directory",
            description="List directory contents with sizes and type indicators.",
            category=ToolCategory.FILESYSTEM,
            input_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path", "default": "."},
                },
            },
            risk_level=RiskLevel.SAFE,
            timeout=10.0,
        ),
        ToolMetadata(
            id="glob",
            name="Glob",
            description="Find files using glob patterns (e.g. **/*.py, src/**/*.ts).",
            category=ToolCategory.FILESYSTEM,
            input_schema={
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Glob pattern"},
                    "path": {"type": "string", "description": "Base directory", "default": "."},
                    "exclude": {"type": "array", "items": {"type": "string"}, "description": "Patterns to exclude"},
                },
                "required": ["pattern"],
            },
            risk_level=RiskLevel.SAFE,
            timeout=10.0,
        ),
    ]

    executors = [execute_read, execute_write, execute_edit, execute_patch, execute_delete, execute_list_dir, execute_glob]
    for meta, executor in zip(tools, executors):
        registry.register(meta, executor)


def _resolve(working_dir: str, path: str) -> Path:
    p = Path(path)
    if not p.is_absolute():
        p = Path(working_dir) / p
    return p.resolve()


def _tool_read(working_dir: str, args: dict) -> str:
    path = _resolve(working_dir, args["path"])
    if not path.exists():
        return f"Error: File not found: {args['path']}"
    if not path.is_file():
        return f"Error: Not a file: {args['path']}"
    offset = args.get("offset", 0)
    limit = args.get("limit", 500)
    try:
        text = path.read_text(errors="ignore")
    except Exception as e:
        return f"Error reading file: {e}"
    lines = text.splitlines()
    selected = lines[offset:offset + limit]
    result = []
    for i, line in enumerate(selected, start=offset + 1):
        result.append(f"{i:>6}\t{line}")
    total = len(lines)
    header = f"File: {path.name} ({total} lines)"
    if offset > 0 or offset + limit < total:
        header += f" [showing {offset+1}-{min(offset+limit, total)}]"
    return header + "\n" + "\n".join(result)


def _tool_write(working_dir: str, args: dict) -> str:
    path = _resolve(working_dir, args["path"])
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        content = args["content"]
        path.write_text(content)
        lines = content.count("\n") + (1 if content and not content.endswith("\n") else 0)
        return f"Written {len(content)} bytes ({lines} lines) to {args['path']}"
    except Exception as e:
        return f"Error writing file: {e}"


def _tool_edit(working_dir: str, args: dict) -> str:
    path = _resolve(working_dir, args["path"])
    if not path.exists():
        return f"Error: File not found: {args['path']}"
    old = args["old_string"]
    new = args["new_string"]
    try:
        text = path.read_text(errors="ignore")
    except Exception as e:
        return f"Error reading file: {e}"
    if old not in text:
        return f"Error: String not found in {args['path']}. The exact old_string must match."
    occurrences = text.count(old)
    if occurrences > 1:
        return f"Error: Found {occurrences} occurrences of old_string in {args['path']}. Provide more context to make it unique."
    new_text = text.replace(old, new, 1)
    try:
        path.write_text(new_text)
    except Exception as e:
        return f"Error writing file: {e}"
    diff = list(difflib.unified_diff(
        text.splitlines(keepends=True),
        new_text.splitlines(keepends=True),
        fromfile=f"a/{args['path']}",
        tofile=f"b/{args['path']}",
    ))
    return f"Edited {args['path']} (1 replacement)\n" + "".join(diff[:50])


def _tool_patch(working_dir: str, args: dict) -> str:
    path = _resolve(working_dir, args["path"])
    diff_text = args["diff"]
    try:
        original = path.read_text(errors="ignore") if path.exists() else ""
    except Exception as e:
        return f"Error reading file: {e}"
    patched = difflib.restore(diff_text.splitlines(keepends=True), 1)
    if patched:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("".join(patched))
            return f"Patch applied to {args['path']}"
        except Exception as e:
            return f"Error applying patch: {e}"
    return f"Error: Could not apply patch to {args['path']}"


def _tool_delete(working_dir: str, args: dict) -> str:
    path = _resolve(working_dir, args["path"])
    working = Path(working_dir).resolve()
    if not str(path).startswith(str(working)):
        return f"Error: Cannot delete path outside working directory: {args['path']}"
    if not path.exists():
        return f"Error: File not found: {args['path']}"
    if path.is_dir():
        return f"Error: Cannot delete directory: {args['path']}. Only files can be deleted."
    try:
        path.unlink()
        return f"Deleted: {args['path']}"
    except Exception as e:
        return f"Error deleting file: {e}"


def _tool_list_dir(working_dir: str, args: dict) -> str:
    path = _resolve(working_dir, args.get("path", "."))
    if not path.exists():
        return f"Error: Directory not found: {args.get('path', '.')}"
    if not path.is_dir():
        return f"Error: Not a directory: {args.get('path', '.')}"
    entries = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
    result = []
    for entry in entries:
        try:
            is_dir = entry.is_dir()
            prefix = "d" if is_dir else "-"
            if is_dir:
                child_count = sum(1 for _ in entry.iterdir()) if entry.exists() else 0
                result.append(f"{prefix} {'':>10} {entry.name}/ ({child_count} items)")
            else:
                size = entry.stat().st_size
                result.append(f"{prefix} {size:>10} {entry.name}")
        except PermissionError:
            result.append(f"? {'':>10} {entry.name}/ (no access)")
    if not result:
        return f"Directory {args.get('path', '.')} is empty"
    return f"Directory: {path}\n" + "\n".join(result)


def _tool_glob(working_dir: str, args: dict) -> str:
    pattern = args["pattern"]
    base = _resolve(working_dir, args.get("path", "."))
    excludes = args.get("exclude", [])
    if not base.exists():
        return f"Error: Directory not found: {args.get('path', '.')}"
    matches = []
    try:
        for match in base.rglob(pattern):
            if match.is_file():
                rel = str(match.relative_to(Path(working_dir))) if str(Path(working_dir)) in str(match) else str(match)
                excluded = False
                for exc in excludes:
                    if fnmatch.fnmatch(rel, exc) or fnmatch.fnmatch(match.name, exc):
                        excluded = True
                        break
                if not excluded:
                    matches.append(rel)
                    if len(matches) >= 200:
                        break
    except Exception as e:
        return f"Error in glob: {e}"
    if not matches:
        return f"No files found matching '{pattern}'"
    return f"Found {len(matches)} files:\n" + "\n".join(matches)

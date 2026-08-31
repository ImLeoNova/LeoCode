"""Code intelligence tools — LSP integration with graceful degradation."""

from __future__ import annotations

from typing import Any

from .registry import ToolMetadata, ToolCategory, RetryPolicy
from ..permissions import RiskLevel


def register_code_intel_tools(registry, working_dir: str):
    """Register code intelligence tools into the registry."""

    async def execute_lsp(tool_id: str, args: dict) -> str:
        return await _tool_lsp(working_dir, args)

    registry.register(
        ToolMetadata(
            id="lsp",
            name="LSP",
            description="Code intelligence: go-to-definition, find-references, hover, symbols, diagnostics.",
            category=ToolCategory.CODE_INTEL,
            input_schema={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["definition", "references", "hover", "symbols", "diagnostics", "implementation"], "description": "LSP action to perform"},
                    "file": {"type": "string", "description": "File path"},
                    "line": {"type": "integer", "description": "Line number (1-indexed)"},
                    "column": {"type": "integer", "description": "Column number (1-indexed)"},
                    "symbol": {"type": "string", "description": "Symbol name for workspace symbol search"},
                },
                "required": ["action"],
            },
            risk_level=RiskLevel.LOW,
            timeout=10.0,
            retry_policy=RetryPolicy(max_retries=0),
        ),
        execute_lsp,
    )


async def _tool_lsp(working_dir: str, args: dict) -> str:
    action = args.get("action", "symbols")
    file_path = args.get("file", "")
    line = args.get("line", 1)
    column = args.get("column", 1)
    symbol = args.get("symbol", "")

    try:
        from pygls.server import LanguageServer
        return (
            "LSP server available but not configured for this workspace.\n"
            "To use LSP features, start a language server (e.g., pyright, typescript-language-server).\n"
            f"Action requested: {action} on {file_path or '(workspace)'}"
        )
    except ImportError:
        pass

    if action == "symbols":
        return _fallback_symbols(working_dir)
    elif action == "definition":
        return f"LSP not available. Cannot resolve definition for {file_path}:{line}:{column}"
    elif action == "references":
        return f"LSP not available. Cannot find references in {file_path}:{line}:{column}"
    elif action == "hover":
        return f"LSP not available. Cannot show hover for {file_path}:{line}:{column}"
    elif action == "diagnostics":
        return _fallback_diagnostics(file_path)
    elif action == "implementation":
        return f"LSP not available. Cannot find implementations for {file_path}:{line}:{column}"
    return f"Unknown LSP action: {action}"


def _fallback_symbols(working_dir: str) -> str:
    """Basic symbol detection via regex when LSP is unavailable."""
    import re
    from pathlib import Path

    patterns = [
        (r"^(?:class|struct|enum)\s+(\w+)", "type"),
        (r"^(?:def|function|fn|func)\s+(\w+)", "function"),
        (r"^(?:const|let|var)\s+(\w+)", "variable"),
    ]

    symbols = []
    base = Path(working_dir)
    for ext in ["*.py", "*.js", "*.ts", "*.tsx", "*.go", "*.rs"]:
        for f in base.rglob(ext):
            if f.stat().st_size > 500_000:
                continue
            try:
                text = f.read_text(errors="ignore")
                for i, line in enumerate(text.splitlines(), 1):
                    for pattern, kind in patterns:
                        m = re.match(pattern, line.strip())
                        if m:
                            rel = str(f.relative_to(base)) if str(base) in str(f) else str(f)
                            symbols.append(f"{rel}:{i} {kind} {m.group(1)}")
                            if len(symbols) >= 100:
                                break
                if len(symbols) >= 100:
                    break
            except Exception:
                continue
    if not symbols:
        return "No symbols found (LSP not available for full analysis)"
    return f"Symbols found ({len(symbols)}):\n" + "\n".join(symbols[:100])


def _fallback_diagnostics(file_path: str) -> str:
    if not file_path:
        return "No file specified for diagnostics"
    from pathlib import Path
    p = Path(file_path)
    if not p.exists():
        return f"File not found: {file_path}"
    if not p.suffix == ".py":
        return f"Diagnostics only available for Python files without LSP. Got: {p.suffix}"
    try:
        import ast
        text = p.read_text(errors="ignore")
        ast.parse(text)
        return f"No syntax errors in {file_path}"
    except SyntaxError as e:
        return f"Syntax error in {file_path}:{e.lineno}: {e.msg}"
    except Exception as e:
        return f"Cannot parse file: {e}"

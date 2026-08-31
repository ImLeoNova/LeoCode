"""Extensibility tools — controlled execution dispatcher."""

from __future__ import annotations

from typing import Any

from .registry import ToolMetadata, ToolCategory
from ..permissions import RiskLevel


def register_extensibility_tools(registry, working_dir: str):
    """Register extensibility tools into the registry."""

    async def execute_execute(tool_id: str, args: dict) -> str:
        return _tool_execute(args)

    registry.register(
        ToolMetadata(
            id="execute",
            name="Execute",
            description="Controlled higher-level execution dispatcher for complex multi-step workflows.",
            category=ToolCategory.EXTENSIBILITY,
            input_schema={
                "type": "object",
                "properties": {
                    "workflow": {"type": "string", "enum": ["refactor", "test", "build", "lint", "format", "deploy"], "description": "Workflow to execute"},
                    "target": {"type": "string", "description": "Target file, directory, or module"},
                    "options": {"type": "object", "description": "Additional workflow options"},
                },
                "required": ["workflow"],
            },
            risk_level=RiskLevel.CRITICAL,
            timeout=120.0,
        ),
        execute_execute,
    )


def _tool_execute(args: dict) -> str:
    workflow = args.get("workflow", "")
    target = args.get("target", "")
    options = args.get("options", {})

    if workflow == "refactor":
        return f"Refactor workflow for '{target}' queued. Use shell tool with appropriate commands."
    elif workflow == "test":
        return f"Test workflow for '{target}' queued. Use shell tool to run tests."
    elif workflow == "build":
        return f"Build workflow for '{target}' queued. Use shell tool to build."
    elif workflow == "lint":
        return f"Lint workflow for '{target}' queued. Use shell tool to lint."
    elif workflow == "format":
        return f"Format workflow for '{target}' queued. Use shell tool to format."
    elif workflow == "deploy":
        return f"Deploy workflow for '{target}' queued. Use shell tool to deploy."
    return f"Unknown workflow: {workflow}"

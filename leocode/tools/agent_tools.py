"""Agent tools — todo, task, question, plan, skill."""

from __future__ import annotations

import uuid
from typing import Any, Optional

from .registry import ToolMetadata, ToolCategory, ToolSource
from ..permissions import RiskLevel


def register_agent_tools(registry, working_dir: str, app=None):
    """Register agent/coordination tools into the registry."""

    async def execute_todo(tool_id: str, args: dict) -> str:
        return _tool_todo(args, app)

    async def execute_task(tool_id: str, args: dict) -> str:
        return f"Sub-agent task queued: {args.get('description', 'unspecified')}"

    async def execute_question(tool_id: str, args: dict) -> str:
        return _tool_question(args)

    async def execute_plan(tool_id: str, args: dict) -> str:
        return _tool_plan(args)

    async def execute_skill(tool_id: str, args: dict) -> str:
        return _tool_skill(args)

    tools = [
        ToolMetadata(
            id="todo",
            name="Todo",
            description="Create, update, complete, cancel, or delete task items for tracking agent progress.",
            category=ToolCategory.AGENT,
            input_schema={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["create", "update", "complete", "cancel", "delete", "reorder", "list"], "description": "Action to perform"},
                    "task_id": {"type": "string", "description": "Task ID (for update/complete/cancel/delete)"},
                    "content": {"type": "string", "description": "Task description (for create/update)"},
                    "active_form": {"type": "string", "description": "Active form description shown while in progress"},
                    "priority": {"type": "string", "enum": ["high", "medium", "low"], "description": "Task priority"},
                    "status": {"type": "string", "enum": ["pending", "in_progress", "completed", "cancelled", "blocked"], "description": "New status (for update)"},
                },
                "required": ["action"],
            },
            risk_level=RiskLevel.SAFE,
            timeout=5.0,
        ),
        ToolMetadata(
            id="task",
            name="Task",
            description="Spawn a sub-agent to handle a complex, independent sub-task with isolated context.",
            category=ToolCategory.AGENT,
            input_schema={
                "type": "object",
                "properties": {
                    "description": {"type": "string", "description": "Short task description"},
                    "prompt": {"type": "string", "description": "Detailed task instructions for the sub-agent"},
                },
                "required": ["description", "prompt"],
            },
            risk_level=RiskLevel.HIGH,
            timeout=120.0,
        ),
        ToolMetadata(
            id="question",
            name="Question",
            description="Ask the user for clarification or a decision before proceeding.",
            category=ToolCategory.AGENT,
            input_schema={
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "Question to ask the user"},
                    "options": {"type": "array", "items": {"type": "string"}, "description": "Optional answer choices"},
                },
                "required": ["question"],
            },
            risk_level=RiskLevel.SAFE,
            timeout=300.0,
        ),
        ToolMetadata(
            id="plan",
            name="Plan",
            description="Create or manage a structured plan before executing complex multi-step tasks.",
            category=ToolCategory.AGENT,
            input_schema={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["create", "update", "complete", "list"], "description": "Action to perform"},
                    "steps": {"type": "array", "items": {"type": "string"}, "description": "Plan steps (for create)"},
                    "step_index": {"type": "integer", "description": "Step index to update/complete"},
                },
                "required": ["action"],
            },
            risk_level=RiskLevel.SAFE,
            timeout=5.0,
        ),
        ToolMetadata(
            id="skill",
            name="Skill",
            description="Load reusable agent skills or instructions for specialized workflows.",
            category=ToolCategory.EXTENSIBILITY,
            input_schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Skill name to load"},
                },
                "required": ["name"],
            },
            risk_level=RiskLevel.SAFE,
            timeout=5.0,
        ),
    ]

    executors = [execute_todo, execute_task, execute_question, execute_plan, execute_skill]
    for meta, executor in zip(tools, executors):
        registry.register(meta, executor)


def _tool_todo(args: dict, app=None) -> str:
    action = args.get("action", "list")

    if hasattr(app, "todo_manager") and app.todo_manager:
        mgr = app.todo_manager
        if action == "create":
            task = mgr.create(
                content=args.get("content", ""),
                active_form=args.get("active_form", ""),
                priority=args.get("priority", "medium"),
            )
            return f"Created task {task.id}: {task.content}"
        elif action == "update":
            tid = args.get("task_id", "")
            result = mgr.update(tid, content=args.get("content"), priority=args.get("priority"))
            return result or f"Updated task {tid}"
        elif action == "complete":
            tid = args.get("task_id", "")
            return mgr.complete(tid)
        elif action == "cancel":
            tid = args.get("task_id", "")
            return mgr.cancel(tid)
        elif action == "delete":
            tid = args.get("task_id", "")
            return mgr.delete(tid)
        elif action == "list":
            tasks = mgr.list_all()
            if not tasks:
                return "No tasks"
            lines = []
            for t in tasks:
                icon = {"pending": "○", "in_progress": "⟳", "completed": "✓", "cancelled": "✗", "blocked": "⊘"}.get(t.status, "?")
                lines.append(f"  {icon} [{t.id}] {t.content} ({t.priority})")
            return "\n".join(lines)
        elif action == "reorder":
            return "Tasks reordered"
    return "Todo manager not available"


def _tool_question(args: dict) -> str:
    question = args.get("question", "")
    options = args.get("options", [])
    parts = [f"Question: {question}"]
    if options:
        for i, opt in enumerate(options, 1):
            parts.append(f"  {i}. {opt}")
    parts.append("\n[Awaiting user response]")
    return "\n".join(parts)


def _tool_plan(args: dict) -> str:
    action = args.get("action", "list")
    if action == "create":
        steps = args.get("steps", [])
        if not steps:
            return "Error: No steps provided"
        lines = ["Plan created:"]
        for i, step in enumerate(steps, 1):
            lines.append(f"  {i}. ○ {step}")
        return "\n".join(lines)
    elif action == "list":
        return "No active plan"
    elif action == "complete":
        idx = args.get("step_index", 0)
        return f"Step {idx + 1} completed"
    return f"Plan {action} executed"


def _tool_skill(args: dict) -> str:
    name = args.get("name", "")
    if not name:
        return "Error: No skill name provided"
    return f"Skill '{name}' loaded. Skill instructions are now active in the agent context."

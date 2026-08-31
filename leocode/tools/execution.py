"""Execution tools — shell command runner."""

from __future__ import annotations

import asyncio
from typing import Any

from .registry import ToolMetadata, ToolCategory, RetryPolicy
from ..permissions import RiskLevel


def register_execution_tools(registry, working_dir: str):
    """Register execution tools into the registry."""

    async def execute_shell(tool_id: str, args: dict) -> str:
        return await _tool_shell(working_dir, args)

    registry.register(
        ToolMetadata(
            id="shell",
            name="Shell",
            description="Execute a shell command with timeout and capture output.",
            category=ToolCategory.EXECUTION,
            input_schema={
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Shell command to execute"},
                    "timeout": {"type": "integer", "description": "Timeout in seconds", "default": 30},
                },
                "required": ["command"],
            },
            risk_level=RiskLevel.HIGH,
            timeout=30.0,
            retry_policy=RetryPolicy(max_retries=0),
            supports_cancellation=True,
        ),
        execute_shell,
    )


async def _tool_shell(working_dir: str, args: dict) -> str:
    command = args.get("command", "")
    if not command:
        return "Error: No command provided"
    timeout = args.get("timeout", 30)
    timeout = min(timeout, 120)

    try:
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=working_dir,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            try:
                proc.kill()
                await proc.communicate()
            except Exception:
                pass
            return f"Error: Command timed out after {timeout}s: {command[:80]}"

        output = stdout.decode(errors="ignore")
        err_output = stderr.decode(errors="ignore")
        exit_code = proc.returncode

        parts = []
        if output:
            parts.append(output)
        if err_output:
            parts.append(f"[stderr]\n{err_output}")
        if exit_code != 0:
            parts.append(f"[exit code: {exit_code}]")

        result = "\n".join(parts) if parts else "(no output)"
        if len(result) > 15000:
            result = result[:15000] + f"\n... (truncated, {len(result)} chars total)"
        return result
    except Exception as e:
        return f"Error executing command: {e}"

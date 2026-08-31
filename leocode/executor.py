"""Unified Tool Executor — handles lifecycle, permissions, timeouts, retry, cancellation."""

from __future__ import annotations

import asyncio
import time
import uuid
import logging
from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Optional, Callable, Coroutine

from .events import EventBus, Event, EventType
from .permissions import PermissionEngine, PermissionAction
from .tools.registry import ToolRegistry, ToolMetadata

log = logging.getLogger(__name__)


class ExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    AWAITING_APPROVAL = "awaiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


@dataclass
class ToolExecution:
    execution_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    tool_name: str = ""
    arguments: dict = field(default_factory=dict)
    status: ExecutionStatus = ExecutionStatus.PENDING
    result: str = ""
    error: str = ""
    start_time: float = 0.0
    end_time: float = 0.0
    duration: float = 0.0
    retries: int = 0
    approval_action: str = ""

    def to_dict(self) -> dict:
        return {
            "execution_id": self.execution_id,
            "tool_name": self.tool_name,
            "arguments": self.arguments,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "retries": self.retries,
        }


ApprovalCallback = Callable[[ToolMetadata, dict, str], Coroutine[Any, Any, str]]


class ToolExecutor:
    """Unified executor with permission gate, timeout, retry, and cancellation."""

    def __init__(
        self,
        registry: ToolRegistry,
        permissions: PermissionEngine,
        events: EventBus,
        approval_callback: Optional[ApprovalCallback] = None,
    ):
        self.registry = registry
        self.permissions = permissions
        self.events = events
        self.approval_callback = approval_callback
        self._history: list[ToolExecution] = []
        self._active: dict[str, asyncio.Task] = {}
        self._max_history = 200
        self._concurrent_limit = 5
        self._semaphore = asyncio.Semaphore(self._concurrent_limit)

    @property
    def history(self) -> list[ToolExecution]:
        return list(self._history)

    @property
    def active_count(self) -> int:
        return len(self._active)

    async def execute(self, tool_name: str, arguments: dict) -> str:
        """Full lifecycle: validate → permission → execute → result."""
        execution = ToolExecution(tool_name=tool_name, arguments=arguments)
        self._history.append(execution)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

        meta = self.registry.resolve(tool_name)
        if not meta:
            execution.status = ExecutionStatus.FAILED
            execution.error = f"Unknown tool: {tool_name}"
            return f"Error: Unknown tool: {tool_name}"

        if not meta.enabled:
            execution.status = ExecutionStatus.FAILED
            execution.error = f"Tool disabled: {tool_name}"
            return f"Error: Tool '{tool_name}' is disabled"

        await self.events.emit(Event(
            type=EventType.TOOL_PENDING,
            data=execution.to_dict(),
        ))

        action = self.permissions.check(tool_name, arguments, risk_level=meta.risk_level)
        if action == PermissionAction.DENY:
            execution.status = ExecutionStatus.FAILED
            execution.error = "Permission denied"
            await self.events.emit(Event(
                type=EventType.TOOL_FAILED,
                data={**execution.to_dict(), "reason": "denied"},
            ))
            return f"Error: Permission denied for tool '{tool_name}'"

        if action == PermissionAction.ASK:
            execution.status = ExecutionStatus.AWAITING_APPROVAL
            await self.events.emit(Event(
                type=EventType.TOOL_AWAITING_APPROVAL,
                data=execution.to_dict(),
            ))
            if self.approval_callback:
                approval_result = await self.approval_callback(meta, arguments, tool_name)
                execution.approval_action = approval_result
                if approval_result == "denied":
                    execution.status = ExecutionStatus.FAILED
                    execution.error = "User denied permission"
                    await self.events.emit(Event(
                        type=EventType.TOOL_FAILED,
                        data={**execution.to_dict(), "reason": "denied"},
                    ))
                    return f"Error: Permission denied by user for tool '{tool_name}'"
            else:
                execution.status = ExecutionStatus.FAILED
                execution.error = "No approval handler"
                return f"Error: Approval required but no handler available"

        async with self._semaphore:
            return await self._run_with_retry(execution, meta)

    async def _run_with_retry(self, execution: ToolExecution, meta: ToolMetadata) -> str:
        max_retries = meta.retry_policy.max_retries
        backoff = meta.retry_policy.backoff_base

        while True:
            execution.status = ExecutionStatus.RUNNING
            execution.start_time = time.time()
            await self.events.emit(Event(
                type=EventType.TOOL_STARTED,
                data=execution.to_dict(),
            ))

            try:
                result = await asyncio.wait_for(
                    self._do_execute(execution, meta),
                    timeout=meta.timeout,
                )
                execution.result = result
                execution.status = ExecutionStatus.COMPLETED
                execution.end_time = time.time()
                execution.duration = execution.end_time - execution.start_time
                await self.events.emit(Event(
                    type=EventType.TOOL_COMPLETED,
                    data=execution.to_dict(),
                ))
                return result

            except asyncio.TimeoutError:
                execution.end_time = time.time()
                execution.duration = execution.end_time - execution.start_time
                msg = f"Tool '{meta.id}' timed out after {meta.timeout}s"
                execution.error = msg

                if execution.retries < max_retries:
                    execution.retries += 1
                    execution.status = ExecutionStatus.RETRYING
                    await self.events.emit(Event(
                        type=EventType.TOOL_FAILED,
                        data={**execution.to_dict(), "retrying": True, "retry": execution.retries},
                    ))
                    await asyncio.sleep(min(backoff, 30.0))
                    backoff *= 2
                    continue

                execution.status = ExecutionStatus.FAILED
                await self.events.emit(Event(
                    type=EventType.TOOL_FAILED,
                    data=execution.to_dict(),
                ))
                return f"Error: {msg}"

            except asyncio.CancelledError:
                execution.end_time = time.time()
                execution.duration = execution.end_time - execution.start_time
                execution.status = ExecutionStatus.CANCELLED
                execution.error = "Cancelled"
                await self.events.emit(Event(
                    type=EventType.TOOL_CANCELLED,
                    data=execution.to_dict(),
                ))
                return "Error: Tool execution cancelled"

            except Exception as e:
                execution.end_time = time.time()
                execution.duration = execution.end_time - execution.start_time
                execution.error = str(e)

                if execution.retries < max_retries:
                    execution.retries += 1
                    execution.status = ExecutionStatus.RETRYING
                    await asyncio.sleep(min(backoff, 30.0))
                    backoff *= 2
                    continue

                execution.status = ExecutionStatus.FAILED
                await self.events.emit(Event(
                    type=EventType.TOOL_FAILED,
                    data=execution.to_dict(),
                ))
                return f"Error: {e}"

    async def _do_execute(self, execution: ToolExecution, meta: ToolMetadata) -> str:
        executor_fn = self.registry.get_executor(meta.id)
        if not executor_fn:
            return f"No executor for tool: {meta.id}"
        return await executor_fn(meta.id, execution.arguments)

    async def cancel(self, execution_id: str) -> bool:
        task = self._active.get(execution_id)
        if task and not task.done():
            task.cancel()
            return True
        return False

    def cancel_all(self):
        for task in self._active.values():
            if not task.done():
                task.cancel()

    def get_by_status(self, status: ExecutionStatus) -> list[ToolExecution]:
        return [e for e in self._history if e.status == status]

    def recent(self, limit: int = 20) -> list[ToolExecution]:
        return self._history[-limit:]

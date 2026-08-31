"""Strongly typed event bus for agent runtime, tools, todos, and UI.

Phase 7: Semantic event layer — renderer receives structured events
instead of guessing UI meaning from arbitrary strings.
"""

from __future__ import annotations

import asyncio
import logging
from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine, Optional

log = logging.getLogger(__name__)

EventHandler = Callable[["Event"], Coroutine[Any, Any, None]]


class EventType(str, Enum):
    # Tool lifecycle
    TOOL_PENDING = "tool.pending"
    TOOL_STARTED = "tool.started"
    TOOL_PROGRESS = "tool.progress"
    TOOL_OUTPUT = "tool.output"
    TOOL_AWAITING_APPROVAL = "tool.awaiting_approval"
    TOOL_COMPLETED = "tool.completed"
    TOOL_FAILED = "tool.failed"
    TOOL_CANCELLED = "tool.cancelled"

    # Task/Todo lifecycle
    TASK_CREATED = "task.created"
    TASK_UPDATED = "task.updated"
    TASK_STARTED = "task.started"
    TASK_COMPLETED = "task.completed"
    TASK_CANCELLED = "task.cancelled"
    TASK_BLOCKED = "task.blocked"

    # Permission
    APPROVAL_REQUESTED = "approval.requested"
    APPROVAL_GRANTED = "approval.granted"
    APPROVAL_DENIED = "approval.denied"

    # Agent state
    AGENT_STATE_CHANGED = "agent.state_changed"

    # Phase 7: Semantic rendering events
    ASSISTANT_MESSAGE = "assistant.message"
    ASSISTANT_THINKING = "assistant.thinking"
    ASSISTANT_STREAMING = "assistant.streaming"

    DIFF_CREATED = "diff.created"
    DIFF_COLLAPSED = "diff.collapsed"

    SYSTEM_STATUS = "system.status"


@dataclass
class Event:
    type: EventType
    data: dict = field(default_factory=dict)
    source: str = ""
    timestamp: float = field(default_factory=lambda: __import__("time").time())


class EventBus:
    """Typed event bus with subscribe/emit/dispatch."""

    def __init__(self):
        self._handlers: dict[EventType, list[EventHandler]] = {}
        self._wildcard_handlers: list[EventHandler] = []
        self._history: list[Event] = []
        self._max_history = 500

    def subscribe(self, event_type: EventType, handler: EventHandler):
        self._handlers.setdefault(event_type, []).append(handler)

    def subscribe_all(self, handler: EventHandler):
        self._wildcard_handlers.append(handler)

    def unsubscribe(self, event_type: EventType, handler: EventHandler):
        handlers = self._handlers.get(event_type, [])
        if handler in handlers:
            handlers.remove(handler)

    def unsubscribe_all(self, handler: EventHandler):
        if handler in self._wildcard_handlers:
            self._wildcard_handlers.remove(handler)

    async def emit(self, event: Event):
        self._history.append(event)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

        handlers = list(self._handlers.get(event.type, []))
        for h in handlers:
            try:
                await h(event)
            except Exception as e:
                log.error(f"Event handler error for {event.type}: {e}")

        for h in list(self._wildcard_handlers):
            try:
                await h(event)
            except Exception as e:
                log.error(f"Wildcard handler error for {event.type}: {e}")

    def emit_sync(self, event: Event):
        """Queue event for async dispatch (non-blocking)."""
        self._history.append(event)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

    def get_history(self, event_type: Optional[EventType] = None, limit: int = 50) -> list[Event]:
        if event_type:
            return [e for e in self._history if e.type == event_type][-limit:]
        return self._history[-limit:]

    def clear(self):
        self._handlers.clear()
        self._wildcard_handlers.clear()
        self._history.clear()

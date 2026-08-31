"""Todo Manager — Claude Code-style task tracking for agent workflows."""

from __future__ import annotations

import time
import uuid
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Callable, Any

from .events import EventBus, Event, EventType


class TodoStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"


class TodoPriority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class TodoTask:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    content: str = ""
    active_form: str = ""
    status: TodoStatus = TodoStatus.PENDING
    priority: TodoPriority = TodoPriority.MEDIUM
    dependencies: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


class TodoManager:
    """First-class task tracking for agent workflows."""

    def __init__(self, events: Optional[EventBus] = None):
        self._tasks: dict[str, TodoTask] = {}
        self._order: list[str] = []
        self._events = events

    def create(
        self,
        content: str,
        active_form: str = "",
        priority: str = "medium",
        dependencies: Optional[list[str]] = None,
    ) -> TodoTask:
        task = TodoTask(
            content=content,
            active_form=active_form or content[:50],
            priority=TodoPriority(priority) if priority in TodoPriority.__members__.values() else TodoPriority.MEDIUM,
            dependencies=dependencies or [],
        )
        self._tasks[task.id] = task
        self._order.append(task.id)
        self._emit("task.created", task)
        return task

    def update(
        self,
        task_id: str,
        content: Optional[str] = None,
        active_form: Optional[str] = None,
        priority: Optional[str] = None,
        status: Optional[str] = None,
    ) -> str:
        task = self._tasks.get(task_id)
        if not task:
            return f"Task not found: {task_id}"
        if content is not None:
            task.content = content
        if active_form is not None:
            task.active_form = active_form
        if priority is not None:
            try:
                task.priority = TodoPriority(priority)
            except ValueError:
                pass
        if status is not None:
            try:
                task.status = TodoStatus(status)
            except ValueError:
                pass
        task.updated_at = time.time()
        self._emit("task.updated", task)
        return f"Updated task {task_id}"

    def complete(self, task_id: str) -> str:
        task = self._tasks.get(task_id)
        if not task:
            return f"Task not found: {task_id}"
        task.status = TodoStatus.COMPLETED
        task.updated_at = time.time()
        self._emit("task.completed", task)
        return f"Completed task: {task.content}"

    def cancel(self, task_id: str) -> str:
        task = self._tasks.get(task_id)
        if not task:
            return f"Task not found: {task_id}"
        task.status = TodoStatus.CANCELLED
        task.updated_at = time.time()
        self._emit("task.cancelled", task)
        return f"Cancelled task: {task.content}"

    def delete(self, task_id: str) -> str:
        task = self._tasks.get(task_id)
        if not task:
            return f"Task not found: {task_id}"
        del self._tasks[task_id]
        if task_id in self._order:
            self._order.remove(task_id)
        return f"Deleted task: {task.content}"

    def reorder(self, task_ids: list[str]):
        self._order = [tid for tid in task_ids if tid in self._tasks]

    def set_status(self, task_id: str, status: str) -> str:
        task = self._tasks.get(task_id)
        if not task:
            return f"Task not found: {task_id}"
        try:
            task.status = TodoStatus(status)
            task.updated_at = time.time()
            self._emit(f"task.{status}", task)
            return f"Task {task_id} → {status}"
        except ValueError:
            return f"Invalid status: {status}"

    def get(self, task_id: str) -> Optional[TodoTask]:
        return self._tasks.get(task_id)

    def list_all(self) -> list[TodoTask]:
        ordered = []
        for tid in self._order:
            if tid in self._tasks:
                ordered.append(self._tasks[tid])
        for tid in self._tasks:
            if tid not in self._order:
                ordered.append(self._tasks[tid])
        return ordered

    def list_by_status(self, status: str) -> list[TodoTask]:
        try:
            s = TodoStatus(status)
            return [t for t in self.list_all() if t.status == s]
        except ValueError:
            return []

    def active_task(self) -> Optional[TodoTask]:
        for task in self.list_all():
            if task.status == TodoStatus.IN_PROGRESS:
                return task
        return None

    def progress(self) -> dict:
        tasks = self.list_all()
        total = len(tasks)
        completed = sum(1 for t in tasks if t.status == TodoStatus.COMPLETED)
        in_progress = sum(1 for t in tasks if t.status == TodoStatus.IN_PROGRESS)
        pending = sum(1 for t in tasks if t.status == TodoStatus.PENDING)
        cancelled = sum(1 for t in tasks if t.status == TodoStatus.CANCELLED)
        blocked = sum(1 for t in tasks if t.status == TodoStatus.BLOCKED)
        return {
            "total": total,
            "completed": completed,
            "in_progress": in_progress,
            "pending": pending,
            "cancelled": cancelled,
            "blocked": blocked,
            "percent": (completed / total * 100) if total > 0 else 0,
        }

    def summary(self) -> str:
        prog = self.progress()
        if prog["total"] == 0:
            return "No tasks"
        active = self.active_task()
        lines = [f"Progress: {prog['completed']}/{prog['total']} ({prog['percent']:.0f}%)"]
        if active:
            lines.append(f"Active: {active.active_form or active.content}")
        return "\n".join(lines)

    def clear_completed(self) -> int:
        completed_ids = [
            tid for tid, task in self._tasks.items()
            if task.status == TodoStatus.COMPLETED
        ]
        for tid in completed_ids:
            del self._tasks[tid]
            if tid in self._order:
                self._order.remove(tid)
        return len(completed_ids)

    def _emit(self, event_name: str, task: TodoTask):
        if self._events:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self._events.emit(Event(
                    type=EventType(event_name),
                    data={"task_id": task.id, "content": task.content, "status": task.status.value},
                )))
            except RuntimeError:
                pass

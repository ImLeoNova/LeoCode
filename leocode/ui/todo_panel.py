"""Todo Panel — compact inline Claude Code-style checklist for conversation flow."""

from __future__ import annotations

from textual.widgets import Static
from textual.reactive import reactive
from rich.text import Text

from .theme import CLAUDE, TEXT, TEXT_SECONDARY, TEXT_MUTED, TEXT_DIM, SUCCESS, WARNING


class TodoPanel(Static):
    """Compact agent task checklist — Claude Code style with checkboxes."""

    _frame = reactive(0)

    def __init__(self, **kwargs):
        self._tasks: list[dict] = []
        self._expanded = False
        kwargs.setdefault("classes", "todo-inline")
        super().__init__(**kwargs)

    def render(self) -> Text:
        t = Text()
        if not self._tasks:
            return t

        for task in self._tasks:
            status = task.get("status", "pending")
            content = task.get("content", "")
            active_form = task.get("active_form", "")

            if status == "completed":
                t.append("☒ ", SUCCESS)
                t.append(content, TEXT_MUTED)
            elif status == "in_progress":
                t.append("☐ ", CLAUDE)
                display = active_form or content
                t.append(display, TEXT)
            elif status == "cancelled":
                t.append("☒ ", TEXT_DIM)
                t.append(content, TEXT_DIM)
            elif status == "blocked":
                t.append("☐ ", WARNING)
                t.append(content, TEXT_SECONDARY)
            else:
                t.append("☐ ", TEXT_DIM)
                t.append(content, TEXT_SECONDARY)

            t.append("\n")

        return t

    def update_tasks(self, tasks: list[dict]):
        self._tasks = tasks
        self.refresh()

    def advance_spinner(self):
        self._frame += 1
        self.refresh()

    def toggle_expand(self):
        self._expanded = not self._expanded
        self.refresh()

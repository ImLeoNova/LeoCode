"""Tool Activity — Claude Code style one-liner tool execution display."""

from __future__ import annotations

from textual.widgets import Static
from textual.reactive import reactive
from rich.text import Text

from .theme import CLAUDE, TEXT, TEXT_SECONDARY, TEXT_MUTED, TEXT_DIM, SUCCESS, WARNING, ERROR


class ToolActivityItem(Static):
    """Single tool execution one-liner — Claude Code format."""

    _frame = reactive(0)

    def __init__(self, tool_name: str, args: dict, execution_id: str = "", **kwargs):
        self.tool_name = tool_name
        self.tool_args = args
        self.execution_id = execution_id
        self.status = "pending"
        self.result = ""
        self.duration = 0.0
        kwargs.setdefault("classes", "tool-activity-inline")
        super().__init__(**kwargs)

    def render(self) -> Text:
        t = Text()
        icons = {
            "pending": "○",
            "running": "⠋",
            "completed": "⏺",
            "failed": "✗",
            "cancelled": "⊘",
            "awaiting_approval": "⚠",
        }
        colors = {
            "pending": TEXT_MUTED,
            "running": CLAUDE,
            "completed": TEXT_SECONDARY,
            "failed": ERROR,
            "cancelled": TEXT_DIM,
            "awaiting_approval": WARNING,
        }
        icon = icons.get(self.status, "?")
        color = colors.get(self.status, TEXT_MUTED)
        t.append(f"{icon} ", color)

        display_name = self._tool_display_name()
        t.append(display_name, TEXT_SECONDARY)

        basename = self._get_basename()
        if basename:
            t.append(f" {basename}", TEXT_MUTED)

        meta = self._get_metadata()
        if meta:
            t.append(f" {meta}", TEXT_DIM)

        t.append("\n")
        return t

    def _tool_display_name(self) -> str:
        names = {
            "read": "Read",
            "write": "Write",
            "edit": "Edit",
            "patch": "Edit",
            "bash": "Bash",
            "shell": "Bash",
            "execute": "Bash",
            "grep": "Grep",
            "glob": "Glob",
            "web_search": "WebSearch",
            "web_fetch": "WebFetch",
        }
        return names.get(self.tool_name, self.tool_name.title())

    def _get_basename(self) -> str:
        path = self.tool_args.get("path", "")
        if path:
            return path.rsplit("/", 1)[-1] if "/" in path else path
        return ""

    def _get_metadata(self) -> str:
        if self.status == "running":
            return ""

        if self.tool_name in ("read", "write", "edit", "patch") and self.result:
            lines = self.result.count("\n") + 1 if self.result else 0
            if lines > 0:
                return f"({lines} lines)"

        if self.tool_name in ("bash", "shell", "execute"):
            cmd = self.tool_args.get("command", "")
            if cmd:
                if len(cmd) > 30:
                    cmd = cmd[:29] + "…"
                return cmd

        if self.tool_name == "grep" and "pattern" in self.tool_args:
            return self.tool_args["pattern"]

        if self.tool_name == "web_search" and "query" in self.tool_args:
            return self.tool_args["query"][:30]

        return ""

    def set_status(self, status: str, result: str = "", duration: float = 0.0):
        self.status = status
        self.result = result
        self.duration = duration
        self.refresh()

    def advance_spinner(self):
        self._frame += 1
        self.refresh()


class ToolActivityFeed(Static):
    """Lightweight tracker for tool executions — items are mounted individually inline."""

    def __init__(self, **kwargs):
        self._items: dict[str, ToolActivityItem] = {}
        kwargs.setdefault("classes", "tool-activity-inline")
        super().__init__(**kwargs)

    def on_mount(self):
        self.styles.display = "none"

    def render(self) -> Text:
        return Text("")

    def add_execution(self, execution_id: str, tool_name: str, args: dict):
        item = ToolActivityItem(tool_name, args, execution_id)
        item.status = "running"
        self._items[execution_id] = item

    def update_execution(self, execution_id: str, status: str, result: str = "", duration: float = 0.0):
        item = self._items.get(execution_id)
        if item:
            item.set_status(status, result, duration)

    def get_item(self, execution_id: str) -> ToolActivityItem | None:
        return self._items.get(execution_id)

    def clear(self):
        self._items.clear()

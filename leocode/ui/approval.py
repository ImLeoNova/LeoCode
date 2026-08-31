"""Approval dialog — modal fallback for permission requests.

Primary permission UI is now InlinePermission in widgets.py.
This modal is kept as fallback for edge cases.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.widgets import Static, Button
from textual.screen import ModalScreen

from .theme import ACCENT, BG_PANEL, TEXT, TEXT_SECONDARY, TEXT_DIM, ACCENT_HOVER


class ApprovalDialog(ModalScreen[str]):
    """Modal approval dialog — fallback when inline permission is unavailable."""

    CSS = f"""
    ApprovalDialog {{
        align: center middle;
    }}
    ApprovalDialog > Container {{
        width: 64;
        max-width: 80;
        height: auto;
        max-height: 20;
        background: {BG_PANEL};
        border: round {ACCENT};
        padding: 1 2;
    }}
    #approval-header {{
        height: 1;
        color: {ACCENT_HOVER};
        text-style: bold;
        padding: 0 0 1 0;
    }}
    #approval-tool {{
        height: 1;
        color: {TEXT};
        text-style: bold;
        padding: 0 0 0 0;
    }}
    #approval-desc {{
        height: auto;
        max-height: 6;
        color: {TEXT_SECONDARY};
        padding: 0 0 1 0;
    }}
    #approval-risk {{
        height: 1;
        color: {ACCENT_HOVER};
        padding: 0 0 0 0;
    }}
    .approval-buttons {{
        height: auto;
        padding: 1 0 0 0;
    }}
    .approval-buttons Button {{
        min-width: 14;
        height: 3;
        margin: 0 1 0 0;
    }}
    """

    BINDINGS = [
        Binding("escape", "deny", show=False),
        Binding("1", "allow_once", show=False),
        Binding("2", "always_allow", show=False),
        Binding("3", "deny", show=False),
    ]

    def __init__(self, tool_name: str, description: str, risk_level: str = "medium", args: dict | None = None, **kwargs):
        self.tool_name = tool_name
        self.description = description
        self.risk_level = risk_level
        self.args = args or {}
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        with Container():
            yield Static("⚠  Permission Required", id="approval-header")
            yield Static(f"Tool: {self.tool_name}", id="approval-tool")
            yield Static(self.description, id="approval-desc")
            yield Static(f"Risk: {self.risk_level.upper()}", id="approval-risk")
            with Horizontal(classes="approval-buttons"):
                yield Button("Cancel [3]", id="btn-deny")
                yield Button("Allow Once [1]", id="btn-allow-once", variant="primary")
                yield Button("Always Allow [2]", id="btn-always")

    def on_mount(self):
        self.query_one("#approval-desc").update(self.description)

    def action_allow_once(self):
        self.dismiss("allow_once")

    def action_always_allow(self):
        self.dismiss("always_allow")

    def action_deny(self):
        self.dismiss("denied")

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "btn-deny":
            self.dismiss("denied")
        elif event.button.id == "btn-allow-once":
            self.dismiss("allow_once")
        elif event.button.id == "btn-always":
            self.dismiss("always_allow")

"""Sidebar helpers for conversation history."""

import json
from datetime import datetime

from textual.app import ComposeResult
from textual.widgets import Static, ListView, ListItem, Label, Button
from textual.containers import Vertical, Horizontal, Container
from textual.reactive import reactive
from rich.text import Text

from ..config import CONVERSATIONS_DIR
from .theme import ACCENT, TEXT_BRIGHT, TEXT_MUTED, TEXT_DIM, INFO
from .widgets import Brand


class ConversationItem(ListItem):
    def __init__(self, title: str = "", conv_id: str = "", timestamp: str = "", **kwargs):
        self.conv_title = title
        self.conv_id = conv_id
        self.conv_timestamp = timestamp
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        yield Label(self.conv_title or self.conv_id)


class Sidebar(Container):
    def compose(self) -> ComposeResult:
        with Vertical(classes="sidebar"):
            yield Brand(classes="sidebar-header", id="sidebar-header")
            with Horizontal(classes="sidebar-actions"):
                yield Button("new session", id="btn-new", variant="primary", classes="sidebar-btn")
            yield Static("  sessions", classes="sidebar-section")
            yield ListView(id="conv-list", classes="conv-list")
            yield Static(classes="sidebar-spacer")
            yield Static(self._render_footer(), classes="sidebar-footer")

    def _render_footer(self) -> Text:
        t = Text()
        t.append("ctrl+n", ACCENT)
        t.append(" new  ", TEXT_MUTED)
        t.append("·", TEXT_DIM)
        t.append("  ctrl+m", ACCENT)
        t.append(" model", TEXT_MUTED)
        return t

    def populate_conversations(self, conversations: list[dict]):
        lv = self.query_one("#conv-list", ListView)
        lv.clear()
        for conv in conversations:
            title = conv.get("title", "Untitled")[:30]
            conv_id = conv.get("id", "")
            timestamp = conv.get("timestamp", "")
            lv.append(ConversationItem(title=title, conv_id=conv_id, timestamp=timestamp))

    @staticmethod
    def list_conversations() -> list[dict]:
        convs = []
        if CONVERSATIONS_DIR.exists():
            for f in sorted(CONVERSATIONS_DIR.glob("*.json"), reverse=True):
                try:
                    data = json.loads(f.read_text())
                    convs.append({
                        "id": f.stem,
                        "title": data.get("title", f.stem),
                        "messages": data.get("messages", []),
                        "timestamp": data.get("timestamp", ""),
                    })
                except Exception:
                    continue
        return convs

    @staticmethod
    def save_conversation(conv_id: str, title: str, messages: list[dict]):
        CONVERSATIONS_DIR.mkdir(parents=True, exist_ok=True)
        data = {
            "title": title,
            "messages": messages,
            "timestamp": datetime.now().isoformat(),
        }
        (CONVERSATIONS_DIR / f"{conv_id}.json").write_text(json.dumps(data, indent=2))

    @staticmethod
    def delete_conversation(conv_id: str):
        f = CONVERSATIONS_DIR / f"{conv_id}.json"
        if f.exists():
            f.unlink()

    @staticmethod
    def load_conversation(conv_id: str) -> dict:
        f = CONVERSATIONS_DIR / f"{conv_id}.json"
        if f.exists():
            return json.loads(f.read_text())
        return {"title": "", "messages": []}


class QuickActions(Container):
    def compose(self) -> ComposeResult:
        with Vertical(classes="quick-actions"):
            yield Static("  actions", classes="sidebar-section")
            with Horizontal(classes="action-buttons"):
                yield Button("attach", id="btn-attach", classes="action-btn")
                yield Button("search", id="btn-search", classes="action-btn")
            with Horizontal(classes="action-buttons"):
                yield Button("settings", id="btn-settings", classes="action-btn")
                yield Button("help", id="btn-help", classes="action-btn")


class ModelInfo(Static):
    model_name = reactive("")
    model_provider = reactive("")

    def render(self) -> Text:
        t = Text()
        t.append("◆ ", ACCENT)
        t.append("model\n", f"bold {TEXT_BRIGHT}")
        t.append(self.model_name or "not selected", ACCENT)
        if self.model_provider:
            t.append(f" ({self.model_provider})", TEXT_MUTED)
        return t


class StatsWidget(Static):
    message_count = reactive(0)
    token_count = reactive(0)
    file_count = reactive(0)

    def render(self) -> Text:
        t = Text()
        t.append("stats\n", f"bold {TEXT_MUTED}")
        for label, value, color in (
            ("messages", str(self.message_count), ACCENT),
            ("tokens", f"{self.token_count:,}", ACCENT),
            ("files", str(self.file_count), INFO),
        ):
            t.append(f"  {label}  ", TEXT_MUTED)
            t.append(f"{value}\n", color)
        return t

"""Leocode - Professional AI Coding Agent with Claude Code UI."""

import asyncio
import json
import uuid
import os
from typing import Optional
from datetime import datetime

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical, Horizontal, ScrollableContainer
from textual.widgets import (
    Static, ListView, ListItem, Label, Button, Input,
)
from textual.reactive import reactive
from textual import on
from textual.message import Message
from textual.screen import ModalScreen

from .config import Config, CONVERSATIONS_DIR, RAG_DIR
from .client import RouterClient
from .rag import RAGStore
from .search import WebSearch
from .agent import AgentTools
from .mcp_client import MCPManager
from .file_ops import load_file, get_file_info
from .ui.widgets import (
    MessageBubble, StatusBar, ModelSelector, ThinkingIndicator, WelcomeBanner,
    ModelSelectionModal, ACCENT, ACCENT_DIM, SECONDARY, MUTED, DIM, SURFACE,
    SURFACE_RAISED, SURFACE_OVERLAY, BORDER, TEXT_PRIMARY, TEXT_SECONDARY,
    TEXT_MUTED, TEXT_DIM, SUCCESS, WARNING, ERROR, INFO,
)


CSS = """
/* Base - Claude Code style */
Screen {
    background: #000000;
    color: #FAFAFA;
}

/* Main Layout */
#main-container {
    layout: horizontal;
    height: 1fr;
    background: #000000;
}

/* Sidebar */
#sidebar {
    width: 24;
    min-width: 20;
    max-width: 35;
    background: #18181B;
    border-right: solid #27272A;
    padding: 0;
    display: block;
}

#sidebar.hidden {
    display: none;
    width: 0;
}

.sidebar-header {
    padding: 1 1 0 1;
    color: #FFFFFF;
    text-style: bold;
    background: #18181B;
    dock: top;
    height: 3;
}

.sidebar-actions {
    dock: top;
    padding: 0 1 1 1;
    height: auto;
    background: #18181B;
}

.sidebar-btn {
    width: 1fr;
    min-width: 8;
    height: 3;
    margin: 0;
    background: #27272A;
    color: #FAFAFA;
    border: none;
}

.sidebar-btn:hover {
    background: #3F3F46;
    color: #FFFFFF;
}

Button.-primary {
    background: #FFFFFF;
    color: #000000;
    border: none;
    text-style: bold;
}

Button.-primary:hover {
    background: #B3B3B3;
    color: #000000;
}

Button {
    background: #27272A;
    color: #A1A1AA;
    border: none;
}

Button:hover {
    background: #3F3F46;
    color: #FAFAFA;
}

.sidebar-section {
    dock: top;
    padding: 1 2 0 2;
    color: #64748B;
    text-style: bold;
    background: #18181B;
}

.conv-list {
    height: 1fr;
    background: #18181B;
    scrollbar-background: #18181B;
    scrollbar-color: #27272A;
    scrollbar-color-hover: #FFFFFF;
}

.conv-list > ListItem {
    padding: 0 1;
    color: #64748B;
    background: #18181B;
    height: 3;
}

.conv-list > ListItem:hover {
    background: #27272A;
    color: #FAFAFA;
}

.conv-list > ListItem.-highlight {
    background: #27272A;
    color: #FAFAFA;
    border-left: thick #FFFFFF;
}

.sidebar-spacer {
    height: 1fr;
}

.sidebar-footer {
    dock: bottom;
    padding: 1 1;
    color: #52525B;
    background: #18181B;
    border-top: solid #27272A;
    height: 3;
}

/* Chat Area - Claude Code style */
#chat-area {
    width: 1fr;
    height: 1fr;
    background: #000000;
}

#model-selector {
    dock: top;
    height: 3;
    background: #18181B;
    border-bottom: solid #27272A;
    padding: 0 2;
    color: #FAFAFA;
}

#chat-scroll {
    height: 1fr;
    background: #000000;
    padding: 2;
    scrollbar-background: #000000;
    scrollbar-color: #27272A;
    scrollbar-color-hover: #FFFFFF;
    scrollbar-size: 1 1;
}

#chat-scroll MessageBubble {
    margin: 1 0 0 0;
    padding: 0;
    width: 1fr;
    height: auto;
    background: transparent;
}

#chat-scroll MessageBubble.user {
    background: transparent;
}

#chat-scroll MessageBubble.assistant {
    background: transparent;
}

#thinking {
    dock: bottom;
    height: auto;
    background: #000000;
    padding: 1 2;
    color: #FFFFFF;
    opacity: 0.7;
}

/* Input Area */
#input-area {
    dock: bottom;
    height: auto;
    min-height: 5;
    max-height: 12;
    background: #000000;
    padding: 0 2 1 2;
}

#prompt-box {
    background: #18181B;
    border: solid #27272A;
    padding: 0 1;
    height: auto;
    min-height: 3;
}

#prompt-box:focus-within {
    border: solid #FFFFFF;
}

#user-input {
    height: auto;
    min-height: 1;
    background: #18181B;
    border: none;
    color: #FAFAFA;
    padding: 0 1;
}

#user-input:focus {
    border: none;
    background: #18181B;
}

#user-input > .input--placeholder {
    color: #52525B;
}

#input-actions {
    height: auto;
    padding: 1 1 0 1;
    background: #000000;
}

.input-btn {
    min-width: 10;
    height: 2;
    margin: 0 1 0 0;
    background: transparent;
    color: #64748B;
    border: none;
}

.input-btn:hover {
    color: #FFFFFF;
    background: #18181B;
}

/* Status Bar */
#status-bar {
    dock: bottom;
    height: 1;
    background: #18181B;
    color: #64748B;
    border-top: solid #27272A;
}

/* Modal Styles - Claude Code style */
.model-modal {
    background: #27272A;
    border: solid #FFFFFF;
    padding: 1 2;
    margin: 2 4;
    height: auto;
    max-height: 25;
}

.modal-title {
    color: #FAFAFA;
    text-style: bold;
    padding: 0 0 1 0;
}

.modal-search {
    background: #000000;
    border: solid #27272A;
    color: #FAFAFA;
    width: 1fr;
    margin: 0 0 1 0;
}

.modal-search:focus {
    border: solid #FFFFFF;
}

.model-list {
    height: auto;
    max-height: 15;
    background: #000000;
    color: #A1A1AA;
    scrollbar-size: 1 1;
}

.model-item {
    height: 2;
    padding: 0 1;
    color: #A1A1AA;
}

.model-item:hover {
    background: #18181B;
    color: #FAFAFA;
}

.model-item.-highlight {
    background: #18181B;
    color: #FFFFFF;
}

.modal-actions {
    height: auto;
    padding: 1 0 0 0;
}

.modal-btn {
    min-width: 10;
    height: 2;
    margin: 0 1 0 0;
    background: #18181B;
    color: #A1A1AA;
    border: none;
}

.modal-btn:hover {
    background: #3F3F46;
    color: #FAFAFA;
}

.modal-btn.primary {
    background: #FFFFFF;
    color: #000000;
}

.modal-btn.primary:hover {
    background: #B3B3B3;
}

/* Settings Container */
.settings-container {
    height: auto;
    padding: 1 2;
    background: #18181B;
    border: solid #27272A;
    margin: 1 0;
}

.settings-text {
    color: #A1A1AA;
    padding: 0 1;
}

.settings-field, .search-field, .attach-field, .model-field {
    background: #000000;
    border: solid #27272A;
    color: #FAFAFA;
    width: 1fr;
    margin: 0 1 0 0;
}

.settings-field:focus, .search-field:focus, .attach-field:focus, .model-field:focus {
    border: solid #FFFFFF;
}

/* Prompt Containers */
.search-prompt, .attach-prompt, .agent-prompt {
    background: #18181B;
    border: solid #FFFFFF;
    padding: 1 1;
    margin: 1 0;
    height: auto;
}

.search-prompt-title, .attach-prompt-title, .agent-prompt-title {
    color: #FFFFFF;
    text-style: bold;
    padding: 0 1 1 1;
}

/* Input Styling */
Input {
    background: #000000;
    color: #FAFAFA;
    border: solid #27272A;
}

Input:focus {
    border: solid #FFFFFF;
}
"""


class ModelSelectScreen(ModalScreen):
    """Modal screen for model selection with Claude Code styling."""
    
    CSS = """
    ModelSelectScreen {
        align: center middle;
    }
    
    ModelSelectScreen > Container {
        width: 60;
        height: auto;
        max-height: 35;
        background: #27272A;
        border: solid #FFFFFF;
        padding: 1;
    }
    
    .modal-header {
        height: 2;
        padding: 0 1;
        background: #18181B;
        border-bottom: solid #27272A;
        margin-bottom: 1;
    }
    
    .modal-title {
        color: #FAFAFA;
        text-style: bold;
    }
    
    .search-box {
        height: 3;
        margin-bottom: 1;
    }
    
    .model-search {
        width: 1fr;
        background: #000000;
        border: solid #27272A;
        color: #FAFAFA;
    }
    
    .model-search:focus {
        border: solid #FFFFFF;
    }
    
    .model-list-container {
        height: auto;
        max-height: 20;
        background: #000000;
    }
    
    .model-list {
        height: auto;
        max-height: 20;
    }
    
    .model-item {
        height: 2;
        padding: 0 1;
        color: #A1A1AA;
    }
    
    .model-item:hover {
        background: #18181B;
        color: #FAFAFA;
    }
    
    .model-item.-highlight {
        background: #18181B;
        color: #FFFFFF;
    }
    
    .modal-footer {
        height: 3;
        padding: 1 0 0 0;
        border-top: solid #27272A;
        margin-top: 1;
    }
    
    .modal-btn {
        min-width: 12;
        height: 2;
        margin: 0 1 0 0;
        background: #18181B;
        color: #A1A1AA;
        border: none;
    }
    
    .modal-btn:hover {
        background: #3F3F46;
        color: #FAFAFA;
    }
    
    .modal-btn.primary {
        background: #FFFFFF;
        color: #000000;
    }
    
    .modal-btn.primary:hover {
        background: #B3B3B3;
    }
    """
    
    BINDINGS = [
        Binding("escape", "close", "Close", show=False),
    ]
    
    def __init__(self, models: list[dict], current_model: str = "", **kwargs):
        self.models = models
        self.current_model = current_model
        self._filtered = models
        super().__init__(**kwargs)
    
    def compose(self) -> ComposeResult:
        with Container():
            with Vertical(classes="modal-header"):
                yield Label("◆ Select Model", classes="modal-title")
            
            with Horizontal(classes="search-box"):
                yield Input(
                    placeholder="Search models…",
                    id="model-search",
                    classes="model-search"
                )
            
            with Vertical(classes="model-list-container"):
                yield ListView(
                    *[self._make_item(m) for m in self._filtered[:20]],
                    id="model-list",
                    classes="model-list"
                )
            
            with Horizontal(classes="modal-footer"):
                yield Button("Select", id="select-btn", variant="primary", classes="modal-btn primary")
                yield Button("Cancel", id="cancel-btn", classes="modal-btn")
    
    def _make_item(self, model: dict) -> ListItem:
        item = ListItem(Label(f"  {model['id']}"), classes="model-item")
        item.model_id = model["id"]
        return item
    
    def on_mount(self):
        self.query_one("#model-search", Input).focus()
        lv = self.query_one("#model-list", ListView)
        for i, item in enumerate(lv.children):
            if hasattr(item, "model_id") and item.model_id == self.current_model:
                lv.index = i
                break
    
    @on(Input.Changed, "#model-search")
    def handle_search(self, event: Input.Changed):
        query = event.value.lower().strip()
        if query:
            self._filtered = [m for m in self.models if query in m["id"].lower()]
        else:
            self._filtered = self.models
        
        lv = self.query_one("#model-list", ListView)
        lv.clear()
        for m in self._filtered[:20]:
            lv.append(self._make_item(m))
    
    @on(ListView.Selected, "#model-list")
    def handle_select(self, event: ListView.Selected):
        if hasattr(event.item, "model_id"):
            self.dismiss(str(event.item.model_id))
    
    @on(Button.Pressed, "#select-btn")
    def handle_select_btn(self):
        lv = self.query_one("#model-list", ListView)
        if lv.highlighted_child and hasattr(lv.highlighted_child, "model_id"):
            self.dismiss(lv.highlighted_child.model_id)
    
    @on(Button.Pressed, "#cancel-btn")
    def handle_cancel(self):
        self.dismiss(None)
    
    def action_close(self):
        self.dismiss(None)


class LeocodeApp(App):
    """Professional AI Coding Agent Application."""
    
    CSS = CSS
    
    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", show=False),
    ]
    
    TITLE = "leocode"
    SUB_TITLE = ""
    
    config: reactive[Config] = reactive(lambda: Config.load())
    current_model: reactive[str] = reactive("")
    available_models: reactive[list[dict]] = reactive(list)
    is_thinking: reactive[bool] = reactive(False)
    chat_messages: reactive[list[dict]] = reactive(list)
    sidebar_visible: reactive[bool] = reactive(True)
    rag_enabled: reactive[bool] = reactive(True)
    current_conv_id: reactive[str] = reactive("")
    attached_files: reactive[list[str]] = reactive(list)
    
    def __init__(self, working_dir: str = "", **kwargs):
        super().__init__(**kwargs)
        self.working_dir = working_dir or os.getcwd()
        self.client: Optional[RouterClient] = None
        self.rag: Optional[RAGStore] = None
        self.search: Optional[WebSearch] = None
        self.agent: Optional[AgentTools] = None
        self.mcp: Optional[MCPManager] = None
        self._stream_task: Optional[asyncio.Task] = None
        self._thinking_interval = None
        self._current_bubble: Optional[MessageBubble] = None
    
    def compose(self) -> ComposeResult:
        with Container(id="main-container"):
            with Vertical(id="sidebar"):
                yield Static("  claude", classes="sidebar-header")
                with Horizontal(classes="sidebar-actions"):
                    yield Button("+ New", id="btn-new", variant="primary", classes="sidebar-btn")
                yield Static("  Recents", classes="sidebar-section")
                yield ListView(id="conv-list", classes="conv-list")
                yield Static(classes="sidebar-spacer")
                yield Static("  /help commands", classes="sidebar-footer")
            
            with Vertical(id="chat-area"):
                yield ModelSelector(id="model-selector")
                yield ScrollableContainer(id="chat-scroll")
                yield ThinkingIndicator(id="thinking")
                
                with Container(id="input-area"):
                    with Vertical(id="prompt-box"):
                        yield Input(
                            id="user-input",
                            placeholder="Type a command or task…",
                        )
                    with Horizontal(id="input-actions"):
                        yield Button("send ↵", id="btn-send", variant="primary", classes="input-btn")
                        yield Button("model", id="btn-model", classes="input-btn")
                        yield Button("agent", id="btn-agent", classes="input-btn")
                        yield Button("attach", id="btn-attach", classes="input-btn")
                        yield Button("search", id="btn-search", classes="input-btn")
        
        yield StatusBar(id="status-bar")
    
    def on_mount(self):
        self._init_systems()
        self._load_conversations()
        asyncio.create_task(self._fetch_models())
        if self.config.model:
            self.current_model = self.config.model
        self._update_status()
        self.query_one("#user-input", Input).focus()
        self.action_new_chat()
    
    def _init_systems(self):
        self.client = RouterClient(self.config)
        self.agent = AgentTools(self.working_dir)
        
        if self.config.rag_enabled:
            try:
                self.rag = RAGStore(str(RAG_DIR / "default"))
            except Exception:
                self.rag = None
        
        if self.config.web_search_enabled:
            self.search = WebSearch(self.config.base_url, self.config.api_key)
        
        if self.config.mcp_enabled and self.config.mcp_servers:
            self.mcp = MCPManager(self.config)
        
        status = self.query_one("#status-bar", StatusBar)
        status.working_dir = self.working_dir
    
    def _load_conversations(self):
        convs = self.query_one("#conv-list", ListView)
        conversations = []
        if CONVERSATIONS_DIR.exists():
            for f in sorted(CONVERSATIONS_DIR.glob("*.json"), reverse=True)[:20]:
                try:
                    data = json.loads(f.read_text())
                    conversations.append({"id": f.stem, "title": data.get("title", f.stem)})
                except Exception:
                    continue
        
        convs.clear()
        for c in conversations:
            title = c["title"].replace("\n", " ").strip()[:28] or c["id"]
            item = ListItem(Label(title))
            item.conv_id = c["id"]
            convs.append(item)
    
    async def _fetch_models(self):
        if not self.client:
            return
        
        try:
            models = await self.client.list_models()
            if models:
                self.available_models = models
                if not self.current_model and models:
                    self.current_model = models[0]["id"]
                    self.config.model = self.current_model
                    self.config.save()
                
                selector = self.query_one("#model-selector", ModelSelector)
                selector.selected_model = self.current_model
                selector.models_count = len(models)
                self._update_status()
                
                for banner in self.query("WelcomeBanner"):
                    banner.model = self.current_model
                    banner.refresh()
        except Exception as e:
            self.log.error(f"Failed to fetch models: {e}")
    
    def _update_status(self):
        status = self.query_one("#status-bar", StatusBar)
        status.model_name = self.current_model or "no model"
        status.rag_count = self.rag.count() if self.rag else 0
        status.mcp_count = len(self.mcp.get_all_tools()) if self.mcp else 0
        status.working_dir = self.working_dir
    
    def _process_command(self, text: str) -> bool:
        """Process slash commands. Returns True if handled."""
        text = text.strip()
        
        if not text.startswith("/"):
            return False
        
        parts = text.split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        if cmd in ["/model", "/m"]:
            self._open_model_modal()
            return True
        
        elif cmd in ["/new", "/n"]:
            self.action_new_chat()
            return True
        
        elif cmd in ["/agent", "/a"]:
            if args:
                self._open_agent_mode(args)
            else:
                self._show_agent_dir_prompt()
            return True
        
        elif cmd in ["/attach", "/f"]:
            if args:
                asyncio.create_task(self._do_attach(args))
            else:
                self._show_attach_prompt()
            return True
        
        elif cmd in ["/search", "/s"]:
            if args:
                asyncio.create_task(self._do_web_search(args))
            else:
                self._show_search_prompt()
            return True
        
        elif cmd in ["/rag", "/r"]:
            self.action_toggle_rag()
            self._add_message("assistant", f"RAG {'enabled' if self.rag_enabled else 'disabled'}.", self.current_model)
            return True
        
        elif cmd in ["/settings", "/config"]:
            self._show_settings_view()
            return True
        
        elif cmd in ["/save"]:
            self.action_save_chat()
            self._add_message("assistant", "Conversation saved.", self.current_model)
            return True
        
        elif cmd in ["/clear"]:
            self.action_clear_chat()
            return True
        
        elif cmd in ["/help", "/h", "/?"]:
            self._show_help()
            return True
        
        elif cmd in ["/quit", "/q", "/exit"]:
            self.exit()
            return True
        
        else:
            self._add_message("assistant", f"Unknown command: {cmd}. Type /help for available commands.", "")
            return True
        
        return False
    
    def _show_help(self):
        """Show help message with all commands."""
        help_text = """Commands

  /model   Select AI model from 9router
  /new     Start new session
  /agent   Set agent working directory
  /attach  Attach file to conversation
  /search  Web search
  /rag     Toggle RAG on/off
  /settings  Configure settings
  /save    Save conversation
  /clear   Clear chat
  /help    Show this help
  /quit    Exit application"""
        
        self._add_message("assistant", help_text, self.current_model)
    
    # ── Actions ──────────────────────────────────────────────
    
    def action_new_chat(self):
        self.chat_messages = []
        self.current_conv_id = ""
        self.attached_files = []
        scroll = self.query_one("#chat-scroll", ScrollableContainer)
        scroll.remove_children()
        scroll.mount(WelcomeBanner(cwd=self.working_dir, model=self.current_model))
    
    def action_save_chat(self):
        if not self.chat_messages:
            return
        
        conv_id = self.current_conv_id or str(uuid.uuid4())[:8]
        title = self.chat_messages[0]["content"][:40] if self.chat_messages else "Untitled"
        self.current_conv_id = conv_id
        
        CONVERSATIONS_DIR.mkdir(parents=True, exist_ok=True)
        data = {"title": title, "messages": self.chat_messages}
        (CONVERSATIONS_DIR / f"{conv_id}.json").write_text(json.dumps(data, indent=2))
        self._load_conversations()
    
    def action_clear_chat(self):
        self.chat_messages = []
        self.attached_files = []
        scroll = self.query_one("#chat-scroll", ScrollableContainer)
        scroll.remove_children()
        self.action_new_chat()
    
    def action_toggle_rag(self):
        self.rag_enabled = not self.rag_enabled
    
    def exit(self):
        self.action_quit()
    
    # ── UI Methods ──────────────────────────────────────────
    
    def _add_message(self, role: str, content: str, model: str = "", thinking: str = ""):
        scroll = self.query_one("#chat-scroll", ScrollableContainer)
        bubble = MessageBubble(role=role, content=content, model=model, thinking=thinking)
        scroll.mount(bubble)
        scroll.scroll_end(animate=False)
        return bubble
    
    def _open_model_modal(self):
        def handle_result(model_id):
            if model_id:
                self.current_model = model_id
                self.config.model = model_id
                self.config.save()
                self.query_one("#model-selector", ModelSelector).selected_model = model_id
                self._update_status()
                self._add_message("assistant", f"Model selected: {model_id}", self.current_model)
        
        self.push_screen(
            ModelSelectScreen(self.available_models, self.current_model),
            handle_result
        )
    
    def _show_search_prompt(self):
        scroll = self.query_one("#chat-scroll", ScrollableContainer)
        existing = scroll.query(".search-prompt")
        for e in existing:
            e.remove()
        
        container = Vertical(
            Static("  web search", classes="search-prompt-title"),
            Horizontal(
                Input(placeholder="Search query…", id="search-input", classes="search-field"),
                Button("go", id="btn-search-go", variant="primary"),
                Button("esc", id="btn-search-close"),
            ),
            classes="search-prompt"
        )
        scroll.mount(container)
        scroll.scroll_end(animate=False)
        self.query_one("#search-input", Input).focus()
    
    def _show_attach_prompt(self):
        scroll = self.query_one("#chat-scroll", ScrollableContainer)
        existing = scroll.query(".attach-prompt")
        for e in existing:
            e.remove()
        
        container = Vertical(
            Static("  attach file", classes="attach-prompt-title"),
            Horizontal(
                Input(placeholder="File or directory path…", id="attach-input", classes="attach-field"),
                Button("attach", id="btn-attach-go", variant="primary"),
                Button("esc", id="btn-attach-close"),
            ),
            classes="attach-prompt"
        )
        scroll.mount(container)
        scroll.scroll_end(animate=False)
        self.query_one("#attach-input", Input).focus()
    
    def _show_agent_dir_prompt(self):
        scroll = self.query_one("#chat-scroll", ScrollableContainer)
        existing = scroll.query(".agent-prompt")
        for e in existing:
            e.remove()
        
        container = Vertical(
            Static("  agent directory", classes="agent-prompt-title"),
            Horizontal(
                Input(placeholder=f"Directory (current: {self.working_dir})", id="agent-dir-input"),
                Button("open", id="btn-agent-go", variant="primary"),
                Button("esc", id="btn-agent-close"),
            ),
            classes="agent-prompt"
        )
        scroll.mount(container)
        scroll.scroll_end(animate=False)
        self.query_one("#agent-dir-input", Input).focus()
    
    def _show_settings_view(self):
        scroll = self.query_one("#chat-scroll", ScrollableContainer)
        existing = scroll.query(".settings-container")
        for e in existing:
            e.remove()
        
        settings_content = f"""  Settings
  ─────────────────────────────
  endpoint     {self.config.base_url}
  api key      {self.config.api_key[:10]}…
  model        {self.current_model or 'auto'}
  temperature  {self.config.temperature}
  max tokens   {self.config.max_tokens}
  rag          {'on' if self.config.rag_enabled else 'off'}
  search       {'on' if self.config.web_search_enabled else 'off'}
  mcp          {'on' if self.config.mcp_enabled else 'off'}
  cwd          {self.working_dir}

  leave blank to keep current"""
        
        container = Vertical(
            Static(settings_content, classes="settings-text"),
            Horizontal(
                Input(placeholder="Base URL", id="set-url", classes="settings-field"),
                Input(placeholder="API Key", id="set-key", classes="settings-field"),
            ),
            Horizontal(
                Input(placeholder="Model", id="set-model", classes="settings-field"),
                Input(placeholder="Temperature", id="set-temp", classes="settings-field"),
            ),
            Horizontal(
                Input(placeholder="Max Tokens", id="set-tokens", classes="settings-field"),
                Input(placeholder="Working Dir", id="set-workdir", classes="settings-field"),
            ),
            Horizontal(
                Button("save", id="btn-settings-save", variant="primary"),
                Button("close", id="btn-settings-close"),
            ),
            classes="settings-container"
        )
        scroll.mount(container)
        scroll.scroll_end(animate=False)
    
    # ── Event Handlers ──────────────────────────────────────
    
    @on(Button.Pressed, "#btn-new")
    def handle_new(self):
        self.action_new_chat()
    
    @on(Button.Pressed, "#btn-send")
    async def handle_send(self):
        await self._send_message()
    
    @on(Button.Pressed, "#btn-model")
    def handle_model_btn(self):
        self._open_model_modal()
    
    @on(Button.Pressed, "#btn-agent")
    def handle_agent_btn(self):
        self._show_agent_dir_prompt()
    
    @on(Button.Pressed, "#btn-attach")
    def handle_attach_btn(self):
        self._show_attach_prompt()
    
    @on(Button.Pressed, "#btn-search")
    def handle_search_btn(self):
        self._show_search_prompt()
    
    @on(Button.Pressed, "#btn-search-go")
    async def handle_search_go(self):
        query = self.query_one("#search-input", Input).value.strip()
        if not query:
            return
        self.query_one(".search-prompt").remove()
        await self._do_web_search(query)
    
    @on(Button.Pressed, "#btn-search-close")
    def handle_search_close(self):
        self.query_one(".search-prompt").remove()
    
    @on(Button.Pressed, "#btn-attach-go")
    async def handle_attach_go(self):
        path = self.query_one("#attach-input", Input).value.strip()
        if not path:
            return
        self.query_one(".attach-prompt").remove()
        await self._do_attach(path)
    
    @on(Button.Pressed, "#btn-attach-close")
    def handle_attach_close(self):
        self.query_one(".attach-prompt").remove()
    
    @on(Button.Pressed, "#btn-agent-go")
    async def handle_agent_go(self):
        path = self.query_one("#agent-dir-input", Input).value.strip() or self.working_dir
        self.query_one(".agent-prompt").remove()
        self._open_agent_mode(path)
    
    @on(Button.Pressed, "#btn-agent-close")
    def handle_agent_close(self):
        self.query_one(".agent-prompt").remove()
    
    @on(Button.Pressed, "#btn-settings-save")
    async def handle_settings_save(self):
        url = self.query_one("#set-url", Input).value.strip()
        key = self.query_one("#set-key", Input).value.strip()
        model = self.query_one("#set-model", Input).value.strip()
        temp = self.query_one("#set-temp", Input).value.strip()
        tokens = self.query_one("#set-tokens", Input).value.strip()
        workdir = self.query_one("#set-workdir", Input).value.strip()
        
        if url:
            self.config.base_url = url
        if key:
            self.config.api_key = key
        if model:
            self.current_model = model
            self.config.model = model
        if temp:
            try:
                self.config.temperature = float(temp)
            except ValueError:
                pass
        if tokens:
            try:
                self.config.max_tokens = int(tokens)
            except ValueError:
                pass
        if workdir:
            self.working_dir = workdir
            self.agent = AgentTools(workdir)
        
        self.config.save()
        if url or key:
            self.client = RouterClient(self.config)
            await self._fetch_models()
        
        self.query_one(".settings-container").remove()
        self._add_message("assistant", "Settings saved.", self.current_model)
    
    @on(Button.Pressed, "#btn-settings-close")
    def handle_settings_close(self):
        self.query_one(".settings-container").remove()
    
    @on(ListView.Selected, "#conv-list")
    async def handle_conv_select(self, event: ListView.Selected):
        if hasattr(event.item, "conv_id") and event.item.conv_id:
            self._load_conversation(event.item.conv_id)
    
    @on(Input.Submitted, "#user-input")
    async def handle_input_submit(self):
        await self._send_message()
    
    def _load_conversation(self, conv_id: str):
        f = CONVERSATIONS_DIR / f"{conv_id}.json"
        if not f.exists():
            return
        
        data = json.loads(f.read_text())
        self.current_conv_id = conv_id
        self.chat_messages = data.get("messages", [])
        
        scroll = self.query_one("#chat-scroll", ScrollableContainer)
        scroll.remove_children()
        
        for msg in self.chat_messages:
            self._add_message(
                msg["role"], 
                msg["content"], 
                msg.get("model", ""),
                msg.get("thinking", "")
            )
    
    # ── Core Messaging Logic ─────────────────────────────────
    
    async def _send_message(self):
        input_widget = self.query_one("#user-input", Input)
        user_input = input_widget.value.strip()
        
        if not user_input:
            return
        
        input_widget.value = ""
        
        # Check for commands
        if self._process_command(user_input):
            return
        
        # Build context
        context_parts = []
        
        for fpath in self.attached_files:
            info = get_file_info(fpath)
            context_parts.append(f"[Attached file: {fpath}]\n{info}")
        self.attached_files = []
        
        if self.rag_enabled and self.rag:
            try:
                rag_results = self.rag.query(user_input, n_results=self.config.rag_chunks)
                if rag_results:
                    rag_ctx = "\n".join([
                        f"[RAG: {r['source']} chunk {r['chunk']}]\n{r['content']}"
                        for r in rag_results
                    ])
                    context_parts.append(f"[RAG Context]\n{rag_ctx}")
            except Exception:
                pass
        
        full_input = user_input
        if context_parts:
            full_input = user_input + "\n\n" + "\n\n".join(context_parts)
        
        # Add user message
        self.chat_messages.append({"role": "user", "content": user_input})
        self._add_message("user", user_input)
        
        # Check model
        if not self.current_model:
            self._add_message("assistant", "ERROR: No model selected. Use /model to choose one.", "")
            return
        
        # Build messages for API
        messages = [{"role": "system", "content": self.config.system_prompt}]
        for msg in self.chat_messages[-20:]:
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages[-1]["content"] = full_input
        
        # Get tools
        tools = self.agent.tool_definitions if self.agent else []
        if self.mcp:
            tools.extend(self.mcp.get_openai_tools())
        
        # Start thinking indicator
        self.is_thinking = True
        thinking = self.query_one("#thinking", ThinkingIndicator)
        thinking.active = True
        thinking.status = "thinking"
        self._start_thinking_animation()
        
        try:
            await self._stream_response(messages, tools)
        except Exception as e:
            error_msg = f"ERROR: {e}\n\nTry checking your API configuration or model selection."
            self._add_message("assistant", error_msg, self.current_model)
            self.log.error(f"Error: {e}")
        finally:
            self.is_thinking = False
            thinking.active = False
            self._stop_thinking_animation()
    
    async def _stream_response(self, messages: list[dict], tools: list[dict] = None):
        full_response = []
        thinking_content = []
        in_thinking = False
        scroll = self.query_one("#chat-scroll", ScrollableContainer)
        
        bubble = MessageBubble(role="assistant", content="", model=self.current_model, thinking="")
        scroll.mount(bubble)
        scroll.scroll_end(animate=False)
        
        thinking = self.query_one("#thinking", ThinkingIndicator)
        
        try:
            if tools:
                stream = await self.client.client.chat.completions.create(
                    model=self.current_model,
                    messages=messages,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                    tools=tools,
                    stream=True,
                )
                
                tool_calls = {}
                
                async for chunk in stream:
                    delta = chunk.choices[0].delta if chunk.choices else None
                    if not delta:
                        continue
                    
                    if delta.content:
                        content = delta.content
                        
                        if "<thinking>" in content or in_thinking:
                            in_thinking = True
                            thinking_content.append(content.replace("<thinking>", "").replace("</thinking>", ""))
                            if "</thinking>" in content:
                                in_thinking = False
                                thinking.status = "processing"
                        else:
                            full_response.append(content)
                        
                        bubble.raw_content = "".join(full_response)
                        if thinking_content:
                            bubble.thinking_content = "".join(thinking_content)
                        bubble.refresh()
                        scroll.scroll_end(animate=False)
                    
                    if delta.tool_calls:
                        thinking.status = "executing tools"
                        for tc in delta.tool_calls:
                            idx = tc.index
                            if idx not in tool_calls:
                                tool_calls[idx] = {"id": tc.id or "", "name": "", "arguments": ""}
                            if tc.id:
                                tool_calls[idx]["id"] = tc.id
                            if tc.function:
                                if tc.function.name:
                                    tool_calls[idx]["name"] = tc.function.name
                                if tc.function.arguments:
                                    tool_calls[idx]["arguments"] += tc.function.arguments
                
                if tool_calls:
                    for idx in sorted(tool_calls.keys()):
                        tc = tool_calls[idx]
                        name = tc["name"]
                        
                        try:
                            args = json.loads(tc["arguments"]) if tc["arguments"] else {}
                        except json.JSONDecodeError:
                            args = {}
                        
                        if self.agent:
                            result = self.agent.execute(name, args)
                        elif self.mcp:
                            result = await self.mcp.call_tool(name, args)
                        else:
                            result = f"Tool {name} not available"
                        
                        # Add tool call visualization
                        tool_call_div = (
                            f"┌ tool: {name}\n"
                            f"│ args: {json.dumps(args)[:200]}{'...' if len(str(args)) > 200 else ''}\n"
                            f"└ result: {result[:500]}{'...' if len(result) > 500 else ''}"
                        )
                        full_response.append("\n\n" + tool_call_div)
                        bubble.raw_content = "".join(full_response)
                        bubble.refresh()
                        
                        messages.append({
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [{
                                "id": tc["id"],
                                "type": "function",
                                "function": {"name": name, "arguments": tc["arguments"]},
                            }],
                        })
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tc["id"],
                            "content": result[:10000],
                        })
                    
                    thinking.status = "generating response"
                    stream2 = await self.client.client.chat.completions.create(
                        model=self.current_model,
                        messages=messages,
                        temperature=self.config.temperature,
                        max_tokens=self.config.max_tokens,
                        stream=True,
                    )
                    
                    more_response = []
                    async for chunk in stream2:
                        delta = chunk.choices[0].delta if chunk.choices else None
                        if delta and delta.content:
                            more_response.append(delta.content)
                            bubble.raw_content = "".join(full_response) + "".join(more_response)
                            bubble.refresh()
                            scroll.scroll_end(animate=False)
                    full_response.extend(more_response)
            
            else:
                async for text in self.client.chat(messages, model=self.current_model):
                    full_response.append(text)
                    bubble.raw_content = "".join(full_response)
                    bubble.refresh()
                    scroll.scroll_end(animate=False)
        
        except Exception as e:
            raise e
        
        final_content = "".join(full_response)
        final_thinking = "".join(thinking_content) if thinking_content else ""
        
        self.chat_messages.append({
            "role": "assistant",
            "content": final_content,
            "model": self.current_model,
            "thinking": final_thinking,
        })
        
        scroll.scroll_end(animate=False)
    
    async def _do_web_search(self, query: str):
        if not self.search:
            self._add_message("assistant", "Web search not configured.", "")
            return
        
        self._add_message("user", f"[Web Search] {query}")
        
        thinking = self.query_one("#thinking", ThinkingIndicator)
        thinking.active = True
        thinking.status = "searching"
        self._start_thinking_animation()
        
        try:
            results = await self.search.search(query)
            if results:
                result_text = f"Search results for: {query}\n\n"
                for i, r in enumerate(results, 1):
                    result_text += f"{i}. {r.get('title', 'N/A')}\n   {r.get('url', '')}\n   {r.get('snippet', '')}\n\n"
                
                self.chat_messages.append({"role": "user", "content": f"[Web Search] {query}"})
                messages = [{"role": "system", "content": self.config.system_prompt}]
                messages.extend(self.chat_messages[-10:])
                messages.append({"role": "user", "content": f"Based on these search results:\n{result_text}\nAnswer: {query}"})
                
                response = []
                async for text in self.client.chat(messages, model=self.current_model):
                    response.append(text)
                
                self._add_message("assistant", "".join(response), self.current_model)
            else:
                self._add_message("assistant", f"No results for: {query}", self.current_model)
        except Exception as e:
            self._add_message("assistant", f"Search error: {e}", self.current_model)
        finally:
            thinking.active = False
            self._stop_thinking_animation()
    
    async def _do_attach(self, path: str):
        attachment = load_file(path)
        if not attachment:
            self._add_message("assistant", f"Could not read: {path}", "")
            return
        
        self.attached_files.append(path)
        preview = attachment.content[:2000]
        if len(attachment.content) > 2000:
            preview += f"\n... ({len(attachment.content)} chars total)"
        
        self._add_message("user", f"[Attached: {attachment.name}]\n{preview}")
        self.chat_messages.append({"role": "user", "content": f"[File attached: {attachment.name}]\n{preview}"})
    
    def _open_agent_mode(self, path: str):
        self.working_dir = path
        self.agent = AgentTools(path)
        
        status = self.query_one("#status-bar", StatusBar)
        status.working_dir = path
        
        dir_info = get_file_info(path)
        self._add_message(
            "assistant", 
            f"Agent mode activated in: {path}\n\n{dir_info}\n\nI can now read, write, edit files and run commands in this directory.", 
            self.current_model
        )
        
        self.chat_messages.append({
            "role": "system",
            "content": f"Agent mode activated in directory: {path}",
        })
    
    def _start_thinking_animation(self):
        self._stop_thinking_animation()
        indicator = self.query_one("#thinking", ThinkingIndicator)
        self._thinking_interval = self.set_interval(
            0.1, 
            lambda: indicator.advance() if self.is_thinking else None
        )
    
    def _stop_thinking_animation(self):
        if self._thinking_interval:
            self._thinking_interval.stop()
            self._thinking_interval = None


def run_app(working_dir: str = ""):
    app = LeocodeApp(working_dir=working_dir)
    app.run()


if __name__ == "__main__":
    run_app()

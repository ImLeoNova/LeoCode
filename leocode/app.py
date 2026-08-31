"""Leocode — AI coding agent TUI with Claude Code visual style.

Full reconstruction based on Claude Code screenshots.
Single-column layout: Header → Scrollable Content → Fixed Input → Status Bar
"""

import asyncio
import json
import os
import re
import subprocess
import uuid
import time
from datetime import datetime
from typing import Optional

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical, Horizontal, ScrollableContainer
from textual.widgets import Static, Input, OptionList
from textual.reactive import reactive
from textual import on

from .config import Config, CONVERSATIONS_DIR, RAG_DIR
from .client import RouterClient, StreamChunk, ToolCallDelta
from .rag import RAGStore
from .search import WebSearch
from .agent import AgentTools
from .mcp_client import MCPManager
from .file_ops import load_file
from .agent_state import AgentStateManager, AgentState

from .events import EventBus, Event, EventType
from .permissions import PermissionEngine, PermissionAction, RiskLevel
from .tools.registry import ToolRegistry, ToolCategory, ToolSource
from .tools.filesystem import register_filesystem_tools
from .tools.search_tools import register_search_tools
from .tools.execution import register_execution_tools
from .tools.agent_tools import register_agent_tools
from .tools.web import register_web_tools
from .tools.code_intel import register_code_intel_tools
from .tools.extensibility import register_extensibility_tools
from .executor import ToolExecutor, ExecutionStatus
from .todo import TodoManager, TodoStatus, TodoPriority

from .ui.theme import CSS, CLAUDE, TEXT, TEXT_SECONDARY, TEXT_DIM, SUCCESS, PROCESSING, ERROR, short_model
from .ui.widgets import (
    WelcomeBanner, MessageBubble, ToolCard,
    SlashMenu, SLASH_COMMANDS,
    DiffWidget, InlinePermission, ThinkingIndicator,
)
from .ui.working_status import ProcessingStatus
from .ui.screens import ModelSelectScreen, SessionSelectScreen, HelpScreen, CommandPalette
from .ui.approval import ApprovalDialog
from .ui.tool_activity import ToolActivityFeed, ToolActivityItem
from .ui.todo_panel import TodoPanel


def _extract_thinking(content: str) -> tuple[str, str]:
    """Extract thinking content from response if present."""
    pattern = r"<thinking>(.*?)</thinking>"
    match = re.search(pattern, content, re.DOTALL)
    if match:
        thinking = match.group(1).strip()
        response = content[:match.start()] + content[match.end():]
        return thinking, response.strip()
    return "", content


class LeocodeApp(App):
    CSS = CSS

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", show=False),
        Binding("ctrl+n", "new_chat", "New", show=False),
        Binding("ctrl+m", "select_model", "Model", show=False),
        Binding("ctrl+p", "palette", "Palette", show=False),
        Binding("ctrl+l", "sessions", "Sessions", show=False),
        Binding("question_mark", "help", "Help", show=False),
        Binding("tab", "toggle_mode", "Mode", show=False, priority=True),
        Binding("escape", "interrupt", "Interrupt", show=False),
        Binding("f1", "help", "Help", show=False),
    ]

    TITLE = "LeoCode"
    SUB_TITLE = "AI coding agent"

    config: reactive[Config] = reactive(lambda: Config.load())
    current_model: reactive[str] = reactive("")
    available_models: reactive[list[dict]] = reactive(list)
    is_thinking: reactive[bool] = reactive(False)
    chat_messages: reactive[list[dict]] = reactive(list)
    rag_enabled: reactive[bool] = reactive(True)
    current_conv_id: reactive[str] = reactive("")
    attached_files: reactive[list[str]] = reactive(list)
    agent_mode: reactive[str] = reactive("build")
    slash_open: reactive[bool] = reactive(False)

    def __init__(self, working_dir: str = "", **kwargs):
        super().__init__(**kwargs)
        self.working_dir = working_dir or os.getcwd()
        self.client: Optional[RouterClient] = None
        self.rag: Optional[RAGStore] = None
        self.search: Optional[WebSearch] = None
        self.agent: Optional[AgentTools] = None
        self.mcp: Optional[MCPManager] = None
        self._stream_task: Optional[asyncio.Task] = None
        self._current_bubble: Optional[MessageBubble] = None
        self._git_branch = self._detect_git_branch()
        self.agent_state: Optional[AgentStateManager] = None

        # Tool system
        self.events = EventBus()
        self.permissions = PermissionEngine(policy=self.config.permission_policy)
        self.tool_registry = ToolRegistry()
        self.tool_executor: Optional[ToolExecutor] = None
        self.todo_manager = TodoManager(events=self.events)
        self._activity_feed: Optional[ToolActivityFeed] = None
        self._todo_panel: Optional[TodoPanel] = None
        self._thinking_widget: Optional[ProcessingStatus] = None
        self._thinking_start_time: float = 0.0
        self._cancel_event = asyncio.Event()
        self._phrase_idx: int = 0
        self._phrase_timer = None

        # File snapshots for diffs
        self._file_snapshots: dict[str, str] = {}

    def compose(self) -> ComposeResult:
        """Claude Code layout structure:
        No header — full-screen transcript
        Scrollable content area (messages, tool calls)
        Fixed input area at bottom
        Status bar at very bottom
        """
        with Vertical(id="main"):
            # Scrollable content area — the entire top is transcript
            yield ScrollableContainer(id="chat-scroll")

            # Fixed input area — Claude Code style
            with Container(id="composer"):
                with Container(id="slash-menu"):
                    yield SlashMenu(id="slash-widget")
                with Horizontal(id="composer-input"):
                    yield Static(">", id="composer-prefix")
                    yield Input(id="user-input", placeholder="")

            # Status bar
            yield Static(id="status-bar")

    def on_mount(self):
        """Initialize system components and load state."""
        self._init_systems()
        self.agent_state = AgentStateManager(self)
        asyncio.create_task(self._fetch_models())
        if self.config.model:
            self.current_model = self.config.model
        self._update_status()
        self._update_header()
        self.query_one("#user-input", Input).focus()
        self.action_new_chat()

    def _detect_git_branch(self) -> str:
        """Detect current git branch."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=1,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return ""

    def _update_header(self):
        """Update header — Claude Code minimal style."""
        # Header is now minimal, just shows brand name
        # Model and path info shown in status bar
        pass

    def _smart_scroll(self):
        """Auto-scroll to bottom only if user is near the bottom."""
        try:
            scroll = self.query_one("#chat-scroll", ScrollableContainer)
            is_at_bottom = scroll.scroll_y >= (scroll.max_scroll_y - 4)
            if is_at_bottom:
                scroll.scroll_end(animate=False)
        except Exception:
            pass

    def _rotate_phrase(self):
        """Rotate through working phrases."""
        from .ui.status_config import WORKING_PHRASES
        if self._thinking_widget:
            self._phrase_idx = (self._phrase_idx + 1) % len(WORKING_PHRASES)
            self._thinking_widget.set_phrase(WORKING_PHRASES[self._phrase_idx])
            self._smart_scroll()

    def _init_systems(self):
        """Initialize all system components."""
        self.client = RouterClient(self.config)
        self.agent = AgentTools(self.working_dir)

        # Register all tools
        register_filesystem_tools(self.tool_registry, self.working_dir)
        register_search_tools(self.tool_registry, self.working_dir)
        register_execution_tools(self.tool_registry, self.working_dir)
        register_agent_tools(self.tool_registry, self.working_dir, app=self)
        register_web_tools(self.tool_registry, self.working_dir)
        register_code_intel_tools(self.tool_registry, self.working_dir)
        register_extensibility_tools(self.tool_registry, self.working_dir)

        # Wire up web search
        if self.config.web_search_enabled:
            self.search = WebSearch(self.config.base_url, self.config.api_key)
            self.tool_registry._web_search = self.search

        # Initialize RAG
        if self.config.rag_enabled:
            try:
                self.rag = RAGStore(str(RAG_DIR / "default"))
            except Exception:
                self.rag = None

        # Initialize MCP
        if self.config.mcp_enabled and self.config.mcp_servers:
            self.mcp = MCPManager(self.config)

        # Create tool executor
        async def approval_callback(meta, args, tool_name):
            return await self._show_inline_permission(meta, args, tool_name)

        self.tool_executor = ToolExecutor(
            registry=self.tool_registry,
            permissions=self.permissions,
            events=self.events,
            approval_callback=approval_callback,
        )

        self._activity_feed = ToolActivityFeed()
        self._todo_panel = TodoPanel()

        # Initialize status bar
        status = self.query_one("#status-bar", Static)
        status.working_dir = self.working_dir
        status.git_branch = self._git_branch
        status.agent_mode = self.agent_mode

    # ─────────────────────────────────────────────
    #  Inline Permission System
    # ─────────────────────────────────────────────

    async def _show_inline_permission(self, meta, args, tool_name: str) -> str:
        """Show inline permission prompt in chat scroll."""
        try:
            scroll = self.query_one("#chat-scroll", ScrollableContainer)
        except Exception:
            return await self._show_approval_dialog(meta, args, tool_name)

        description = self.permissions.describe_action(tool_name, args)
        risk = self.permissions.get_risk_level(tool_name)

        perm_widget = InlinePermission(
            action=description,
            tool_name=tool_name,
            risk_level=risk.value,
        )
        scroll.mount(perm_widget)
        scroll.scroll_end(animate=False)

        resolution_event = asyncio.Event()
        resolution_result = ["denied"]

        original_resolve = perm_widget.resolve

        def patched_resolve(approved: bool, always: bool = False):
            original_resolve(approved, always)
            resolution_result[0] = "always_allow" if (approved and always) else (
                "allow_once" if approved else "denied"
            )
            if always and approved:
                self.permissions.always_allow(tool_name, args)
            resolution_event.set()

        perm_widget.resolve = patched_resolve

        async def handle_key(event):
            if perm_widget.resolved:
                return
            if event.key == "1":
                patched_resolve(True, False)
                event.stop()
            elif event.key == "2":
                patched_resolve(True, True)
                event.stop()
            elif event.key == "3":
                patched_resolve(False)
                event.stop()
            elif event.key == "escape":
                patched_resolve(False)
                event.stop()

        self.on_key = handle_key
        await resolution_event.wait()
        self.on_key = self._original_on_key
        return resolution_result[0]

    def _original_on_key(self, event):
        """Default key handler."""
        if not self.slash_open or event.key not in ("down", "up"):
            return
        options = self.query_one("#slash-options", OptionList)
        if event.key == "down":
            options.action_cursor_down()
        else:
            options.action_cursor_up()
        event.stop()
        event.prevent_default()

    # ─────────────────────────────────────────────
    #  File Diff System
    # ─────────────────────────────────────────────

    def _snapshot_file(self, filepath: str):
        """Snapshot file content before modification."""
        full_path = os.path.join(self.working_dir, filepath)
        try:
            if os.path.exists(full_path):
                with open(full_path, "r", errors="replace") as f:
                    self._file_snapshots[filepath] = f.read()
            else:
                self._file_snapshots[filepath] = ""
        except Exception:
            self._file_snapshots[filepath] = ""

    def _show_file_diff(self, filepath: str, new_content: str):
        """Display diff for file operation."""
        try:
            scroll = self.query_one("#chat-scroll", ScrollableContainer)
        except Exception:
            return

        old_content = self._file_snapshots.get(filepath, "")
        is_new = old_content == "" and not os.path.exists(
            os.path.join(self.working_dir, filepath)
        )

        diff_widget = DiffWidget(
            filepath=filepath,
            is_new=is_new,
            old_content=old_content,
            new_content=new_content,
        )
        scroll.mount(diff_widget)
        self._smart_scroll()

        self._file_snapshots.pop(filepath, None)

        self.events.emit_sync(Event(
            type=EventType.DIFF_CREATED,
            data={"filepath": filepath, "is_new": is_new},
        ))

    def _should_track_file(self, tool_name: str, args: dict) -> bool:
        """Check if tool should generate diff."""
        return tool_name in ("write", "edit", "patch") and "path" in args

    # ─────────────────────────────────────────────
    #  Semantic Event System
    # ─────────────────────────────────────────────

    def _emit_semantic(self, event_type: EventType, **data):
        """Emit semantic event."""
        self.events.emit_sync(Event(type=event_type, data=data))

    # ─────────────────────────────────────────────
    #  Modal Approval (Fallback)
    # ─────────────────────────────────────────────

    async def _show_approval_dialog(self, meta, args, tool_name: str) -> str:
        """Modal approval dialog — fallback when inline unavailable."""
        description = self.permissions.describe_action(tool_name, args)
        risk = self.permissions.get_risk_level(tool_name)
        result = await self.push_screen_wait(
            ApprovalDialog(
                tool_name=tool_name,
                description=description,
                risk_level=risk.value,
                args=args,
            )
        )
        if result == "always_allow":
            self.permissions.always_allow(tool_name, args)
            return "allow_once"
        return result or "denied"

    def _list_sessions(self) -> list[dict]:
        """List saved sessions."""
        conversations = []
        if CONVERSATIONS_DIR.exists():
            for f in sorted(CONVERSATIONS_DIR.glob("*.json"), reverse=True)[:40]:
                try:
                    data = json.loads(f.read_text())
                    conversations.append({
                        "id": f.stem,
                        "title": data.get("title", f.stem),
                        "messages": data.get("messages", []),
                        "timestamp": data.get("timestamp", ""),
                    })
                except Exception:
                    continue
        return conversations

    def _save_conversation(self):
        """Save current conversation."""
        if not self.chat_messages:
            return
        if not self.current_conv_id:
            self.current_conv_id = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:6]
        title = ""
        for msg in self.chat_messages:
            if msg.get("role") == "user":
                title = msg.get("content", "").replace("\n", " ").strip()[:48]
                break
        CONVERSATIONS_DIR.mkdir(parents=True, exist_ok=True)
        data = {
            "title": title or "untitled",
            "messages": self.chat_messages,
            "timestamp": datetime.now().isoformat(),
            "model": self.current_model,
        }
        (CONVERSATIONS_DIR / f"{self.current_conv_id}.json").write_text(json.dumps(data, indent=2))

    def _open_session(self, conv_id: str):
        """Open saved session."""
        path = CONVERSATIONS_DIR / f"{conv_id}.json"
        if not path.exists():
            self._show_error(f"session not found: {conv_id}")
            return
        try:
            data = json.loads(path.read_text())
        except Exception as e:
            self._show_error(f"could not load session: {e}")
            return
        self.current_conv_id = conv_id
        self.chat_messages = data.get("messages", [])
        self.attached_files = []
        if self._todo_panel:
            self._todo_panel.update_tasks([])
            try:
                if self._todo_panel.parent:
                    self._todo_panel.remove()
            except Exception:
                pass
        scroll = self.query_one("#chat-scroll", ScrollableContainer)
        scroll.remove_children()
        if not self.chat_messages:
            scroll.mount(WelcomeBanner(cwd=self.working_dir, model=self.current_model))
        else:
            for msg in self.chat_messages:
                self._add_message(msg.get("role", "assistant"), msg.get("content", ""), msg.get("model", ""))
        self._update_status()

    async def _fetch_models(self):
        """Fetch available models."""
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
                self._update_status()
                self._update_header()
                for banner in self.query("WelcomeBanner"):
                    banner.model = self.current_model
                    banner.refresh()
        except Exception as e:
            self.log.error(f"Failed to fetch models: {e}")
            self._show_error(f"failed to fetch models: {e}\ncheck API config")

    def _update_status(self):
        """Update status bar with current state."""
        try:
            status = self.query_one("#status-bar", Static)
        except Exception:
            return

        # Build status text: mode indicator + context meter + model + status
        status_text = []

        # Mode indicator
        # Claude Code footer style
        # Mode indicator
        if self.agent_mode == "plan":
            status_text.append("⏸ plan mode")
        elif self.agent_mode == "build":
            status_text.append("⏸ manual mode")
        else:
            status_text.append(f"⏸ {self.agent_mode} mode")

        # Context meter
        msg_factor = min(len(self.chat_messages) * 2, 50)
        context_remaining = max(50, 100 - msg_factor)
        bar_len = 10
        filled = int(context_remaining / 100 * bar_len)
        bar = "█" * filled + "░" * (bar_len - filled)
        status_text.append(f"  · {context_remaining}% {bar}")

        # Model name
        status_text.append(f"  · {short_model(self.current_model) or 'no model'}")

        # Processing status
        if self.is_thinking:
            status_text.append("  · thinking")

        status.update(" ".join(status_text))

    def _show_banner_note(self, kind: str, message: str):
        """Show banner message in chat scroll."""
        try:
            scroll = self.query_one("#chat-scroll", ScrollableContainer)
        except Exception:
            return
        widget = Static(message, classes=f"{kind}-message")
        scroll.mount(widget)
        self._smart_scroll()

    def _show_error(self, message: str):
        self._show_banner_note("error", f"\u2717  {message}")

    def _show_warning(self, message: str):
        self._show_banner_note("warning", f"\u26A0  {message}")

    def _show_info(self, message: str):
        self._show_banner_note("info", f"\u2139  {message}")

    def _show_success(self, message: str):
        self._show_banner_note("success", f"\u2713  {message}")

    def _hide_slash(self):
        """Hide slash command menu."""
        self.slash_open = False
        try:
            self.query_one("#slash-menu").remove_class("visible")
        except Exception:
            pass

    def _show_slash(self, query: str):
        """Show slash command menu."""
        try:
            menu = self.query_one("#slash-widget", SlashMenu)
            box = self.query_one("#slash-menu")
        except Exception:
            return
        count = menu.update_query(query)
        if count:
            box.add_class("visible")
            self.slash_open = True
        else:
            box.remove_class("visible")
            self.slash_open = False

    def _process_command(self, text: str) -> bool:
        """Process slash command."""
        text = text.strip()
        if not text.startswith("/"):
            return False
        parts = text.split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        if cmd in ["/model", "/m"]:
            self._open_model_modal()
            return True
        if cmd in ["/new", "/n"]:
            self.action_new_chat()
            return True
        if cmd in ["/sessions", "/resume", "/continue"]:
            self.action_sessions()
            return True
        if cmd in ["/attach", "/f"]:
            if args:
                asyncio.create_task(self._do_attach(args))
            else:
                self._show_info("usage: /attach <path>")
            return True
        if cmd in ["/mode"]:
            self.action_toggle_mode()
            return True
        if cmd in ["/help", "/h", "/?"]:
            self.action_help()
            return True
        if cmd in ["/quit", "/q", "/exit"]:
            self.exit()
            return True
        if cmd in ["/clear"]:
            self.action_clear_chat()
            return True
        self._add_message("assistant", f"unknown command: {cmd}\ntype /help", "")
        return True

    def _run_shell(self, command: str):
        """Run shell command and display output."""
        scroll = self.query_one("#chat-scroll", ScrollableContainer)
        activity_item = ToolActivityItem(
            tool_name="shell",
            args={"command": command},
            execution_id=f"shell-{int(time.time())}",
        )
        activity_item.status = "running"
        scroll.mount(activity_item)
        self._smart_scroll()

        self._emit_semantic(EventType.TOOL_STARTED, tool="shell", command=command)

        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=30,
            )
            output = (result.stdout or result.stderr or "").strip() or "(no output)"
            status = "completed" if result.returncode == 0 else "failed"
            activity_item.set_status(status, output, 0.0)

            self._emit_semantic(EventType.TOOL_COMPLETED, tool="shell", status=status)

            self.chat_messages.append({
                "role": "user",
                "content": f"[shell] {command}\n{output}",
            })
        except Exception as e:
            activity_item.set_status("failed", str(e), 0.0)
            self._emit_semantic(EventType.TOOL_FAILED, tool="shell", error=str(e))
        self._smart_scroll()

    def action_new_chat(self):
        """Start new chat session."""
        if self.chat_messages:
            self._save_conversation()
        if self.agent_state:
            self.agent_state.reset()
        self.chat_messages = []
        self.current_conv_id = ""
        self.attached_files = []
        self._cancel_event.clear()
        if self._todo_panel:
            self._todo_panel.update_tasks([])
            try:
                if self._todo_panel.parent:
                    self._todo_panel.remove()
            except Exception:
                pass
        if self._activity_feed:
            self._activity_feed.clear()
        if self._thinking_widget:
            try:
                if self._thinking_widget.parent:
                    self._thinking_widget.remove()
            except Exception:
                pass
            self._thinking_widget = None
        scroll = self.query_one("#chat-scroll", ScrollableContainer)
        scroll.remove_children()
        scroll.mount(WelcomeBanner(cwd=self.working_dir, model=self.current_model))
        self._update_status()

    def action_select_model(self):
        self._open_model_modal()

    def action_clear_chat(self):
        if self.agent_state:
            self.agent_state.reset()
        self.chat_messages = []
        self.attached_files = []
        if self._todo_panel:
            self._todo_panel.update_tasks([])
            try:
                if self._todo_panel.parent:
                    self._todo_panel.remove()
            except Exception:
                pass
        if self._activity_feed:
            self._activity_feed.clear()
        scroll = self.query_one("#chat-scroll", ScrollableContainer)
        scroll.remove_children()
        scroll.mount(WelcomeBanner(cwd=self.working_dir, model=self.current_model))
        self._update_status()

    def action_toggle_mode(self):
        if self.slash_open:
            menu = self.query_one("#slash-widget", SlashMenu)
            cmd = menu.selected_command()
            inp = self.query_one("#user-input", Input)
            inp.value = cmd + (" " if cmd in ("/attach",) else "")
            inp.cursor_position = len(inp.value)
            if cmd != "/attach":
                self._hide_slash()
            return
        self.agent_mode = "plan" if self.agent_mode == "build" else "build"
        self._update_status()
        if self.agent_mode == "plan":
            self._show_info("\u23F8 plan mode on")
        else:
            self._show_info("\u23F8 manual mode on")
        self.query_one("#user-input", Input).focus()

    def action_help(self):
        self.push_screen(HelpScreen())

    def action_sessions(self):
        sessions = self._list_sessions()
        if not sessions:
            self._show_info("no saved sessions yet")
            return

        def handle(conv_id):
            if conv_id:
                self._open_session(conv_id)

        self.push_screen(SessionSelectScreen(sessions, self.current_conv_id), handle)

    def action_palette(self):
        def handle(choice):
            if not choice:
                return
            choice = str(choice).strip()
            mapping = {
                "new session": self.action_new_chat,
                "select model": self._open_model_modal,
                "browse sessions": self.action_sessions,
                "toggle plan / build": self.action_toggle_mode,
                "help": self.action_help,
                "quit": self.exit,
            }
            if choice in mapping:
                mapping[choice]()
                return
            if choice.startswith("/"):
                cmd = choice.split()[0]
                self._process_command(cmd)

        self.push_screen(CommandPalette(), handle)

    def action_interrupt(self):
        if self.slash_open:
            self._hide_slash()
            return
        if self.is_thinking:
            self.is_thinking = False
            self._cancel_event.set()
            if self.agent_state:
                self.agent_state.handle_error()
            self._show_warning("interrupted")
            self._update_status()
            if self._thinking_widget:
                try:
                    if self._thinking_widget.parent:
                        self._thinking_widget.remove()
                except Exception:
                    pass
                self._thinking_widget = None

    def _add_message(self, role: str, content: str, model: str = "", thinking: str = ""):
        """Add message to chat scroll."""
        try:
            scroll = self.query_one("#chat-scroll", ScrollableContainer)
        except Exception:
            return None

        if role == "assistant":
            self._emit_semantic(EventType.ASSISTANT_MESSAGE, content=content[:200])

        bubble = MessageBubble(role=role, content=content, model=model, thinking=thinking)
        scroll.mount(bubble)
        self._smart_scroll()
        return bubble

    def _add_tool_card(self, name: str, args: dict):
        """Add tool card for tracking."""
        if self._should_track_file(name, args):
            self._snapshot_file(args["path"])
        return None

    def _update_tool_card(self, card: ToolCard, status: str, result: str = "", duration: float = 0.0):
        """Update tool card with result."""
        if not card:
            return
        card.tool_status = "ok" if status == "completed" else ("error" if status == "failed" else "running")
        card.tool_result = result
        if duration > 0:
            card.elapsed = f"{duration:.1f}s"
        card.refresh()

        if status == "completed" and card.tool_name in ("write", "edit", "patch"):
            filepath = card.tool_args
            if filepath:
                full_path = os.path.join(self.working_dir, filepath)
                try:
                    if os.path.exists(full_path):
                        with open(full_path, "r", errors="replace") as f:
                            new_content = f.read()
                        self._show_file_diff(filepath, new_content)
                except Exception:
                    pass

    def _open_model_modal(self):
        if not self.available_models:
            self._show_warning("no models available")
            return

        def handle_result(model_id):
            if model_id:
                self.current_model = model_id
                self.config.model = model_id
                self.config.save()
                self._update_status()
                self._update_header()
                self._show_success(f"model  {model_id}")

        self.push_screen(
            ModelSelectScreen(self.available_models, self.current_model),
            handle_result,
        )

    def on_key(self, event):
        if not self.slash_open or event.key not in ("down", "up"):
            return
        options = self.query_one("#slash-options", OptionList)
        if event.key == "down":
            options.action_cursor_down()
        else:
            options.action_cursor_up()
        event.stop()
        event.prevent_default()

    @on(Input.Changed, "#user-input")
    def handle_input_changed(self, event: Input.Changed):
        value = event.value
        exact = {cmd for cmd, _ in SLASH_COMMANDS}
        if value.startswith("/") and " " not in value and value not in exact:
            self._show_slash(value)
        elif self.slash_open:
            self._hide_slash()

    @on(Input.Submitted, "#user-input")
    async def handle_input_submit(self):
        await self._send_message()

    async def _send_message(self):
        """Handle message submission."""
        input_widget = self.query_one("#user-input", Input)
        user_input = input_widget.value.strip()
        if not user_input:
            return

        if self.slash_open and user_input.startswith("/"):
            menu = self.query_one("#slash-widget", SlashMenu)
            if " " not in user_input:
                user_input = menu.selected_command()
            self._hide_slash()

        input_widget.value = ""
        self._hide_slash()

        if user_input.startswith("!") and len(user_input) > 1:
            self._run_shell(user_input[1:].strip())
            return

        if self._process_command(user_input):
            return

        self.chat_messages.append({"role": "user", "content": user_input})
        self._add_message("user", user_input)

        if not self.current_model:
            self._show_error("no model selected  \u00B7  ctrl+m")
            return

        system = self.config.system_prompt
        if self.agent_mode == "plan":
            system += "\nYou are in PLAN mode. Do not write or modify files. Analyze, propose, and wait for approval."
        else:
            system += "\nYou have access to tools. Use them to help the user. Always use tools when needed rather than guessing."

        messages = [{"role": "system", "content": system}]
        for msg in self.chat_messages[-20:]:
            messages.append({"role": msg["role"], "content": msg["content"]})

        self.is_thinking = True
        self._thinking_start_time = time.time()
        self._cancel_event.clear()
        self._update_status()

        # Mount animated working indicator
        if self._thinking_widget:
            try:
                if self._thinking_widget.parent:
                    self._thinking_widget.remove()
            except Exception:
                pass
        self._thinking_widget = ProcessingStatus()
        try:
            scroll = self.query_one("#chat-scroll", ScrollableContainer)
            scroll.mount(self._thinking_widget)
            self._smart_scroll()
        except Exception:
            pass

        # Start phrase rotation timer
        self._phrase_idx = getattr(self, '_phrase_idx', 0)
        self._rotate_phrase()
        self._phrase_timer = self.set_interval(1.5, self._rotate_phrase)

        self._emit_semantic(EventType.ASSISTANT_THINKING, state="started")

        if self.agent_state:
            self.agent_state.start()

        try:
            await self._stream_response(messages)
        except asyncio.CancelledError:
            self._show_warning("interrupted")
            if self.agent_state:
                self.agent_state.handle_error()
        except Exception as e:
            self._show_error(f"{e}\ncheck API at {self.config.base_url}")
            self.log.error(f"Error: {e}")
            if self.agent_state:
                self.agent_state.handle_error()
        finally:
            self.is_thinking = False
            self._save_conversation()
            self._update_status()
            self._emit_semantic(EventType.ASSISTANT_THINKING, state="ended")
            # Stop phrase rotation timer
            if self._phrase_timer:
                try:
                    self._phrase_timer.stop()
                except Exception:
                    pass
                self._phrase_timer = None
            if self._thinking_widget:
                try:
                    if self._thinking_widget.parent:
                        self._thinking_widget.remove()
                except Exception:
                    pass
                self._thinking_widget = None

    async def _stream_response(self, messages: list[dict]):
        """Full agentic loop: stream → tool calls → execute → repeat."""
        tools = self.tool_registry.get_openai_tools()
        if not tools:
            tools = []

        max_rounds = 5
        round_num = 0

        while round_num < max_rounds:
            if self._cancel_event.is_set():
                break

            round_num += 1
            full_response = []
            thinking_started = False
            thinking_content = []
            in_thinking_block = False
            tool_calls_data: dict[int, dict] = {}

            try:
                async for chunk in self.client.chat_stream(
                    messages, model=self.current_model, tools=tools if tools else None
                ):
                    if self._cancel_event.is_set():
                        break

                    if not thinking_started and (chunk.content or chunk.tool_calls):
                        if self.agent_state:
                            self.agent_state.begin_thinking()
                        thinking_started = True

                    if chunk.content:
                        # Track thinking content for real-time display
                        content = chunk.content

                        # Check for thinking tags (streaming-aware)
                        if "<thinking>" in content and not in_thinking_block:
                            in_thinking_block = True
                            # Extract content before thinking tag
                            before, _, after = content.partition("<thinking>")
                            if before.strip():
                                full_response.append(before)
                            # Stop phrase rotation and show real thinking
                            if self._phrase_timer:
                                try:
                                    self._phrase_timer.stop()
                                except Exception:
                                    pass
                                self._phrase_timer = None
                        elif "</thinking>" in content and in_thinking_block:
                            in_thinking_block = False
                            before, _, after = content.partition("</thinking>")
                            if before.strip():
                                thinking_content.append(before)
                            if after.strip():
                                full_response.append(after)
                        elif in_thinking_block:
                            thinking_content.append(content)
                            # Update thinking widget with real thinking content
                            if self._thinking_widget:
                                accumulated_thinking = "".join(thinking_content)
                                # Show last few lines of thinking
                                lines = accumulated_thinking.strip().split("\n")
                                display_lines = lines[-5:] if len(lines) > 5 else lines
                                display_text = "\n".join(display_lines)
                                self._thinking_widget.set_phrase(f"Thinking: {display_text[:60]}...")
                        else:
                            full_response.append(content)

                    for tc in chunk.tool_calls:
                        idx = tc.index
                        if idx not in tool_calls_data:
                            tool_calls_data[idx] = {"id": "", "name": "", "arguments": ""}
                        if tc.id:
                            tool_calls_data[idx]["id"] = tc.id
                        if tc.name:
                            tool_calls_data[idx]["name"] = tc.name
                        if tc.arguments:
                            tool_calls_data[idx]["arguments"] += tc.arguments

            except Exception as e:
                if self._cancel_event.is_set():
                    break
                raise

            if tool_calls_data and not self._cancel_event.is_set():
                if self.agent_state:
                    self.agent_state.begin_tool_execution()

                assistant_msg = {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [],
                }
                for idx in sorted(tool_calls_data.keys()):
                    tc = tool_calls_data[idx]
                    assistant_msg["tool_calls"].append({
                        "id": tc["id"],
                        "type": "function",
                        "function": {"name": tc["name"], "arguments": tc["arguments"]},
                    })
                messages.append(assistant_msg)

                for idx in sorted(tool_calls_data.keys()):
                    tc = tool_calls_data[idx]
                    tool_name = tc["name"]
                    try:
                        args = json.loads(tc["arguments"]) if tc["arguments"] else {}
                    except json.JSONDecodeError:
                        args = {}

                    self._add_tool_card(tool_name, args)
                    start = time.time()

                    activity_item = None
                    try:
                        scroll = self.query_one("#chat-scroll", ScrollableContainer)
                        activity_item = ToolActivityItem(
                            tool_name=tool_name,
                            args=args,
                            execution_id=tc["id"],
                        )
                        activity_item.status = "running"
                        scroll.mount(activity_item)
                        self._smart_scroll()
                    except Exception:
                        pass

                    self._emit_semantic(EventType.TOOL_STARTED, tool=tool_name, args=args)

                    if self._activity_feed:
                        self._activity_feed.add_execution(tc["id"], tool_name, args)

                    result = await self.tool_executor.execute(tool_name, args)

                    duration = time.time() - start

                    if activity_item:
                        activity_item.set_status("completed", result, duration)

                    self._emit_semantic(EventType.TOOL_COMPLETED, tool=tool_name, duration=duration, result_len=len(result))

                    if self._activity_feed:
                        self._activity_feed.update_execution(tc["id"], "completed", result, duration)

                    if tool_name in ("write", "edit", "patch") and "path" in args:
                        filepath = args["path"]
                        full_path = os.path.join(self.working_dir, filepath)
                        try:
                            if os.path.exists(full_path):
                                with open(full_path, "r", errors="replace") as f:
                                    new_content = f.read()
                                self._show_file_diff(filepath, new_content)
                        except Exception:
                            pass

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": result[:10000],
                    })

                continue

            # Final text response
            final_content = "".join(full_response)

            # Use accumulated thinking content if available, otherwise extract from final
            if thinking_content:
                thinking = "".join(thinking_content).strip()
                response = final_content.strip()
            else:
                thinking, response = _extract_thinking(final_content)

            if self.agent_state:
                self.agent_state.begin_response(response, thinking)

            self.chat_messages.append({
                "role": "assistant",
                "content": response,
                "model": self.current_model,
                "thinking": thinking,
            })

            if self.agent_state:
                self.agent_state.finish()

            # Update todo panel
            if self._todo_panel:
                tasks = self.todo_manager.list_all()
                task_data = [
                    {
                        "id": t.id,
                        "content": t.content,
                        "active_form": t.active_form,
                        "status": t.status.value,
                        "priority": t.priority.value,
                    }
                    for t in tasks
                ]
                if task_data:
                    self._todo_panel.update_tasks(task_data)
                    try:
                        scroll = self.query_one("#chat-scroll", ScrollableContainer)
                        if self._todo_panel.parent is None:
                            scroll.mount(self._todo_panel)
                            self._smart_scroll()
                        else:
                            self._todo_panel.refresh()
                    except Exception:
                        pass

            break

    async def _do_attach(self, path: str):
        """Attach file to conversation."""
        attachment = load_file(path)
        if not attachment:
            self._show_error(f"could not read  {path}")
            return
        self.attached_files.append(path)
        preview = attachment.content[:500]
        if len(attachment.content) > 500:
            preview += f"\n\u2026 ({len(attachment.content)} chars)"
        self._add_message("user", f"attached  {attachment.name}\n\n```\n{preview}\n```")
        self.chat_messages.append({"role": "user", "content": f"[File: {attachment.name}]\n{attachment.content}"})
        self._show_success(f"attached  {attachment.name}")
        self._update_status()


def run_app(working_dir: str = ""):
    app = LeocodeApp(working_dir=working_dir)
    app.run()


if __name__ == "__main__":
    run_app()

"""Leocode TUI widgets — Claude Code faithful reimplementation."""

import re
import difflib
from typing import Optional

from textual.widgets import Static, OptionList, Input
from textual.containers import Container, Horizontal
from textual.reactive import reactive
from textual.app import ComposeResult
from textual.binding import Binding
from rich.text import Text
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.console import Console
from rich.table import Table
from rich import box

from .theme import (
    CLAUDE, CLAUDE_SHIMMER, TEXT, TEXT_SECONDARY, TEXT_MUTED, TEXT_DIM, TEXT_BRIGHT,
    SUCCESS, WARNING, ERROR, INFO, PLAN_MODE, AUTO_ACCEPT, BYPASS, MANUAL,
    BG, BG_PANEL, BORDER, BORDER_SUBTLE, MUTED, SURFACE,
    short_path, short_model,
)
from .status_config import SPINNER_FRAMES, WORKING_PHRASES

MARK = "\u2733"


def _render_markdown_text(content: str, width: int) -> Text:
    if not content.strip():
        return Text("")

    fence_count = content.count("```")
    render_content = content
    if fence_count % 2 == 1:
        render_content = content + "\n```\n"

    try:
        md = Markdown(render_content, code_theme="monokai", hyperlinks=True)
        console = Console(width=width, highlight=False)
        with console.capture() as capture:
            console.print(md)
        result = Text.from_ansi(capture.get())

        if fence_count % 2 == 1:
            raw = result.plain
            if raw.rstrip().endswith("```"):
                lines = raw.split("\n")
                for i in range(len(lines) - 1, -1, -1):
                    if lines[i].strip() == "```":
                        lines.pop(i)
                        break
                result = Text("\n".join(lines))
        return result
    except Exception:
        return Text(content, TEXT)


def _render_table_from_markdown(content: str, width: int) -> Optional[Text]:
    lines = content.strip().split("\n")
    table_lines = []
    in_table = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            inner = stripped[1:-1]
            cells = [c.strip() for c in inner.split("|")]
            is_separator = all(re.match(r'^[-:]+$', c) for c in cells if c)
            if is_separator:
                in_table = True
                continue
            if in_table or (cells and any(c for c in cells)):
                table_lines.append(cells)
                in_table = True
            else:
                break
        elif in_table:
            break

    if len(table_lines) < 2:
        return None

    try:
        table = Table(
            show_header=True,
            header_style=f"bold {CLAUDE}",
            box=box.SIMPLE_HEAVY,
            border_style=BORDER,
            pad_edge=False,
            expand=False,
        )
        headers = table_lines[0]
        for h in headers:
            table.add_column(h, style=TEXT)

        for row in table_lines[1:]:
            padded = row + [""] * (len(headers) - len(row))
            table.add_row(*padded[:len(headers)])

        console = Console(width=width, highlight=False)
        with console.capture() as capture:
            console.print(table)
        return Text.from_ansi(capture.get())
    except Exception:
        return None


class WelcomeBanner(Static):
    """Claude Code style welcome screen."""

    def __init__(self, cwd: str = "", model: str = "", **kwargs):
        self.cwd = cwd
        self.model = model or "no model selected"
        super().__init__(**kwargs)

    def render(self) -> Text:
        t = Text()

        # LeoCode ASCII logo
        t.append("  ╔══════════════════════════════════╗\n", f"bold {CLAUDE}")
        t.append("  ║        █████╗ ██████╗  ██████╗   ║\n", f"bold {CLAUDE}")
        t.append("  ║       ██╔══██╗██╔══██╗██╔═══██╗  ║\n", f"bold {CLAUDE}")
        t.append("  ║       ███████║██████╔╝██║   ██║  ║\n", f"bold {CLAUDE}")
        t.append("  ║       ██╔══██║██╔══██╗██║   ██║  ║\n", f"bold {CLAUDE}")
        t.append("  ║       ██║  ██║██║  ██║╚██████╔╝  ║\n", f"bold {CLAUDE}")
        t.append("  ║       ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝   ║\n", f"bold {CLAUDE}")
        t.append("  ╚══════════════════════════════════╝\n", f"bold {CLAUDE}")

        # Working directory
        t.append(f"  {short_path(self.cwd, 50) or '.'}", TEXT_DIM)
        t.append("\n")

        # Hints — Claude Code style
        t.append("\n", TEXT)
        t.append("  /help for commands, Ctrl+P for command palette", TEXT_DIM)
        t.append("\n")

        return t


class MessageBubble(Static):
    """Message bubble — Claude Code faithful style.

    User messages: plain text, no prefix
    Assistant messages: plain text, no prefix
    """

    def __init__(
        self,
        role: str,
        content: str,
        model: str = "",
        thinking: str = "",
        **kwargs,
    ):
        self.role = role
        self.raw_content = content
        self.model = model
        self.thinking_content = thinking
        self.reveal_mode = False
        self._revealed_text = ""
        self._word_queue: list[str] = []
        self._code_mode = False
        self._reveal_timer = None
        kwargs.setdefault("classes", f"bubble-{role}")
        super().__init__(**kwargs)

    def start_reveal(self, full_text: str):
        if not full_text.strip():
            self.raw_content = full_text
            self.refresh()
            return

        self.raw_content = full_text
        self.reveal_mode = True
        self._revealed_text = ""
        self._code_mode = False
        self._word_queue = self._build_word_queue(full_text)

        if not self._word_queue:
            self.reveal_mode = False
            self.refresh()
            return

        self._reveal_timer = self.app.set_interval(0.04, self._advance_reveal)

    def finish_reveal(self):
        if self._reveal_timer:
            self._reveal_timer.stop()
            self._reveal_timer = None
        self.reveal_mode = False
        self._revealed_text = ""
        self._word_queue = []
        self._code_mode = False
        self.refresh()

    def _build_word_queue(self, text: str) -> list[str]:
        parts = re.split(r"(```[^\n]*\n.*?```)", text, flags=re.DOTALL)
        queue: list[str] = []
        for part in parts:
            if part.startswith("```"):
                queue.append(part)
            else:
                words = re.findall(r"\S+\s*", part)
                queue.extend(words)
        return queue

    def _advance_reveal(self):
        if not self._word_queue:
            if self._reveal_timer:
                self._reveal_timer.stop()
                self._reveal_timer = None
            self.reveal_mode = False
            self.refresh()
            try:
                scroll = self.app.query_one("#chat-scroll")
                scroll.scroll_end(animate=False)
            except Exception:
                pass
            return

        word = self._word_queue.pop(0)

        if word.startswith("```"):
            if self._code_mode:
                self._code_mode = False
            else:
                self._code_mode = True
            self._revealed_text += word
        else:
            self._revealed_text += word

        self.refresh()
        try:
            scroll = self.app.query_one("#chat-scroll")
            scroll.scroll_end(animate=False)
        except Exception:
            pass

    def _render_content(self, content: str, width: int) -> Text:
        if not content:
            return Text("")

        table_result = _render_table_from_markdown(content, width)
        if table_result and table_result.plain.strip():
            lines = content.strip().split("\n")
            table_like = sum(1 for l in lines if l.strip().startswith("|"))
            if table_like >= len(lines) * 0.5:
                return table_result

        return _render_markdown_text(content, width)

    def render(self) -> Text:
        t = Text()

        if self.role == "user":
            # Claude Code: user messages are plain text
            t.append(self.raw_content.strip(), TEXT)
            return t

        if self.role == "assistant":
            # Claude Code: assistant messages are plain text
            content = self._revealed_text if self.reveal_mode else self.raw_content.strip()
            if content:
                width = max(40, (self.size.width or 80) - 4)
                t.append(self._render_content(content, width))
            return t

        # System messages
        t.append(self.raw_content.strip(), TEXT_MUTED)
        return t


class ThinkingIndicator(Container):
    """Clickable thinking spinner with expandable reasoning panel."""

    BINDINGS = [
        Binding("enter", "toggle_panel", show=False),
        Binding("space", "toggle_panel", show=False),
    ]

    active = reactive(False)
    _frame = reactive(0)
    elapsed = reactive(0.0)
    expanded = reactive(False)
    thinking_content = reactive("")
    current_phrase = reactive("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._header: Optional[Static] = None
        self._panel: Optional[Static] = None
        self._phrase_idx = 0

    def compose(self) -> ComposeResult:
        self._header = Static(id="thinking-header")
        self._panel = Static(id="thinking-panel")
        yield self._header
        yield self._panel

    def on_click(self):
        if self.active:
            self.action_toggle_panel()

    def action_toggle_panel(self):
        if not self.active:
            return
        self.expanded = not self.expanded
        if self._panel:
            if self.expanded:
                self._panel.styles.display = "block"
                if self.thinking_content:
                    self._panel.update(self._format_panel(self.thinking_content))
            else:
                self._panel.styles.display = "none"
        self._refresh_header()

    def _refresh_header(self):
        if not self._header:
            return
        t = Text()
        spark = SPINNER_FRAMES[self._frame % len(SPINNER_FRAMES)]
        t.append(f"{spark} ", CLAUDE)
        phrase = self.current_phrase or "Thinking"
        t.append(phrase, TEXT_SECONDARY)
        t.append("...", TEXT_SECONDARY)
        if self.elapsed:
            t.append(f" ({self.elapsed:.0f}s)", TEXT_DIM)
        t.append("  ", TEXT_DIM)
        t.append("(esc to interrupt)", TEXT_DIM)
        if self.active:
            indicator = " ↓" if not self.expanded else " ↑"
            t.append(indicator, TEXT_DIM)
        self._header.update(t)

    def _format_panel(self, content: str) -> Text:
        t = Text()
        t.append("┌─ ", TEXT_DIM)
        t.append("Thinking", TEXT_SECONDARY)
        t.append(" ", TEXT_DIM)
        t.append("─" * max(1, 26 - len("Thinking")), TEXT_DIM)
        t.append("┐", TEXT_DIM)
        t.append("\n")
        for line in content.strip().split("\n"):
            t.append("│ ", TEXT_DIM)
            t.append(line, TEXT_SECONDARY)
            t.append("\n")
        t.append("└", TEXT_DIM)
        t.append("─" * 28, TEXT_DIM)
        t.append("┘", TEXT_DIM)
        t.append("\n")
        return t

    def activate(self):
        self.active = True
        self.elapsed = 0.0
        self._frame = 0
        self._phrase_idx = (self._phrase_idx + 1) % len(WORKING_PHRASES)
        self.current_phrase = WORKING_PHRASES[self._phrase_idx]
        self._refresh_header()

    def deactivate(self):
        self.active = False
        self.expanded = False
        if self._panel:
            self._panel.styles.display = "none"
        self._refresh_header()

    def advance(self):
        self._frame += 1
        self.elapsed += 0.08
        self._refresh_header()

    def update_thinking(self, content: str):
        self.thinking_content = content
        if self.expanded and self._panel:
            self._panel.update(self._format_panel(content))


class DiffWidget(Static):
    """Renders a diff for file operations — Claude Code style."""

    def __init__(self, filepath: str, is_new: bool = False,
                 old_content: str = "", new_content: str = "", **kwargs):
        self.filepath = filepath
        self.is_new = is_new
        self.old_content = old_content
        self.new_content = new_content
        self._expanded = True
        self._header_widget: Optional[Static] = None
        self._body_widget: Optional[Static] = None
        kwargs.setdefault("classes", "diff-widget")
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        self._header_widget = Static(self._render_header(), classes="diff-header")
        self._body_widget = Static(self._render_body(), classes="diff-expanded")
        yield self._header_widget
        yield self._body_widget

    def _render_header(self) -> Text:
        t = Text()
        basename = self.filepath.rsplit("/", 1)[-1] if "/" in self.filepath else self.filepath
        if self.is_new:
            added = len(self.new_content.splitlines())
            t.append("✓ ", SUCCESS)
            t.append(f"{basename} ", SUCCESS)
            t.append(f"(new, {added} lines)", TEXT_DIM)
        else:
            old_lines = self.old_content.splitlines()
            new_lines = self.new_content.splitlines()
            diff = list(difflib.unified_diff(old_lines, new_lines, lineterm=""))
            adds = sum(1 for l in diff if l.startswith("+") and not l.startswith("+++"))
            dels = sum(1 for l in diff if l.startswith("-") and not l.startswith("---"))
            t.append("✓ ", SUCCESS)
            t.append(f"{basename} ", SUCCESS)
            t.append(f"+{adds} ", SUCCESS)
            t.append(f"-{dels}", ERROR)
        t.append("\n")
        return t

    def _render_body(self) -> Text:
        t = Text()
        if self.is_new:
            for i, line in enumerate(self.new_content.splitlines()[:50], 1):
                t.append(f" {i:>3} ", TEXT_DIM)
                t.append("+ ", SUCCESS)
                t.append(line[:120], TEXT)
                t.append("\n")
            remaining = len(self.new_content.splitlines()) - 50
            if remaining > 0:
                t.append(f"   ... {remaining} more lines\n", TEXT_DIM)
            return t

        old_lines = self.old_content.splitlines()
        new_lines = self.new_content.splitlines()
        diff = list(difflib.unified_diff(
            old_lines, new_lines,
            fromfile=f"a/{self.filepath}",
            tofile=f"b/{self.filepath}",
            lineterm="",
        ))

        if not diff:
            t.append(" (no changes)\n", TEXT_DIM)
            return t

        for line in diff[:80]:
            if line.startswith("+++") or line.startswith("---"):
                continue
            if line.startswith("@@"):
                t.append(f" {line[:120]}\n", INFO)
            elif line.startswith("+"):
                t.append("+ ", SUCCESS)
                t.append(line[1:][:120], SUCCESS)
                t.append("\n")
            elif line.startswith("-"):
                t.append("- ", ERROR)
                t.append(line[1:][:120], ERROR)
                t.append("\n")
            else:
                t.append(" ", TEXT_DIM)
                t.append(line[:120] if line else " ", TEXT_DIM)
                t.append("\n")

        remaining = len(diff) - 80
        if remaining > 0:
            t.append(f"   ... {remaining} more diff lines\n", TEXT_DIM)
        return t

    def toggle_expand(self):
        self._expanded = not self._expanded
        if self._body_widget:
            self._body_widget.styles.display = "block" if self._expanded else "none"
        self.refresh()

    def collapse(self):
        self._expanded = False
        if self._body_widget:
            self._body_widget.styles.display = "none"
        self.refresh()

    def expand(self):
        self._expanded = True
        if self._body_widget:
            self._body_widget.styles.display = "block"
        self.refresh()

    def render(self) -> Text:
        return Text("")


class InlinePermission(Container):
    """Inline permission prompt — Claude Code style."""

    BINDINGS = [
        Binding("1", "allow_once", show=False),
        Binding("2", "always_allow", show=False),
        Binding("3", "deny", show=False),
        Binding("escape", "deny", show=False),
    ]

    resolved = reactive(False)
    resolution = reactive("")
    selected_index = reactive(0)

    def __init__(self, action: str, tool_name: str = "",
                 risk_level: str = "medium", **kwargs):
        self.action = action
        self.tool_name = tool_name
        self.risk_level = risk_level
        self._action_widget: Optional[Static] = None
        self._options_widget: Optional[Static] = None
        self._result_widget: Optional[Static] = None
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        with Container(classes="permission-box"):
            self._action_widget = Static(self._render_action(), classes="permission-action")
            self._options_widget = Static(self._render_options(), classes="permission-options")
            self._result_widget = Static("", classes="permission-result")
            self._result_widget.styles.display = "none"
            yield self._action_widget
            yield self._options_widget
            yield self._result_widget

    def _render_action(self) -> Text:
        t = Text()
        t.append(self.action, TEXT)
        t.append("\n")
        return t

    def _render_options(self) -> Text:
        t = Text()
        options = [
            "Yes",
            "Yes, and don't ask again for this session",
            "No, and tell Claude what to do differently",
        ]
        for i, opt in enumerate(options):
            if i == self.selected_index:
                t.append("  \u276F ", CLAUDE)
                t.append(opt, TEXT)
            else:
                t.append(f"    {i + 1}. ", TEXT_DIM)
                t.append(opt, TEXT_SECONDARY)
            t.append("\n")
        return t

    def _render_result(self, approved: bool, always: bool = False) -> Text:
        t = Text()
        if approved:
            t.append("✓ ", SUCCESS)
            t.append(f"Approved: {self.tool_name} ", SUCCESS)
            t.append(self.action, TEXT_MUTED)
        else:
            t.append("✗ ", ERROR)
            t.append(f"Denied: {self.tool_name} ", ERROR)
            t.append(self.action, TEXT_MUTED)
        return t

    def resolve(self, approved: bool, always: bool = False):
        self.resolved = True
        self.resolution = "approved" if approved else "denied"
        if self._options_widget:
            self._options_widget.styles.display = "none"
        if self._result_widget:
            self._result_widget.update(self._render_result(approved, always))
            self._result_widget.styles.display = "block"
        self.refresh()

    def action_allow_once(self):
        if not self.resolved:
            self.resolve(True, False)
            self.app.call_from_thread(self._emit_result, "allow_once")

    def action_always_allow(self):
        if not self.resolved:
            self.resolve(True, True)
            self.app.call_from_thread(self._emit_result, "always_allow")

    def action_deny(self):
        if not self.resolved:
            self.resolve(False)
            self.app.call_from_thread(self._emit_result, "denied")

    def _emit_result(self, result: str):
        self._resolution_result = result


class StatusBar(Static):
    """Compact one-line status bar — Claude Code footer style."""

    model_name = reactive("no model")
    rag_count = reactive(0)
    mcp_count = reactive(0)
    working_dir = reactive("")
    status_text = reactive("ready")
    agent_mode = reactive("build")
    git_branch = reactive("")
    message_count = reactive(0)
    active_tools = reactive(0)
    elapsed_time = reactive(0.0)
    context_remaining = reactive(100)

    def render(self) -> Text:
        t = Text()

        # Mode indicator — Claude Code style
        if self.agent_mode == "plan":
            t.append("⏸ plan mode", TEXT_SECONDARY)
        elif self.agent_mode == "build":
            t.append("⏸ manual mode", TEXT_SECONDARY)
        else:
            t.append(f"⏸ {self.agent_mode} mode", TEXT_SECONDARY)

        # Context meter
        ctx = max(0, min(100, self.context_remaining))
        bar_len = 10
        filled = int(ctx / 100 * bar_len)
        bar = "█" * filled + "░" * (bar_len - filled)
        t.append(f"  · {ctx}% ", TEXT_DIM)
        t.append(bar, CLAUDE)

        # Model name
        t.append(f"  · ", TEXT_DIM)
        t.append(short_model(self.model_name), TEXT_DIM)

        # Processing status
        if self.status_text == "thinking":
            t.append("  · ", TEXT_DIM)
            t.append("thinking", CLAUDE)

        return t


class ComposerMeta(Static):
    hint = reactive("")
    attached = reactive(0)

    def render(self) -> Text:
        return Text("")


SLASH_COMMANDS = [
    ("/model", "Select AI model"),
    ("/new", "Start a new session"),
    ("/clear", "Clear the current chat"),
    ("/sessions", "Browse saved sessions"),
    ("/attach", "Attach a file to context"),
    ("/mode", "Toggle plan / build"),
    ("/help", "Show commands and shortcuts"),
    ("/quit", "Exit LeoCode"),
]


class SlashMenu(Container):
    def compose(self) -> ComposeResult:
        yield OptionList(id="slash-options")

    def filter(self, query: str) -> list[tuple[str, str]]:
        q = query.lstrip("/").lower()
        if not q:
            return SLASH_COMMANDS
        return [c for c in SLASH_COMMANDS if q in c[0][1:] or q in c[1].lower()]

    def update_query(self, query: str) -> int:
        options = self.query_one("#slash-options", OptionList)
        options.clear_options()
        matches = self.filter(query)
        for cmd, desc in matches:
            options.add_option(f"{cmd:<12} {desc}")
        if matches:
            options.highlighted = 0
        return len(matches)

    def selected_command(self) -> str:
        options = self.query_one("#slash-options", OptionList)
        if options.option_count == 0:
            return "/help"
        idx = options.highlighted if options.highlighted is not None else 0
        prompt = str(options.get_option_at_index(idx).prompt)
        return prompt.split()[0]


class ToolCard(Static):
    def __init__(
        self,
        name: str,
        args: str = "",
        result: str = "",
        status: str = "running",
        elapsed: str = "",
        **kwargs,
    ):
        self.tool_name = name
        self.tool_args = args
        self.tool_result = result
        self.tool_status = status
        self.elapsed = elapsed
        self._expanded = False
        kwargs.setdefault("classes", "tool-card")
        super().__init__(**kwargs)

    def render(self) -> Text:
        t = Text()
        mark = {"running": "⠋", "ok": "✓", "error": "✗"}.get(self.tool_status, "⠋")
        color = {"running": CLAUDE, "ok": SUCCESS, "error": ERROR}.get(self.tool_status, CLAUDE)
        t.append(f"{mark} ", color)
        t.append(self.tool_name, TEXT_SECONDARY)
        if self.tool_args:
            preview = self.tool_args.replace("\n", " ").strip()
            if len(preview) > 60:
                preview = preview[:59] + "..."
            t.append(f"  {preview}", TEXT_DIM)
        if self.elapsed:
            t.append(f"  {self.elapsed}", TEXT_DIM)
        if not self._expanded and self.tool_result and self.tool_status != "running":
            lines = self.tool_result.strip().splitlines()
            extra = len(lines)
            if extra > 0:
                t.append(f"  [{extra} lines]", TEXT_DIM)
        t.append("\n")
        if self._expanded and self.tool_result and self.tool_status != "running":
            lines = self.tool_result.strip().splitlines()[:12]
            for line in lines:
                t.append(f"  {line[:96]}\n", TEXT_MUTED)
            remaining = max(0, len(self.tool_result.strip().splitlines()) - 12)
            if remaining:
                t.append(f"  ... {remaining} more\n", TEXT_DIM)
        return t

    def toggle_expand(self):
        self._expanded = not self._expanded
        self.refresh()


class Brand(Static):
    def render(self) -> Text:
        t = Text()
        t.append("LeoCode\n", f"bold {CLAUDE}")
        return t


HeaderBar = StatusBar
ModelSelector = StatusBar
Logo = Brand
ThinkingSection = ThinkingIndicator
ModelSelectionModal = Container

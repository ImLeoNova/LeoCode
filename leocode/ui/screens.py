"""Modal screens — model picker, sessions, help, command palette."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.screen import ModalScreen
from textual.widgets import Input, ListView, ListItem, Label, OptionList, Static
from textual import on

from .theme import MODAL_CSS, CLAUDE, TEXT


class ModelSelectScreen(ModalScreen):
    CSS = MODAL_CSS
    BINDINGS = [Binding("escape", "close", "Close", show=False)]

    def __init__(self, models: list[dict], current_model: str = "", **kwargs):
        self.models = models
        self.current_model = current_model
        self._filtered = models
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        with Container(id="modal"):
            yield Label("select model", classes="modal-title")
            yield Label("type to filter  ·  enter to choose", classes="modal-sub")
            yield Input(placeholder="search models…", id="model-search", classes="modal-search")
            yield ListView(
                *[self._make_item(m) for m in self._filtered[:40]],
                id="model-list",
                classes="modal-list",
            )
            yield Static("esc close", classes="modal-footer")

    def _make_item(self, model: dict) -> ListItem:
        mid = model["id"]
        mark = "●  " if mid == self.current_model else "   "
        item = ListItem(Label(f"{mark}{mid}"), classes="model-item")
        item.model_id = mid
        return item

    def on_mount(self):
        self.query_one("#model-search", Input).focus()
        lv = self.query_one("#model-list", ListView)
        for i, item in enumerate(lv.children):
            if getattr(item, "model_id", "") == self.current_model:
                lv.index = i
                break

    @on(Input.Changed, "#model-search")
    def handle_search(self, event: Input.Changed):
        query = event.value.lower().strip()
        self._filtered = [m for m in self.models if query in m["id"].lower()] if query else self.models
        lv = self.query_one("#model-list", ListView)
        lv.clear()
        for m in self._filtered[:40]:
            lv.append(self._make_item(m))

    @on(ListView.Selected, "#model-list")
    def handle_select(self, event: ListView.Selected):
        if hasattr(event.item, "model_id"):
            self.dismiss(str(event.item.model_id))

    def action_close(self):
        self.dismiss(None)


class SessionSelectScreen(ModalScreen):
    CSS = MODAL_CSS
    BINDINGS = [Binding("escape", "close", "Close", show=False)]

    def __init__(self, sessions: list[dict], current_id: str = "", **kwargs):
        self.sessions = sessions
        self.current_id = current_id
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        with Container(id="modal"):
            yield Label("sessions", classes="modal-title")
            yield Label("enter to resume  ·  esc to close", classes="modal-sub")
            yield ListView(
                *[self._make_item(s) for s in self.sessions[:40]],
                id="session-list",
                classes="modal-list",
            )
            yield Static(f"{len(self.sessions)} saved", classes="modal-footer")

    def _make_item(self, session: dict) -> ListItem:
        title = (session.get("title") or session.get("id") or "untitled").replace("\n", " ").strip()[:48]
        mark = "●  " if session.get("id") == self.current_id else "   "
        item = ListItem(Label(f"{mark}{title}"))
        item.conv_id = session.get("id", "")
        return item

    def on_mount(self):
        self.query_one("#session-list", ListView).focus()

    @on(ListView.Selected, "#session-list")
    def handle_select(self, event: ListView.Selected):
        if hasattr(event.item, "conv_id"):
            self.dismiss(str(event.item.conv_id))

    def action_close(self):
        self.dismiss(None)


class HelpScreen(ModalScreen):
    CSS = MODAL_CSS
    BINDINGS = [Binding("escape", "close", "Close", show=False)]

    def compose(self) -> ComposeResult:
        from rich.text import Text as RichText

        def _help_text() -> RichText:
            t = RichText()
            t.append("commands\n\n", f"bold {TEXT}")
            cmds = [
                ("/model", "select AI model"),
                ("/new", "start a new session"),
                ("/sessions", "browse saved sessions"),
                ("/attach", "attach a file"),
                ("/mode", "toggle plan / build"),
                ("/clear", "clear current chat"),
                ("/help", "this overlay"),
                ("/quit", "exit"),
            ]
            for cmd, desc in cmds:
                t.append(f"  {cmd:<12}", f"bold {CLAUDE}")
                t.append(f"{desc}\n", TEXT)
            t.append("\nshortcuts\n\n", f"bold {TEXT}")
            keys = [
                ("enter", "send"),
                ("tab", "plan / build"),
                ("ctrl+n", "new session"),
                ("ctrl+m", "model picker"),
                ("ctrl+p", "command palette"),
                ("ctrl+l", "sessions"),
                ("esc", "interrupt / close"),
                ("ctrl+q", "quit"),
            ]
            for key, desc in keys:
                t.append(f"  {key:<12}", f"bold {CLAUDE}")
                t.append(f"{desc}\n", TEXT)
            t.append("\ninput\n\n", f"bold {TEXT}")
            t.append("  /", f"bold {CLAUDE}")
            t.append("           slash commands\n", TEXT)
            t.append("  !", f"bold {CLAUDE}")
            t.append("           run a local shell command\n", TEXT)
            t.append("  type naturally for everything else\n", TEXT)
            return t

        with Container(id="modal"):
            yield Label("LeoCode", classes="modal-title")
            yield Static(_help_text(), classes="help-body")
            yield Static("esc close", classes="modal-footer")

    def action_close(self):
        self.dismiss(None)


class CommandPalette(ModalScreen):
    CSS = MODAL_CSS
    BINDINGS = [Binding("escape", "close", "Close", show=False)]

    ACTIONS = [
        ("new session", "new"),
        ("select model", "model"),
        ("browse sessions", "sessions"),
        ("toggle plan / build", "mode"),
        ("help", "help"),
        ("quit", "quit"),
    ]

    def compose(self) -> ComposeResult:
        with Container(id="modal"):
            yield Label("command palette", classes="modal-title")
            yield Input(placeholder="filter actions…", id="palette-search", classes="modal-search")
            yield OptionList(id="palette-list", classes="modal-list")
            yield Static("enter run  ·  esc close", classes="modal-footer")

    def on_mount(self):
        self._fill("")
        self.query_one("#palette-search", Input).focus()

    def _fill(self, query: str):
        q = query.lower().strip()
        options = self.query_one("#palette-list", OptionList)
        options.clear_options()
        for label, _key in self.ACTIONS:
            if not q or q in label:
                options.add_option(label)
        for cmd, desc in SLASH_COMMANDS:
            line = f"{cmd}  {desc}"
            if not q or q in line.lower():
                options.add_option(line)

    @on(Input.Changed, "#palette-search")
    def handle_search(self, event: Input.Changed):
        self._fill(event.value)

    @on(OptionList.OptionSelected, "#palette-list")
    def handle_select(self, event: OptionList.OptionSelected):
        self.dismiss(str(event.option.prompt))

    @on(Input.Submitted, "#palette-search")
    def handle_submit(self):
        options = self.query_one("#palette-list", OptionList)
        if options.option_count:
            idx = options.highlighted if options.highlighted is not None else 0
            self.dismiss(str(options.get_option_at_index(idx).prompt))

    def action_close(self):
        self.dismiss(None)

"""WorkingStatus widget — Claude Code style thinking indicator."""

from textual.widgets import Static
from textual.reactive import reactive
from rich.text import Text

from .theme import CLAUDE, TEXT_SECONDARY, TEXT_DIM, SUCCESS, PROCESSING
from .status_config import SPINNER_FRAMES, WORKING_PHRASES


class WorkingStatus(Static):
    """Minimal animated working indicator with braille spinner."""

    _frame = reactive(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._spinner_timer = None

    def on_mount(self):
        self._frame = 0
        self._spinner_timer = self.set_interval(0.08, self._advance_spinner)

    def on_unmount(self):
        if hasattr(self, '_spinner_timer') and self._spinner_timer:
            self._spinner_timer.stop()
            self._spinner_timer = None

    def _advance_spinner(self):
        self._frame += 1
        self.refresh()

    def render(self) -> Text:
        spark = SPINNER_FRAMES[self._frame % len(SPINNER_FRAMES)]
        t = Text()
        t.append(f"{spark} ", CLAUDE)
        t.append("Thinking...", TEXT_SECONDARY)
        return t


class ProcessingStatus(Static):
    """Thinking/processing indicator with Claude Code visual style.
    
    Shows:
    * Spinner icon (* or +)
    * Processing phrase ("Grooving...", "Thinking...", etc.)
    * Timing and token info
    """

    active = reactive(False)
    _frame = reactive(0)
    elapsed = reactive(0.0)
    current_phrase = reactive("")

    def __init__(self, phrase: str = "", **kwargs):
        self.current_phrase = phrase or "Grooving..."
        kwargs.setdefault("classes", "processing-status")
        super().__init__(**kwargs)

    def on_mount(self):
        self._frame = 0
        self._timer = self.set_interval(0.08, self._advance_spinner)

    def on_unmount(self):
        if hasattr(self, '_timer') and self._timer:
            self._timer.stop()
            self._timer = None

    def _advance_spinner(self):
        self._frame += 1
        self.elapsed += 0.08
        self.refresh()

    def _get_icon(self) -> str:
        """Get spinner icon based on frame."""
        return SPINNER_FRAMES[self._frame % len(SPINNER_FRAMES)]

    def _format_spinner(self) -> Text:
        """Format the spinner line."""
        t = Text()
        icon = self._get_icon()
        t.append(f"{icon} ", PROCESSING)
        t.append(self.current_phrase, PROCESSING)
        t.append(" (esc to interrupt)", TEXT_DIM)
        
        if self.elapsed > 0:
            t.append(f"  \u00B7  {self.elapsed:.0f}s", TEXT_DIM)
        
        return t

    def render(self) -> Text:
        """Render the processing status."""
        return self._format_spinner()

    def set_phrase(self, phrase: str):
        """Update the processing phrase."""
        self.current_phrase = phrase
        self.refresh()

    def set_timing(self, elapsed: float, tokens: int = 0):
        """Update timing information."""
        self.elapsed = elapsed
        if tokens > 0:
            self._tokens = tokens
        self.refresh()

"""Agent state machine and timer orchestration for the response lifecycle."""

from enum import Enum
from typing import Optional

from .ui.working_status import WorkingStatus
from .ui.widgets import ThinkingIndicator, MessageBubble


class AgentState(Enum):
    IDLE = "idle"
    USER_SUBMITTED = "user_submitted"
    WORKING = "working"
    THINKING = "thinking"
    TOOL_EXECUTION = "tool_execution"
    WAITING_FOR_APPROVAL = "waiting_for_approval"
    FINAL_RESPONSE = "final_response"
    COMPLETE = "complete"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class AgentStateManager:
    """Manages the agent response lifecycle and associated UI timers."""

    def __init__(self, app):
        self.app = app
        self.state = AgentState.IDLE
        self._spinner_timer = None
        self._phrase_timer = None
        self._working_widget: Optional[WorkingStatus] = None
        self._thinking_widget: Optional[ThinkingIndicator] = None
        self._current_bubble: Optional[MessageBubble] = None

    def start(self):
        """USER_SUBMITTED → immediately show funny working message."""
        self.state = AgentState.USER_SUBMITTED
        self._start_spinner()
        self._start_phrase_rotation()
        self._mount_working_status()

    def begin_thinking(self):
        """WORKING/USER_SUBMITTED → thinking: remove working, show thinking."""
        self.state = AgentState.THINKING
        self._stop_phrase_rotation()
        self._remove_working_status()
        self._mount_thinking_indicator()

    def begin_tool_execution(self):
        """THINKING → TOOL_EXECUTION."""
        self.state = AgentState.TOOL_EXECUTION
        self._stop_phrase_rotation()
        self._remove_working_status()
        if self._thinking_widget:
            self._thinking_widget.update_thinking("Executing tools...")

    def begin_awaiting_approval(self, tool_name: str, description: str):
        """TOOL_EXECUTION → WAITING_FOR_APPROVAL."""
        self.state = AgentState.WAITING_FOR_APPROVAL
        if self._thinking_widget:
            self._thinking_widget.update_thinking(f"Awaiting approval: {tool_name}")

    def begin_response(self, response: str, thinking: str = ""):
        """THINKING → FINAL_RESPONSE: remove thinking, mount bubble, reveal."""
        self.state = AgentState.FINAL_RESPONSE
        self._stop_spinner()
        self._remove_thinking_indicator()

        try:
            scroll = self.app.query_one("#chat-scroll")
        except Exception:
            self.state = AgentState.COMPLETE
            return

        bubble = MessageBubble(
            role="assistant",
            content="",
            model=getattr(self.app, "current_model", ""),
            thinking=thinking,
        )
        self._current_bubble = bubble
        scroll.mount(bubble)
        if hasattr(self.app, '_smart_scroll'):
            self.app._smart_scroll()
        else:
            scroll.scroll_end(animate=False)
        bubble.start_reveal(response)

    def finish(self):
        """FINAL_RESPONSE → COMPLETE: clean up all timers."""
        self._stop_spinner()
        self._stop_phrase_rotation()
        self._stop_reveal()
        self.state = AgentState.COMPLETE

    def handle_error(self):
        """Error path: clean everything and go to COMPLETE."""
        self._stop_spinner()
        self._stop_phrase_rotation()
        self._stop_reveal()
        self._remove_working_status()
        self._remove_thinking_indicator()
        self.state = AgentState.COMPLETE

    def reset(self):
        """Return to IDLE."""
        self._stop_spinner()
        self._stop_phrase_rotation()
        self._stop_reveal()
        self._remove_working_status()
        self._remove_thinking_indicator()
        if self._current_bubble:
            self._current_bubble.finish_reveal()
            self._current_bubble = None
        self.state = AgentState.IDLE

    # ── Timer management ──────────────────────────────────────────

    def _start_spinner(self):
        self._stop_spinner()
        self._spinner_timer = self.app.set_interval(
            0.08, self._on_spinner_tick
        )

    def _stop_spinner(self):
        if self._spinner_timer:
            self._spinner_timer.stop()
            self._spinner_timer = None

    def _on_spinner_tick(self):
        if self.state in (AgentState.IDLE, AgentState.COMPLETE):
            self._stop_spinner()
            return
        if self._thinking_widget and self._thinking_widget.active:
            self._thinking_widget.advance()

    def _start_phrase_rotation(self):
        self._stop_phrase_rotation()
        self._phrase_timer = self.app.set_interval(
            2.5, self._on_phrase_tick
        )

    def _stop_phrase_rotation(self):
        if self._phrase_timer:
            self._phrase_timer.stop()
            self._phrase_timer = None

    def _on_phrase_tick(self):
        if self.state not in (AgentState.USER_SUBMITTED, AgentState.WORKING):
            self._stop_phrase_rotation()

    def _stop_reveal(self):
        if self._current_bubble:
            self._current_bubble.finish_reveal()

    # ── Widget mount/unmount ───────────────────────────────────────

    def _mount_working_status(self):
        try:
            scroll = self.app.query_one("#chat-scroll")
        except Exception:
            return
        self._working_widget = WorkingStatus(classes="working-status")
        scroll.mount(self._working_widget)
        if hasattr(self.app, '_smart_scroll'):
            self.app._smart_scroll()
        else:
            scroll.scroll_end(animate=False)

    def _remove_working_status(self):
        if self._working_widget:
            try:
                self._working_widget.remove()
            except Exception:
                pass
            self._working_widget = None

    def _mount_thinking_indicator(self):
        try:
            scroll = self.app.query_one("#chat-scroll")
        except Exception:
            return
        self._thinking_widget = ThinkingIndicator(classes="thinking-indicator")
        scroll.mount(self._thinking_widget)
        self._thinking_widget.activate()
        if hasattr(self.app, '_smart_scroll'):
            self.app._smart_scroll()
        else:
            scroll.scroll_end(animate=False)

    def _remove_thinking_indicator(self):
        if self._thinking_widget:
            self._thinking_widget.deactivate()
            try:
                self._thinking_widget.remove()
            except Exception:
                pass
            self._thinking_widget = None

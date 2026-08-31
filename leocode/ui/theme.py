"""LeoCode TUI theme — Claude Code faithful reimplementation."""

from __future__ import annotations

from rich.text import Text

# ──────────────────────────────────────────────
#  Claude Code Color Tokens — Faithful Match
# ──────────────────────────────────────────────

# Claude Code uses a dark, muted background
BG = "#1a1a2e"  # Dark navy background
BG_HEADER = "#16162a"  # Slightly darker header
BG_INPUT = "#252540"  # Input field background
BG_PANEL = "#1a1a2e"  # Panel background

# Text hierarchy — Claude Code uses muted, low-contrast text
TEXT = "#a0a0b0"  # Primary text - muted gray
TEXT_SECONDARY = "#606070"  # Secondary text
TEXT_MUTED = "#606070"  # Muted text (alias)
TEXT_DIM = "#404050"  # Dimmed text
TEXT_BRIGHT = "#c0c0d0"  # Bright text

# Borders
BORDER = "#303050"  # Default border
BORDER_SUBTLE = "#2a2a45"  # Subtle border

# Status colors — Claude Code uses subtle, not saturated
SUCCESS = "#50a070"  # Muted green
WARNING = "#c0a050"  # Muted amber
ERROR = "#c05050"  # Muted red
INFO = "#5080c0"  # Muted blue

# Processing/thinking colors
PROCESSING = "#c07050"  # Muted orange

# Mode colors
PLAN_MODE = "#5080c0"  # Blue for plan mode
AUTO_ACCEPT = "#c07050"  # Orange for auto mode
BYPASS = "#c05050"  # Red for bypass
BUILD = "#c07050"  # Orange for build
MANUAL = "#606070"  # Muted gray for manual

# Semantic aliases
ACCENT = PROCESSING
ACCENT_HOVER = "#d08060"
CLAUDE = PROCESSING  # Brand color
CLAUDE_SHIMMER = "#d08060"
USER = "#50a070"  # User message color
ASSISTANT = TEXT
SYSTEM = TEXT_SECONDARY
MUTED = TEXT_SECONDARY
SURFACE = BG_HEADER
PERMISSION = WARNING

# Diff colors — Claude Code style
DIFF_ADDED = "#1a2e1a"  # Subtle green background
DIFF_REMOVED = "#2e1a1a"  # Subtle red background
DIFF_ADDED_DIMMED = "#1a251a"  # Even more subtle
DIFF_REMOVED_DIMMED = "#251a1a"  # Even more subtle
DIFF_ADDED_WORD = "#50a070"  # Green text
DIFF_REMOVED_WORD = "#c05050"  # Red text

# Labels
BRIEF_LABEL_YOU = "#50a070"
BRIEF_LABEL_CLAUDE = PROCESSING


# ──────────────────────────────────────────────
#  Helper Functions
# ──────────────────────────────────────────────

def short_path(path: str, limit: int = 60) -> str:
    """Truncate a file path for display."""
    from pathlib import Path
    if not path:
        return ""
    home = str(Path.home())
    if path.startswith(home):
        path = "~" + path[len(home):]
    if len(path) > limit:
        return "\u2026" + path[-(limit - 1):]
    return path


def short_model(model: str) -> str:
    """Extract short model name."""
    if not model:
        return "no model"
    return model.split("/")[-1] if "/" in model else model


def format_size(lines: int) -> str:
    """Format line count for display."""
    if lines == 1:
        return "1 line"
    return f"{lines} lines"


# ──────────────────────────────────────────────
#  CSS — Claude Code Faithful Style
# ──────────────────────────────────────────────

CSS = f"""
Screen {{
    background: {BG};
    color: {TEXT};
}}

#main {{
    layout: vertical;
    height: 1fr;
    background: {BG};
    width: 100%;
}}

/* Chat scroll area — full height transcript */
#chat-scroll {{
    height: 1fr;
    background: {BG};
    padding: 1 2;
    scrollbar-background: {BG};
    scrollbar-color: {BORDER};
    scrollbar-color-hover: {CLAUDE};
    scrollbar-size: 1 1;
    scrollbar-gutter: stable;
}}

/* Scrollbar styling */
VerticalScrollBar {{
    background: {BG};
    color: {BORDER};
}}

VerticalScrollBar > Handle {{
    background: {BORDER};
    color: {CLAUDE};
}}

/* Welcome banner — Claude Code style */
.welcome-box {{
    height: auto;
    background: transparent;
    padding: 2 0;
    margin: 0;
}}

/* Message areas — Claude Code style */
.message-area {{
    padding: 0 0;
    height: auto;
    background: transparent;
}}

.message-user {{
    background: transparent;
    border: none;
    padding: 0;
    margin: 0;
}}

.message-assistant {{
    background: transparent;
    border: none;
    padding: 0;
    margin: 0;
}}

.message-system {{
    background: transparent;
    border: none;
    padding: 0;
    margin: 0;
}}

/* Processing status indicator */
.processing-status {{
    height: auto;
    background: transparent;
    padding: 0 0;
    margin: 1 0;
}}

.processing-header {{
    color: {PROCESSING};
    height: 1;
}}

.processing-details {{
    color: {TEXT_SECONDARY};
    height: 1;
}}

.processing-next {{
    color: {TEXT_SECONDARY};
    height: 1;
    padding: 0 0 0 2;
}}

/* Thinking indicator */
.thinking-indicator {{
    height: auto;
    background: transparent;
    padding: 0 0;
    margin: 1 0;
}}

.thinking-header {{
    color: {TEXT_SECONDARY};
    height: 1;
}}

.thinking-panel {{
    height: auto;
    max-height: 12;
    background: {BG_HEADER};
    border: heavy {BORDER};
    padding: 0 1;
    margin: 0 0 0 2;
    color: {TEXT_SECONDARY};
    overflow-y: auto;
    display: none;
}}

.thinking-panel.visible {{
    display: block;
}}

/* Composer — input area at bottom — Claude Code style */
#composer {{
    dock: bottom;
    height: auto;
    min-height: 3;
    background: {BG};
    border-top: heavy {BORDER};
    padding: 1 2 0 2;
}}

#composer-input {{
    height: auto;
    min-height: 3;
    background: {BG};
}}

#composer-prefix {{
    width: 2;
    color: {TEXT_SECONDARY};
    content-align: left middle;
}}

#user-input {{
    width: 1fr;
    height: auto;
    min-height: 3;
    background: {BG};
    border: none;
    color: {TEXT};
}}

#user-input:focus {{
    border: none;
    background: {BG};
}}

/* Input hint area */
#input-hint {{
    height: 1;
    color: {TEXT_DIM};
    padding: 0 2;
    background: transparent;
}}

/* Status bar — Claude Code footer */
#status-bar {{
    dock: bottom;
    height: 1;
    background: {BG};
    color: {TEXT_DIM};
    padding: 0 2;
    border-top: heavy {BORDER};
}}

/* Status items */
.status-left {{
    height: 1;
    color: {TEXT_DIM};
}}

.status-right {{
    height: 1;
    color: {TEXT_DIM};
}}

.status-mode {{
    color: {TEXT_SECONDARY};
}}

.status-indicator {{
    color: {CLAUDE};
}}

.status-text {{
    color: {SUCCESS};
}}

/* Banner messages */
.error-message {{
    color: {ERROR};
    padding: 0 0;
    margin: 1 0;
}}

.warning-message {{
    color: {WARNING};
    padding: 0 0;
    margin: 1 0;
}}

.info-message {{
    color: {INFO};
    padding: 0 0;
    margin: 1 0;
}}

.success-message {{
    color: {SUCCESS};
    padding: 0 0;
    margin: 1 0;
}}

/* Tool results */
.tool-result {{
    padding: 1 0;
    margin: 1 0;
    height: auto;
    background: transparent;
}}

.tool-result-header {{
    color: {SUCCESS};
    height: 1;
}}

.tool-result-body {{
    color: {TEXT_SECONDARY};
    height: 1;
    padding: 0 0 0 2;
}}

/* Diff widget — Claude Code style */
.diff-widget {{
    padding: 0 0;
    margin: 1 0;
    height: auto;
    background: transparent;
}}

.diff-header {{
    color: {TEXT_SECONDARY};
    height: auto;
}}

.diff-expanded {{
    background: {BG_HEADER};
    border: heavy {BORDER_SUBTLE};
    padding: 0 1;
    height: auto;
    max-height: 30;
}}

/* Permission prompt — Claude Code style */
.permission-box {{
    background: {BG};
    border: heavy {WARNING};
    padding: 1 2;
    height: auto;
    margin: 1 0;
}}

.permission-action {{
    color: {TEXT};
    height: auto;
}}

.permission-options {{
    color: {TEXT_SECONDARY};
    height: auto;
}}

.permission-result {{
    color: {SUCCESS};
    height: auto;
}}

/* Todo panel */
.todo-inline {{
    height: auto;
    background: transparent;
    padding: 1 0;
    margin: 1 0;
}}

/* Tool activity */
.tool-activity-inline {{
    height: auto;
    background: transparent;
    padding: 0 0;
    margin: 0 0;
}}

/* Buttons */
Button {{
    background: {BG_INPUT};
    color: {TEXT_SECONDARY};
    border: none;
    height: 3;
}}

Button:hover {{
    background: {BG_HEADER};
    color: {TEXT};
}}

Button.-primary {{
    background: {CLAUDE};
    color: {BG};
}}

Button.-primary:hover {{
    background: {CLAUDE_SHIMMER};
}}

/* Option lists */
OptionList {{
    background: {BG_HEADER};
    border: none;
    scrollbar-background: {BG_HEADER};
    scrollbar-color: {BORDER};
    scrollbar-color-hover: {CLAUDE};
}}

OptionList > .option-list--option {{
    color: {TEXT_SECONDARY};
    padding: 0 1;
}}

OptionList > .option-list--option-highlighted {{
    background: {BG_INPUT};
    color: {TEXT};
}}

/* Modal overlay — Claude Code style */
ModalScreen {{
    align: center middle;
    background: {BG} 80%;
}}

#modal {{
    width: 72;
    height: auto;
    max-height: 32;
    background: {BG_HEADER};
    border: heavy {CLAUDE};
    padding: 1 2;
}}

#modal.wide {{
    width: 80;
    max-height: 36;
}}

.modal-title {{
    height: 1;
    color: {TEXT};
    text-style: bold;
    padding: 0 1 1 1;
}}

.modal-sub {{
    height: 1;
    color: {TEXT_SECONDARY};
    padding: 0 1 1 1;
}}

.modal-search {{
    width: 1fr;
    background: {BG};
    border: heavy {BORDER};
    color: {TEXT};
    margin-bottom: 1;
}}

.modal-search:focus {{
    border: heavy {CLAUDE};
}}

.modal-list {{
    height: auto;
    max-height: 18;
    background: {BG};
    border: heavy {BORDER};
    padding: 0 1;
}}

.modal-footer {{
    height: 1;
    color: {TEXT_DIM};
    padding: 1 1 0 1;
}}

.help-body {{
    height: auto;
    max-height: 24;
    padding: 0 1;
    color: {TEXT_SECONDARY};
}}

/* Tree connectors */
.tree-connector {{
    color: {TEXT_SECONDARY};
}}

.tree-connector-first {{
    color: {TEXT_SECONDARY};
}}

/* Spacers */
.spacer {{
    height: 1;
}}

/* Scrollable containers */
ScrollableContainer {{
    scrollbar-background: {BG};
    scrollbar-color: {BORDER};
    scrollbar-color-hover: {CLAUDE};
    scrollbar-size: 1 1;
}}

/* Input styling — Claude Code style */
Input {{
    background: {BG};
    border: none;
    color: {TEXT};
}}

Input:focus {{
    border: none;
    background: {BG};
}}

Input > .input--placeholder {{
    color: {TEXT_DIM};
}}
"""

# Modal CSS for dialogs
MODAL_CSS = f"""
ModalScreen {{
    align: center middle;
    background: {BG} 80%;
}}

#modal {{
    width: 72;
    height: auto;
    max-height: 32;
    background: {BG_HEADER};
    border: heavy {CLAUDE};
    padding: 1 2;
}}

#modal.wide {{
    width: 80;
    max-height: 36;
}}

.modal-title {{
    height: 1;
    color: {TEXT};
    text-style: bold;
    padding: 0 1 1 1;
}}

.modal-sub {{
    height: 1;
    color: {TEXT_SECONDARY};
    padding: 0 1 1 1;
}}

.modal-search {{
    width: 1fr;
    background: {BG};
    border: heavy {BORDER};
    color: {TEXT};
    margin-bottom: 1;
}}

.modal-search:focus {{
    border: heavy {CLAUDE};
}}

.modal-list {{
    height: auto;
    max-height: 18;
    background: {BG};
    border: heavy {BORDER};
    padding: 0 1;
}}

.modal-footer {{
    height: 1;
    color: {TEXT_DIM};
    padding: 1 1 0 1;
}}

.help-body {{
    height: auto;
    max-height: 24;
    padding: 0 1;
    color: {TEXT_SECONDARY};
}}
"""

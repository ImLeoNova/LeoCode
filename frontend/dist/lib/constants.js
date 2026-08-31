/**
 * LeoCode Constants
 */
export const APP_NAME = 'LeoCode';
export const APP_VERSION = '1.0.0';
export const APP_DESCRIPTION = 'AI coding assistant';
// Terminal defaults
export const MIN_COLUMNS = 80;
export const MIN_ROWS = 24;
export const DEFAULT_COLUMNS = 120;
export const DEFAULT_ROWS = 40;
// Layout dimensions
export const STATUS_BAR_HEIGHT = 1; // 1 line
export const HELP_BAR_HEIGHT = 1; // 1 line
export const INPUT_MIN_HEIGHT = 1; // 1 line (single-line)
export const INPUT_MAX_HEIGHT = 15; // Max input height before scrolling
export const VIRTUAL_SCROLL_OVERSCAN = 10; // Extra messages above/below viewport
// Animation
export const SPINNER_INTERVAL_MS = 80;
export const STREAMING_DELAY_MS = 16; // ~60fps streaming
// IPC
export const IPC_TIMEOUT_MS = 30000;
// Message types
export const MSG_USER = 'user';
export const MSG_ASSISTANT = 'assistant';
export const MSG_SYSTEM = 'system';
export const MSG_TOOL_USE = 'tool_use';
export const MSG_TOOL_RESULT = 'tool_result';
// Tool states
export const TOOL_PENDING = 'pending';
export const TOOL_RUNNING = 'running';
export const TOOL_SUCCESS = 'success';
export const TOOL_ERROR = 'error';
// Agent states
export const AGENT_IDLE = 'idle';
export const AGENT_THINKING = 'thinking';
export const AGENT_STREAMING = 'streaming';
export const AGENT_TOOL_USE = 'tool_use';
export const AGENT_COMPLETE = 'complete';
// Permission actions
export const PERM_ALLOW = 'allow';
export const PERM_DENY = 'deny';
export const PERM_ALWAYS = 'always_allow';
export const PERM_ONCE = 'allow_once';
// Slash commands
export const SLASH_COMMANDS = [
    { name: '/help', description: 'Show help' },
    { name: '/clear', description: 'Clear conversation' },
    { name: '/model', description: 'Switch model' },
    { name: '/config', description: 'Open config' },
    { name: '/compact', description: 'Compact conversation' },
    { name: '/sessions', description: 'Browse sessions' },
    { name: '/theme', description: 'Change theme' },
    { name: '/doctor', description: 'Run diagnostics' },
    { name: '/mcp', description: 'Manage MCP servers' },
    { name: '/plan', description: 'Switch to plan mode' },
    { name: '/code', description: 'Switch to code mode' },
];
//# sourceMappingURL=constants.js.map
/**
 * LeoCode Constants
 */
export declare const APP_NAME = "LeoCode";
export declare const APP_VERSION = "1.0.0";
export declare const APP_DESCRIPTION = "AI coding assistant";
export declare const MIN_COLUMNS = 80;
export declare const MIN_ROWS = 24;
export declare const DEFAULT_COLUMNS = 120;
export declare const DEFAULT_ROWS = 40;
export declare const STATUS_BAR_HEIGHT = 1;
export declare const HELP_BAR_HEIGHT = 1;
export declare const INPUT_MIN_HEIGHT = 1;
export declare const INPUT_MAX_HEIGHT = 15;
export declare const VIRTUAL_SCROLL_OVERSCAN = 10;
export declare const SPINNER_INTERVAL_MS = 80;
export declare const STREAMING_DELAY_MS = 16;
export declare const IPC_TIMEOUT_MS = 30000;
export declare const MSG_USER = "user";
export declare const MSG_ASSISTANT = "assistant";
export declare const MSG_SYSTEM = "system";
export declare const MSG_TOOL_USE = "tool_use";
export declare const MSG_TOOL_RESULT = "tool_result";
export declare const TOOL_PENDING = "pending";
export declare const TOOL_RUNNING = "running";
export declare const TOOL_SUCCESS = "success";
export declare const TOOL_ERROR = "error";
export declare const AGENT_IDLE = "idle";
export declare const AGENT_THINKING = "thinking";
export declare const AGENT_STREAMING = "streaming";
export declare const AGENT_TOOL_USE = "tool_use";
export declare const AGENT_COMPLETE = "complete";
export declare const PERM_ALLOW = "allow";
export declare const PERM_DENY = "deny";
export declare const PERM_ALWAYS = "always_allow";
export declare const PERM_ONCE = "allow_once";
export declare const SLASH_COMMANDS: readonly [{
    readonly name: "/help";
    readonly description: "Show help";
}, {
    readonly name: "/clear";
    readonly description: "Clear conversation";
}, {
    readonly name: "/model";
    readonly description: "Switch model";
}, {
    readonly name: "/config";
    readonly description: "Open config";
}, {
    readonly name: "/compact";
    readonly description: "Compact conversation";
}, {
    readonly name: "/sessions";
    readonly description: "Browse sessions";
}, {
    readonly name: "/theme";
    readonly description: "Change theme";
}, {
    readonly name: "/doctor";
    readonly description: "Run diagnostics";
}, {
    readonly name: "/mcp";
    readonly description: "Manage MCP servers";
}, {
    readonly name: "/plan";
    readonly description: "Switch to plan mode";
}, {
    readonly name: "/code";
    readonly description: "Switch to code mode";
}];
//# sourceMappingURL=constants.d.ts.map
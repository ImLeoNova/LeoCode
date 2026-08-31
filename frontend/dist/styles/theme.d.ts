/**
 * LeoCode Terminal Theme
 * Based on Claude Code's visual language, branded as LeoCode
 *
 * Color tokens follow a semantic naming convention:
 * - bg.* : background colors
 * - fg.* : foreground/text colors
 * - border.* : border colors
 * - accent.* : accent/highlight colors
 * - status.* : status indicator colors
 * - diff.* : diff rendering colors
 * - tool.* : tool execution colors
 */
export declare const theme: {
    readonly bg: {
        readonly default: "#1a1b26";
        readonly elevated: "#1f2030";
        readonly sunken: "#141520";
        readonly input: "#1f2030";
        readonly hover: "#252638";
        readonly selected: "#2a2b3d";
        readonly overlay: "#0d0e16";
    };
    readonly fg: {
        readonly primary: "#c0caf5";
        readonly secondary: "#9aa5ce";
        readonly muted: "#565f89";
        readonly dim: "#414868";
        readonly bright: "#e0e6ff";
        readonly inverse: "#1a1b26";
    };
    readonly border: {
        readonly default: "#33354a";
        readonly subtle: "#292d42";
        readonly active: "#7aa2f7";
        readonly muted: "#24283b";
    };
    readonly accent: {
        readonly primary: "#7aa2f7";
        readonly secondary: "#bb9af7";
        readonly brand: "#e0af68";
        readonly link: "#7dcfff";
        readonly code: "#9ece6a";
    };
    readonly status: {
        readonly success: "#9ece6a";
        readonly warning: "#e0af68";
        readonly error: "#f7768e";
        readonly info: "#7aa2f7";
        readonly processing: "#ff9e64";
        readonly thinking: "#bb9af7";
        readonly idle: "#565f89";
    };
    readonly diff: {
        readonly added: "#1a2e1a";
        readonly addedText: "#9ece6a";
        readonly removed: "#2e1a1a";
        readonly removedText: "#f7768e";
        readonly context: "#1a1b26";
        readonly header: "#292d42";
    };
    readonly tool: {
        readonly running: "#7aa2f7";
        readonly success: "#9ece6a";
        readonly error: "#f7768e";
        readonly pending: "#565f89";
        readonly border: "#33354a";
    };
    readonly permission: {
        readonly allow: "#9ece6a";
        readonly deny: "#f7768e";
        readonly warning: "#e0af68";
        readonly background: "#1f2030";
    };
    readonly syntax: {
        readonly keyword: "#bb9af7";
        readonly string: "#9ece6a";
        readonly number: "#ff9e64";
        readonly comment: "#565f89";
        readonly function: "#7aa2f7";
        readonly variable: "#c0caf5";
        readonly type: "#2ac3de";
        readonly operator: "#89ddff";
        readonly punctuation: "#a9b1d6";
        readonly tag: "#f7768e";
        readonly attribute: "#e0af68";
        readonly constant: "#ff9e64";
        readonly regex: "#b4f9f8";
    };
};
export declare const semantic: {
    readonly userMessage: "#c0caf5";
    readonly userPrefix: "#e0af68";
    readonly assistantMessage: "#9aa5ce";
    readonly errorMessage: "#f7768e";
    readonly successMessage: "#9ece6a";
    readonly codeBlock: "#141520";
    readonly codeBorder: "#292d42";
    readonly prompt: "#e0af68";
    readonly helpBar: "#565f89";
    readonly statusBar: "#565f89";
    readonly statusBarBorder: "#292d42";
    readonly toolBorder: "#24283b";
};
export type Theme = typeof theme;
export type Semantic = typeof semantic;
//# sourceMappingURL=theme.d.ts.map
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

export const theme = {
  // Background colors
  bg: {
    default: '#1a1b26',      // Main background
    elevated: '#1f2030',     // Elevated surfaces (input, cards)
    sunken: '#141520',       // Sunken areas
    input: '#1f2030',        // Input background
    hover: '#252638',        // Hover state
    selected: '#2a2b3d',     // Selected state
    overlay: '#0d0e16',      // Overlay/modal background
  },

  // Foreground/text colors
  fg: {
    primary: '#c0caf5',      // Primary text (bright) - user messages
    secondary: '#9aa5ce',    // Secondary text - assistant messages (more muted)
    muted: '#565f89',        // Muted text
    dim: '#414868',          // Very dim text
    bright: '#e0e6ff',       // Bright/highlighted text
    inverse: '#1a1b26',      // Inverse text (on highlighted bg)
  },

  // Border colors
  border: {
    default: '#33354a',      // Default borders
    subtle: '#292d42',       // Subtle borders
    active: '#7aa2f7',       // Active/focused borders
    muted: '#24283b',        // Very muted borders (tool blocks)
  },

  // Accent colors
  accent: {
    primary: '#7aa2f7',      // Primary accent (blue)
    secondary: '#bb9af7',    // Secondary accent (purple)
    brand: '#e0af68',        // LeoCode brand color (warm gold)
    link: '#7dcfff',         // Link color (cyan)
    code: '#9ece6a',         // Inline code color (green)
  },

  // Status colors
  status: {
    success: '#9ece6a',      // Success/complete
    warning: '#e0af68',      // Warning
    error: '#f7768e',        // Error
    info: '#7aa2f7',         // Info
    processing: '#ff9e64',   // Processing/thinking
    thinking: '#bb9af7',     // Thinking (purple)
    idle: '#565f89',         // Idle state
  },

  // Diff colors
  diff: {
    added: '#1a2e1a',        // Added line background
    addedText: '#9ece6a',    // Added line text
    removed: '#2e1a1a',      // Removed line background
    removedText: '#f7768e',  // Removed line text
    context: '#1a1b26',      // Context line background
    header: '#292d42',       // Diff header background
  },

  // Tool execution colors
  tool: {
    running: '#7aa2f7',      // Tool running
    success: '#9ece6a',      // Tool completed
    error: '#f7768e',        // Tool failed
    pending: '#565f89',      // Tool pending
    border: '#33354a',       // Tool block border
  },

  // Permission colors
  permission: {
    allow: '#9ece6a',        // Allow action
    deny: '#f7768e',         // Deny action
    warning: '#e0af68',      // Warning
    background: '#1f2030',   // Permission dialog bg
  },

  // Syntax highlighting (Tokyo Night palette)
  syntax: {
    keyword: '#bb9af7',
    string: '#9ece6a',
    number: '#ff9e64',
    comment: '#565f89',
    function: '#7aa2f7',
    variable: '#c0caf5',
    type: '#2ac3de',
    operator: '#89ddff',
    punctuation: '#a9b1d6',
    tag: '#f7768e',
    attribute: '#e0af68',
    constant: '#ff9e64',
    regex: '#b4f9f8',
  },
} as const;

// Semantic aliases
export const semantic = {
  userMessage: theme.fg.primary,
  userPrefix: theme.accent.brand,        // ">" marker for user messages
  assistantMessage: theme.fg.secondary,   // Muted/softer for assistant
  errorMessage: theme.status.error,
  successMessage: theme.status.success,
  codeBlock: theme.bg.sunken,
  codeBorder: theme.border.subtle,
  prompt: theme.accent.brand,
  helpBar: theme.fg.muted,
  statusBar: theme.fg.muted,
  statusBarBorder: theme.border.subtle,
  toolBorder: theme.border.muted,        // Subtle border for tool blocks
} as const;

export type Theme = typeof theme;
export type Semantic = typeof semantic;

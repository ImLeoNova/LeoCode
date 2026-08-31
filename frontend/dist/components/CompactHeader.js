import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Box, Text } from 'ink';
import { theme } from '../styles/theme.js';
import { APP_NAME, APP_VERSION } from '../lib/constants.js';
/**
 * CompactHeader - Persistent branding header for active sessions
 *
 * Claude Code style: minimal, single-line branding with the hint message
 * Always visible at the top, never disappears once chat starts
 */
export const CompactHeader = () => {
    return (_jsxs(Box, { flexDirection: "column", paddingLeft: 2, paddingTop: 1, paddingBottom: 1, children: [_jsxs(Box, { children: [_jsx(Text, { color: theme.accent.brand, bold: true, children: APP_NAME }), _jsxs(Text, { color: theme.fg.dim, children: [" v", APP_VERSION] })] }), _jsx(Box, { marginTop: 1, children: _jsxs(Text, { color: theme.fg.dim, children: ["Type a message to start, or use", ' ', _jsx(Text, { color: theme.fg.muted, children: "/help" }), ' ', "for commands."] }) })] }));
};
//# sourceMappingURL=CompactHeader.js.map
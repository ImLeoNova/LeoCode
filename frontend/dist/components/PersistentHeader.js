import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Box, Text } from 'ink';
import { theme } from '../styles/theme.js';
import { APP_NAME, APP_VERSION } from '../lib/constants.js';
/**
 * PersistentHeader - ALWAYS visible header with branding and hint
 *
 * This component is NEVER unmounted or conditionally hidden.
 * It appears at the top of every screen state: idle, chatting, streaming, etc.
 * No props control its visibility - it's permanently rendered.
 */
export const PersistentHeader = () => {
    return (_jsxs(Box, { flexDirection: "column", paddingLeft: 2, paddingTop: 1, paddingBottom: 1, flexShrink: 0, children: [_jsxs(Box, { children: [_jsx(Text, { color: theme.accent.brand, bold: true, children: APP_NAME }), _jsxs(Text, { color: theme.fg.dim, children: [" v", APP_VERSION] })] }), _jsx(Box, { marginTop: 1, children: _jsxs(Text, { color: theme.fg.dim, children: ["Type a message to start, or use", ' ', _jsx(Text, { color: theme.fg.muted, children: "/help" }), ' ', "for commands."] }) })] }));
};
//# sourceMappingURL=PersistentHeader.js.map
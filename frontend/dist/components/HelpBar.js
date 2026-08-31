import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Box, Text } from 'ink';
import { theme } from '../styles/theme.js';
/**
 * HelpBar - Bottom help bar showing keyboard shortcuts
 * Claude Code style: compact, single line, minimal
 * With proper left/right padding so nothing touches the terminal edges
 */
export const HelpBar = ({ columns = 120 }) => {
    return (_jsx(Box, { flexDirection: "row", justifyContent: "center", paddingLeft: 2, paddingRight: 2, paddingTop: 0, paddingBottom: 0, flexShrink: 0, children: _jsxs(Text, { color: theme.fg.dim, children: [_jsx(Text, { color: theme.fg.muted, children: "Enter" }), " send \u00B7 ", _jsx(Text, { color: theme.fg.muted, children: "Shift+Enter" }), " newline \u00B7 ", _jsx(Text, { color: theme.fg.muted, children: "Esc" }), " interrupt \u00B7 ", _jsx(Text, { color: theme.fg.muted, children: "Ctrl+Q" }), " quit \u00B7 ", _jsx(Text, { color: theme.fg.muted, children: "/help" }), " commands"] }) }));
};
//# sourceMappingURL=HelpBar.js.map
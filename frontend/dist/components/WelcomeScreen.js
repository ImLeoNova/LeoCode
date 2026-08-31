import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Box, Text } from 'ink';
import { theme } from '../styles/theme.js';
import { APP_NAME, APP_VERSION } from '../lib/constants.js';
const ASCII_LOGO_MIN_WIDTH = 64;
// Keep this as ONE multi-line string, not an array of separate lines.
// Ink measures a single Text node's width using the widest embedded line
// (see the `widest-line` dependency), which is what lets Box's
// alignItems="center" center the whole block correctly as one unit.
// Splitting it into multiple <Text> elements makes each line wrap/measure
// independently, which is what was breaking the shape.
const ASCII_LOGO = [
    '██╗     ███████╗ ██████╗  ██████╗ ██████╗ ██████╗ ███████╗',
    '██║     ██╔════╝██╔═══██╗██╔════╝██╔═══██╗██╔══██╗██╔════╝',
    '██║     █████╗  ██║   ██║██║     ██║   ██║██║  ██║█████╗  ',
    '██║     ██╔══╝  ██║   ██║██║     ██║   ██║██║  ██║██╔══╝  ',
    '███████╗███████╗╚██████╔╝╚██████╗╚██████╔╝██████╔╝███████╗',
    '╚══════╝╚══════╝ ╚═════╝  ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝',
].join('\n');
/**
 * WelcomeScreen - Full welcome banner (shown only on initial idle state)
 * Claude Code style: centered, spacious, low contrast
 */
export const WelcomeScreen = ({ columns = 120 }) => {
    const showWideLogo = columns >= ASCII_LOGO_MIN_WIDTH;
    return (_jsxs(Box, { flexDirection: "column", width: "100%", paddingTop: 2, paddingBottom: 1, children: [_jsx(Box, { flexDirection: "column", width: "100%", alignItems: "center", children: showWideLogo ? (
                // wrap="truncate-end" is critical here: without it, Ink's default
                // wrap="wrap" can reflow the block-drawing characters the moment
                // available width is even 1 column short of 60, which staircases
                // the whole logo. truncate-end just clips instead of reflowing.
                _jsx(Text, { color: theme.accent.brand, bold: true, wrap: "truncate-end", children: ASCII_LOGO })) : (_jsxs(Text, { color: theme.accent.brand, bold: true, children: [APP_NAME, " v", APP_VERSION] })) }), _jsx(Box, { marginTop: 1, flexDirection: "column", width: "100%", alignItems: "center", children: _jsxs(Text, { color: theme.fg.dim, children: ["v", APP_VERSION] }) }), _jsx(Box, { marginTop: 2, flexDirection: "column", width: "100%", alignItems: "center", children: _jsx(Text, { color: theme.fg.dim, children: '─'.repeat(50) }) }), _jsx(Box, { marginTop: 2, flexDirection: "column", width: "100%", alignItems: "center", children: _jsxs(Text, { color: theme.fg.secondary, children: ["Type a message to start, or use", ' ', _jsx(Text, { color: theme.accent.brand, bold: true, children: "/help" }), ' ', "for commands."] }) }), _jsx(Box, { marginTop: 2, flexDirection: "column", width: "100%", alignItems: "center", children: _jsxs(Text, { color: theme.fg.dim, children: ["Ctrl+", _jsx(Text, { color: theme.fg.muted, children: "N" }), " new chat \u00B7 Ctrl+", _jsx(Text, { color: theme.fg.muted, children: "M" }), " model \u00B7 Ctrl+", _jsx(Text, { color: theme.fg.muted, children: "P" }), " commands \u00B7 Ctrl+", _jsx(Text, { color: theme.fg.muted, children: "Q" }), " quit \u00B7 ", _jsx(Text, { color: theme.fg.muted, children: "Esc" }), " interrupt"] }) })] }));
};
//# sourceMappingURL=WelcomeScreen.js.map
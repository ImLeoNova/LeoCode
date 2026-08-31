import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Box, Text } from 'ink';
import { theme } from '../styles/theme.js';
/**
 * StatusBar - Top status bar (Claude Code style)
 *
 * Compact single line showing:
 * - Model name (left)
 * - Mode (plan/code) indicator
 * - Token count and cost (right)
 *
 * With proper left/right padding so nothing touches the terminal edges
 */
export const StatusBar = ({ agentState, columns }) => {
    const model = agentState.model || 'unknown';
    const tokens = agentState.tokensUsed || 0;
    const cost = agentState.costAccumulated || 0;
    const isStreaming = agentState.isStreaming;
    const mode = agentState.mode || 'code';
    // Compact format
    const tokenStr = tokens > 0
        ? tokens >= 1000
            ? `${(tokens / 1000).toFixed(1)}k`
            : `${tokens}`
        : '';
    const costStr = cost > 0 ? `$${cost.toFixed(4)}` : '';
    return (_jsxs(Box, { flexDirection: "row", justifyContent: "space-between", paddingLeft: 2, paddingRight: 2, paddingTop: 0, paddingBottom: 0, flexShrink: 0, children: [_jsxs(Box, { children: [_jsx(Text, { color: theme.fg.muted, children: model }), _jsx(Text, { color: theme.fg.dim, children: " \u00B7 " }), _jsx(Text, { color: mode === 'plan' ? theme.status.warning : theme.status.success, children: mode.toUpperCase() })] }), _jsxs(Box, { children: [tokenStr && (_jsxs(Text, { color: theme.fg.dim, children: [tokenStr, " tokens"] })), tokenStr && costStr && (_jsx(Text, { color: theme.fg.dim, children: " \u00B7 " })), costStr && (_jsx(Text, { color: theme.fg.dim, children: costStr }))] })] }));
};
//# sourceMappingURL=StatusBar.js.map
import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from 'react';
import { Box, Text, useInput } from 'ink';
import { theme } from '../styles/theme.js';
/**
 * PermissionDialog - Claude Code-style permission prompt
 *
 * Shows what tool is being requested, parameters, and choices.
 * Keyboard-driven: Left/Right to select, Enter to confirm.
 */
export const PermissionDialog = ({ request, onAllow, onDeny, onAlwaysAllow, }) => {
    const [selectedIndex, setSelectedIndex] = useState(0);
    const choices = [
        { label: 'Allow', key: 'allow', action: onAllow, color: theme.permission.allow },
        { label: 'Deny', key: 'deny', action: onDeny, color: theme.permission.deny },
        { label: 'Always Allow', key: 'always', action: onAlwaysAllow, color: theme.permission.warning },
    ];
    useInput((input, key) => {
        if (key.leftArrow) {
            setSelectedIndex(prev => Math.max(0, prev - 1));
        }
        else if (key.rightArrow) {
            setSelectedIndex(prev => Math.min(choices.length - 1, prev + 1));
        }
        else if (key.return) {
            choices[selectedIndex].action();
        }
        else if (input === 'y' || input === 'Y') {
            onAllow();
        }
        else if (input === 'n' || input === 'N') {
            onDeny();
        }
        else if (input === 'a' || input === 'A') {
            onAlwaysAllow();
        }
    });
    const riskColor = {
        safe: theme.status.success,
        low: theme.status.info,
        medium: theme.status.warning,
        high: theme.status.error,
        critical: theme.status.error,
    }[request.risk] || theme.status.warning;
    return (_jsxs(Box, { flexDirection: "column", borderStyle: "round", borderColor: riskColor, paddingLeft: 1, paddingRight: 1, paddingTop: 0, paddingBottom: 0, marginTop: 1, marginBottom: 1, children: [_jsx(Box, { children: _jsx(Text, { color: riskColor, bold: true, children: " \u26A0 Permission Required " }) }), _jsxs(Box, { flexDirection: "column", paddingTop: 0, children: [_jsxs(Text, { color: theme.fg.primary, children: ["Tool: ", _jsx(Text, { bold: true, children: request.toolName })] }), _jsx(Text, { color: theme.fg.secondary, children: request.description }), request.params && (_jsx(Text, { color: theme.fg.dim, children: typeof request.params === 'string'
                            ? request.params
                            : JSON.stringify(request.params) }))] }), _jsx(Box, { paddingTop: 0, children: choices.map((choice, i) => (_jsxs(Text, { children: [i === selectedIndex ? (_jsxs(Text, { color: choice.color, bold: true, inverse: true, children: [" ", choice.label, " "] })) : (_jsxs(Text, { color: theme.fg.muted, children: [" ", choice.label, " "] })), '  '] }, choice.key))) }), _jsx(Box, { children: _jsxs(Text, { color: theme.fg.dim, children: ["Press ", _jsx(Text, { color: theme.fg.muted, children: "Y" }), " allow,", ' ', _jsx(Text, { color: theme.fg.muted, children: "N" }), " deny,", ' ', _jsx(Text, { color: theme.fg.muted, children: "A" }), " always allow"] }) })] }));
};
//# sourceMappingURL=PermissionDialog.js.map
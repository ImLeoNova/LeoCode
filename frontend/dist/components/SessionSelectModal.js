import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState, useEffect } from 'react';
import { Box, Text, useInput } from 'ink';
import { theme } from '../styles/theme.js';
/**
 * SessionSelectModal - Real session picker modal
 *
 * Features:
 * - Scrollable list with Up/Down navigation
 * - Current session highlighted with ●
 * - Enter to resume, Esc to cancel
 *
 * Styled consistently with ModelSelectModal and PermissionDialog.
 */
export const SessionSelectModal = ({ sessions, currentSessionId = '', onSelect, onClose, }) => {
    const [selectedIndex, setSelectedIndex] = useState(0);
    // Auto-select current session on mount
    useEffect(() => {
        const currentIndex = sessions.findIndex(s => s.id === currentSessionId);
        if (currentIndex >= 0) {
            setSelectedIndex(currentIndex);
        }
    }, []);
    useInput((input, key) => {
        // Navigation
        if (key.upArrow) {
            setSelectedIndex(prev => Math.max(0, prev - 1));
        }
        else if (key.downArrow) {
            setSelectedIndex(prev => Math.min(sessions.length - 1, prev + 1));
        }
        else if (key.return) {
            // Confirm selection
            if (sessions.length > 0 && selectedIndex < sessions.length) {
                onSelect(sessions[selectedIndex].id);
            }
        }
        else if (key.escape) {
            // Cancel
            onClose();
        }
    });
    const maxVisible = 12;
    const startIndex = Math.max(0, Math.min(selectedIndex - Math.floor(maxVisible / 2), sessions.length - maxVisible));
    const visibleSessions = sessions.slice(startIndex, startIndex + maxVisible);
    return (_jsxs(Box, { flexDirection: "column", borderStyle: "round", borderColor: theme.accent.brand, paddingLeft: 1, paddingRight: 1, paddingTop: 0, paddingBottom: 0, marginTop: 1, marginBottom: 1, width: 80, children: [_jsx(Box, { children: _jsx(Text, { color: theme.accent.brand, bold: true, children: " Saved Sessions " }) }), _jsx(Box, { paddingTop: 0, children: _jsx(Text, { color: theme.fg.dim, children: "Enter to resume \u00B7 Esc to close" }) }), _jsx(Box, { paddingTop: 0, children: _jsx(Text, { color: theme.fg.dim, children: '─'.repeat(74) }) }), _jsx(Box, { flexDirection: "column", paddingTop: 0, paddingBottom: 0, children: sessions.length === 0 ? (_jsx(Text, { color: theme.fg.muted, children: " No saved sessions yet" })) : (visibleSessions.map((session, i) => {
                    const actualIndex = startIndex + i;
                    const isSelected = actualIndex === selectedIndex;
                    const isCurrent = session.id === currentSessionId;
                    const marker = isCurrent ? '● ' : '  ';
                    // Truncate title to fit
                    const title = session.title.replace(/\n/g, ' ').trim().substring(0, 68);
                    return (_jsx(Box, { children: isSelected ? (_jsxs(Text, { color: theme.accent.brand, bold: true, inverse: true, children: [' ', marker, title, ' '] })) : (_jsxs(Text, { color: isCurrent ? theme.fg.primary : theme.fg.secondary, children: [' ', marker, title] })) }, session.id));
                })) }), _jsx(Box, { paddingTop: 0, children: _jsxs(Text, { color: theme.fg.dim, children: [sessions.length, " saved ", sessions.length === 1 ? 'session' : 'sessions'] }) })] }));
};
//# sourceMappingURL=SessionSelectModal.js.map
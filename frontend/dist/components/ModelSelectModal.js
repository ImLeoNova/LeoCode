import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState, useEffect } from 'react';
import { Box, Text, useInput } from 'ink';
import { theme } from '../styles/theme.js';
/**
 * ModelSelectModal - Real model picker modal
 *
 * Features:
 * - Live search/filter (substring match, case-insensitive)
 * - Scrollable list with Up/Down navigation
 * - Current model highlighted with ●
 * - Enter to confirm, Esc to cancel
 *
 * Styled consistently with PermissionDialog (bordered overlay).
 */
export const ModelSelectModal = ({ models, currentModel, onSelect, onClose, }) => {
    const [filter, setFilter] = useState('');
    const [selectedIndex, setSelectedIndex] = useState(0);
    // Filter models based on search query
    const filteredModels = filter.trim()
        ? models.filter(m => m.toLowerCase().includes(filter.toLowerCase()))
        : models;
    // Auto-select current model on mount
    useEffect(() => {
        const currentIndex = filteredModels.findIndex(m => m === currentModel);
        if (currentIndex >= 0) {
            setSelectedIndex(currentIndex);
        }
    }, []);
    // Keep selection in bounds when filter changes
    useEffect(() => {
        if (selectedIndex >= filteredModels.length && filteredModels.length > 0) {
            setSelectedIndex(filteredModels.length - 1);
        }
    }, [filteredModels.length, selectedIndex]);
    useInput((input, key) => {
        // Navigation
        if (key.upArrow) {
            setSelectedIndex(prev => Math.max(0, prev - 1));
        }
        else if (key.downArrow) {
            setSelectedIndex(prev => Math.min(filteredModels.length - 1, prev + 1));
        }
        else if (key.return) {
            // Confirm selection
            if (filteredModels.length > 0 && selectedIndex < filteredModels.length) {
                onSelect(filteredModels[selectedIndex]);
            }
        }
        else if (key.escape) {
            // Cancel
            onClose();
        }
        else if (key.backspace || key.delete) {
            // Handle backspace in filter
            setFilter(prev => prev.slice(0, -1));
            setSelectedIndex(0);
        }
        else if (input && !key.ctrl && !key.meta) {
            // Append to filter (printable characters only)
            if (input.length === 1 && input.charCodeAt(0) >= 32) {
                setFilter(prev => prev + input);
                setSelectedIndex(0);
            }
        }
    });
    const maxVisible = 12;
    const startIndex = Math.max(0, Math.min(selectedIndex - Math.floor(maxVisible / 2), filteredModels.length - maxVisible));
    const visibleModels = filteredModels.slice(startIndex, startIndex + maxVisible);
    return (_jsxs(Box, { flexDirection: "column", borderStyle: "round", borderColor: theme.accent.brand, paddingLeft: 1, paddingRight: 1, paddingTop: 0, paddingBottom: 0, marginTop: 1, marginBottom: 1, width: 80, children: [_jsx(Box, { children: _jsx(Text, { color: theme.accent.brand, bold: true, children: " Select Model " }) }), _jsx(Box, { paddingTop: 0, children: _jsx(Text, { color: theme.fg.dim, children: "Type to filter \u00B7 Enter to choose \u00B7 Esc to cancel" }) }), _jsxs(Box, { paddingTop: 0, children: [_jsx(Text, { color: theme.fg.muted, children: "Search: " }), _jsx(Text, { color: theme.fg.primary, children: filter }), _jsx(Text, { color: theme.status.processing, children: "\u258A" })] }), _jsx(Box, { paddingTop: 0, children: _jsx(Text, { color: theme.fg.dim, children: '─'.repeat(74) }) }), _jsx(Box, { flexDirection: "column", paddingTop: 0, paddingBottom: 0, children: filteredModels.length === 0 ? (_jsx(Text, { color: theme.fg.muted, children: " No models match your search" })) : (visibleModels.map((model, i) => {
                    const actualIndex = startIndex + i;
                    const isSelected = actualIndex === selectedIndex;
                    const isCurrent = model === currentModel;
                    const marker = isCurrent ? '● ' : '  ';
                    return (_jsx(Box, { children: isSelected ? (_jsxs(Text, { color: theme.accent.brand, bold: true, inverse: true, children: [' ', marker, model, ' '] })) : (_jsxs(Text, { color: isCurrent ? theme.fg.primary : theme.fg.secondary, children: [' ', marker, model] })) }, model));
                })) }), _jsx(Box, { paddingTop: 0, children: _jsxs(Text, { color: theme.fg.dim, children: [filteredModels.length, " ", filteredModels.length === 1 ? 'model' : 'models', filter && ` (filtered from ${models.length})`] }) })] }));
};
//# sourceMappingURL=ModelSelectModal.js.map
import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useRef, useMemo } from 'react';
import { Box, Text } from 'ink';
import { theme } from '../styles/theme.js';
import { WorkingIndicator } from './WorkingIndicator.js';
/**
 * Renders a single message in the transcript.
 * Claude Code style: no bubbles, no avatars, terminal-native presentation.
 * User messages: colored ">" prefix + primary text, with horizontal padding
 */
const UserMessage = ({ message }) => {
    return (_jsx(Box, { flexDirection: "column", paddingLeft: 2, paddingRight: 2, marginBottom: 1, children: _jsxs(Box, { children: [_jsx(Text, { color: theme.accent.brand, bold: true, children: '> ' }), _jsx(Text, { color: theme.fg.primary, children: message.content })] }) }));
};
/**
 * Strips <thinking>...</thinking> tags and their content from assistant text.
 */
function stripThinkingTags(text) {
    return text.replace(/<thinking>[\s\S]*?<\/thinking>/g, '').trim();
}
/**
 * Assistant messages: no prefix, indented slightly, muted color for softer visual weight
 */
const AssistantMessage = ({ message }) => {
    const content = stripThinkingTags(message.content || '');
    const isStreaming = message.streaming;
    return (_jsxs(Box, { flexDirection: "column", paddingLeft: 2, paddingRight: 2, marginBottom: 1, children: [_jsx(Text, { color: theme.fg.secondary, wrap: "wrap", children: content }), isStreaming && _jsx(Text, { color: theme.status.processing, children: "\u258A" })] }));
};
/**
 * Tool use messages: single-line rounded border, subtle/muted color, compact display
 * This is the ONE place where bordered elements are appropriate
 */
const ToolUseMessage = ({ message }) => {
    const toolName = message.toolName || 'tool';
    const state = message.toolState || 'pending';
    const stateIcon = {
        pending: '○',
        running: '◌',
        success: '●',
        error: '●',
    }[state] || '○';
    const stateColor = {
        pending: theme.tool.pending,
        running: theme.tool.running,
        success: theme.tool.success,
        error: theme.tool.error,
    }[state] || theme.tool.pending;
    return (_jsxs(Box, { flexDirection: "column", marginLeft: 2, marginRight: 2, marginTop: 1, marginBottom: 1, borderStyle: "round", borderColor: theme.border.muted, paddingLeft: 1, paddingRight: 1, children: [_jsxs(Box, { children: [_jsxs(Text, { color: stateColor, children: [stateIcon, " "] }), _jsx(Text, { color: theme.fg.muted, bold: true, children: toolName }), message.toolPath && (_jsxs(Text, { color: theme.fg.dim, children: [" ", message.toolPath] }))] }), message.toolInput && (_jsx(Box, { paddingTop: 0, children: _jsx(Text, { color: theme.fg.dim, wrap: "wrap", children: typeof message.toolInput === 'string'
                        ? message.toolInput
                        : JSON.stringify(message.toolInput, null, 2) }) }))] }));
};
/**
 * Tool result messages: indented under the tool call, muted color
 */
const ToolResultMessage = ({ message }) => {
    const state = message.toolState || 'success';
    const stateColor = state === 'error' ? theme.tool.error : theme.tool.success;
    return (_jsx(Box, { flexDirection: "column", paddingLeft: 4, paddingRight: 2, marginBottom: 1, children: _jsx(Text, { color: theme.fg.dim, wrap: "wrap", children: message.content }) }));
};
/**
 * Diff messages: indented, colored by diff type
 */
const DiffMessage = ({ message }) => {
    const lines = (message.content || '').split('\n');
    return (_jsx(Box, { flexDirection: "column", paddingLeft: 2, paddingRight: 2, marginBottom: 1, children: lines.map((line, i) => {
            if (line.startsWith('+') && !line.startsWith('+++')) {
                return (_jsx(Text, { color: theme.diff.addedText, wrap: "wrap", children: line }, i));
            }
            else if (line.startsWith('-') && !line.startsWith('---')) {
                return (_jsx(Text, { color: theme.diff.removedText, wrap: "wrap", children: line }, i));
            }
            else if (line.startsWith('@@')) {
                return (_jsx(Text, { color: theme.status.info, wrap: "wrap", children: line }, i));
            }
            else if (line.startsWith('diff') || line.startsWith('index') || line.startsWith('---') || line.startsWith('+++')) {
                return (_jsx(Text, { color: theme.fg.muted, wrap: "wrap", children: line }, i));
            }
            return (_jsx(Text, { color: theme.fg.secondary, wrap: "wrap", children: line }, i));
        }) }));
};
/**
 * System messages: muted, italic, indented
 */
const SystemMessage = ({ message }) => {
    return (_jsx(Box, { paddingLeft: 2, paddingRight: 2, marginBottom: 1, children: _jsx(Text, { color: theme.fg.muted, italic: true, children: message.content }) }));
};
/**
 * ThinkingBlock - Displays real reasoning/thinking content from the model.
 * Styled distinct from the final answer: dimmed, italic, gray text.
 * Added proper spacing around it.
 */
const ThinkingBlock = ({ content }) => {
    if (!content)
        return null;
    const lines = content.split('\n');
    return (_jsxs(Box, { flexDirection: "column", paddingLeft: 2, paddingRight: 2, marginTop: 1, marginBottom: 1, children: [_jsx(Text, { color: theme.fg.dim, bold: true, italic: true, children: "thinking" }), lines.map((line, i) => (_jsx(Text, { color: theme.fg.muted, italic: true, wrap: "wrap", children: line || ' ' }, i)))] }));
};
export const MessageList = ({ messages, terminalHeight, isThinking, thinkingContent, waitingForResponse, }) => {
    const scrollRef = useRef(null);
    // Calculate available height for messages
    // Reserve: status bar (1) + help bar (1) + input (min 3)
    const reservedLines = 5;
    const availableHeight = Math.max(terminalHeight - reservedLines, 5);
    // Virtual scrolling: only render visible messages + overscan
    const visibleMessages = useMemo(() => {
        return messages;
    }, [messages]);
    // Determine what to show in the thinking/loading area
    const hasAssistantContent = messages.some(m => m.role === 'assistant');
    // Show WorkingIndicator when waiting for response (before any thinking content arrives)
    const showWorkingIndicator = (waitingForResponse || isThinking) && !thinkingContent && !hasAssistantContent;
    // Show ThinkingBlock when real thinking content is streaming (distinct from the animated phrase)
    const showThinkingBlock = thinkingContent.length > 0 && !hasAssistantContent;
    return (_jsxs(Box, { flexDirection: "column", flexGrow: 1, ref: scrollRef, overflow: "hidden", paddingTop: 1, children: [visibleMessages.map((msg, i) => {
                const key = msg.id || `msg-${i}`;
                switch (msg.role) {
                    case 'user':
                        return _jsx(UserMessage, { message: msg }, key);
                    case 'assistant':
                        return _jsx(AssistantMessage, { message: msg }, key);
                    case 'tool_use':
                        return _jsx(ToolUseMessage, { message: msg }, key);
                    case 'tool_result':
                        return _jsx(ToolResultMessage, { message: msg }, key);
                    case 'diff':
                        return _jsx(DiffMessage, { message: msg }, key);
                    case 'system':
                        return _jsx(SystemMessage, { message: msg }, key);
                    default:
                        return _jsx(SystemMessage, { message: msg }, key);
                }
            }), showWorkingIndicator && (_jsx(Box, { paddingLeft: 2, marginTop: 1, children: _jsx(WorkingIndicator, {}) })), showThinkingBlock && (_jsx(ThinkingBlock, { content: thinkingContent }))] }));
};
//# sourceMappingURL=MessageList.js.map
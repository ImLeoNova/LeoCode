import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState, useCallback, useEffect, useRef } from 'react';
import { Box, useStdout, useInput } from 'ink';
import { AGENT_IDLE, AGENT_THINKING, AGENT_STREAMING } from '../lib/constants.js';
import { PersistentHeader } from './PersistentHeader.js';
import { MessageList } from './MessageList.js';
import { PromptInput } from './PromptInput.js';
import { StatusBar } from './StatusBar.js';
import { HelpBar } from './HelpBar.js';
import { PermissionDialog } from './PermissionDialog.js';
import { SlashMenu } from './SlashMenu.js';
import { ModelSelectModal } from './ModelSelectModal.js';
import { SessionSelectModal } from './SessionSelectModal.js';
import { WelcomeScreen } from './WelcomeScreen.js';
import { getIPC } from '../lib/ipc.js';
const DEBUG_LOG = '/tmp/leocode-app-debug.log';
function appDebug(msg) {
    try {
        const fs = require('fs');
        fs.appendFileSync(DEBUG_LOG, `[APP ${new Date().toISOString()}] ${msg}\n`);
    }
    catch (_) { }
}
/**
 * App - Root component for LeoCode TUI
 *
 * Claude Code-style layout:
 * ┌────────────────────────────────────┐
 * │ StatusBar (model, tokens, cost)    │
 * ├────────────────────────────────────┤
 * │ MessageList (scrollable)           │
 * ├────────────────────────────────────┤
 * │ [SlashMenu] (when active)          │
 * │ PromptInput                        │
 * ├────────────────────────────────────┤
 * │ HelpBar (shortcuts)                │
 * └────────────────────────────────────┘
 */
export const App = () => {
    const { stdout } = useStdout();
    // State
    const [messages, setMessages] = useState([]);
    const [agentState, setAgentState] = useState({
        status: AGENT_IDLE,
        model: '...',
        sessionId: '',
        tokensUsed: 0,
        costAccumulated: 0,
        isStreaming: false,
        mode: 'code',
    });
    const [inputDisabled, setInputDisabled] = useState(false);
    const [permissionRequest, setPermissionRequest] = useState(null);
    const [slashFilter, setSlashFilter] = useState('');
    const [showSlashMenu, setShowSlashMenu] = useState(false);
    const [dimensions, setDimensions] = useState({ columns: 120, rows: 40 });
    const [connected, setConnected] = useState(false);
    const [thinkingContent, setThinkingContent] = useState('');
    const [waitingForResponse, setWaitingForResponse] = useState(false);
    const [showModelModal, setShowModelModal] = useState(false);
    const [availableModels, setAvailableModels] = useState([]);
    const [showSessionModal, setShowSessionModal] = useState(false);
    const [availableSessions, setAvailableSessions] = useState([]);
    // Current streaming message accumulator
    const streamAccum = useRef('');
    appDebug(`Render: messages=${messages.length} connected=${connected} waitingForResponse=${waitingForResponse} agentStatus=${agentState.status}`);
    // Get terminal dimensions
    useEffect(() => {
        if (stdout.columns && stdout.rows) {
            setDimensions({ columns: stdout.columns, rows: stdout.rows });
        }
        const handleResize = () => {
            setDimensions({ columns: stdout.columns || 120, rows: stdout.rows || 40 });
        };
        stdout.on('resize', handleResize);
        return () => { stdout.off('resize', handleResize); };
    }, [stdout]);
    // Connect to IPC backend
    useEffect(() => {
        const ipc = getIPC();
        appDebug('Setting up IPC listeners');
        // Ready event - backend is initialized
        const onReady = (params) => {
            appDebug(`IPC ready: model=${params.model}`);
            setConnected(true);
            setAgentState(prev => ({
                ...prev,
                model: params.model || prev.model,
                mode: params.mode || 'code',
            }));
        };
        // Thinking indicator
        const onThinking = () => {
            appDebug('IPC thinking');
            setAgentState(prev => ({
                ...prev,
                status: AGENT_THINKING,
                isStreaming: true,
            }));
        };
        // Streaming thinking content from <thinking> tags
        const onThinkingStream = (params) => {
            const content = params.content || '';
            appDebug(`IPC thinking_stream: len=${content.length} done=${params.done}`);
            setThinkingContent(content);
            if (content.length > 0) {
                setAgentState(prev => {
                    if (prev.status === AGENT_THINKING) {
                        return { ...prev, status: AGENT_STREAMING };
                    }
                    return prev;
                });
            }
        };
        // Streaming text chunks
        const onAssistantStream = (params) => {
            const chunk = params.content || '';
            appDebug(`IPC assistant_stream: chunk_len=${chunk.length} total_len=${streamAccum.current.length + chunk.length}`);
            streamAccum.current += chunk;
            setMessages(prev => {
                const msgs = [...prev];
                const lastMsg = msgs[msgs.length - 1];
                if (lastMsg && lastMsg.role === 'assistant' && lastMsg.streaming) {
                    msgs[msgs.length - 1] = {
                        ...lastMsg,
                        content: streamAccum.current,
                    };
                }
                else {
                    msgs.push({
                        role: 'assistant',
                        content: streamAccum.current,
                        streaming: true,
                        timestamp: Date.now(),
                    });
                }
                return msgs;
            });
        };
        // Final assistant message
        const onAssistantMessage = (params) => {
            const content = params.content || '';
            const thinking = params.thinking || '';
            appDebug(`IPC assistant_message: content_len=${content.length} thinking_len=${thinking.length}`);
            streamAccum.current = '';
            if (thinking) {
                setThinkingContent(thinking);
            }
            setMessages(prev => {
                const msgs = [...prev];
                const lastMsg = msgs[msgs.length - 1];
                if (lastMsg && lastMsg.role === 'assistant' && lastMsg.streaming) {
                    msgs[msgs.length - 1] = {
                        ...lastMsg,
                        content,
                        streaming: false,
                        thinking: thinking || undefined,
                    };
                }
                else {
                    msgs.push({
                        role: 'assistant',
                        content,
                        streaming: false,
                        thinking: thinking || undefined,
                        timestamp: Date.now(),
                    });
                }
                return msgs;
            });
            setAgentState(prev => ({
                ...prev,
                status: AGENT_IDLE,
                isStreaming: false,
            }));
            setWaitingForResponse(false);
            appDebug('IPC assistant_message: waitingForResponse set to false');
        };
        // Tool use event
        const onToolUse = (params) => {
            appDebug(`IPC tool_use: ${params.name}`);
            setMessages(prev => [...prev, {
                    role: 'tool_use',
                    content: `${params.name}`,
                    toolName: params.name,
                    toolState: 'running',
                    toolPath: params.input?.path || params.input?.file_path || '',
                    toolInput: params.input,
                    timestamp: Date.now(),
                }]);
        };
        // Tool result event
        const onToolResult = (params) => {
            appDebug(`IPC tool_result: ${params.name} state=${params.state}`);
            setMessages(prev => [...prev, {
                    role: 'tool_result',
                    content: params.result || '',
                    toolName: params.name,
                    toolState: (params.state || 'success'),
                    timestamp: Date.now(),
                }]);
        };
        // Agent state changes
        const onAgentStateChanged = (params) => {
            appDebug(`IPC agent_state_changed: status=${params.status} isStreaming=${params.isStreaming} mode=${params.mode}`);
            setAgentState(prev => ({
                ...prev,
                status: params.status || prev.status,
                isStreaming: params.isStreaming ?? prev.isStreaming,
                mode: params.mode || prev.mode,
            }));
        };
        // Permission requests
        const onPermissionRequested = (params) => {
            appDebug(`IPC permission_requested: ${params.tool_name}`);
            setPermissionRequest({
                id: params.id,
                toolName: params.tool_name,
                description: params.description,
                params: params.params,
                risk: params.risk || 'medium',
            });
            setInputDisabled(true);
        };
        // Errors
        const onError = (params) => {
            appDebug(`IPC error: ${params.message}`);
            setMessages(prev => [...prev, {
                    role: 'system',
                    content: `Error: ${params.message}`,
                    timestamp: Date.now(),
                }]);
            setAgentState(prev => ({
                ...prev,
                status: AGENT_IDLE,
                isStreaming: false,
            }));
            setInputDisabled(false);
            setWaitingForResponse(false);
        };
        ipc.on('ready', onReady);
        ipc.on('thinking', onThinking);
        ipc.on('thinking_stream', onThinkingStream);
        ipc.on('assistant_stream', onAssistantStream);
        ipc.on('assistant_message', onAssistantMessage);
        ipc.on('tool_use', onToolUse);
        ipc.on('tool_result', onToolResult);
        ipc.on('agent_state_changed', onAgentStateChanged);
        ipc.on('permission_requested', onPermissionRequested);
        ipc.on('error', onError);
        return () => {
            ipc.off('ready', onReady);
            ipc.off('thinking', onThinking);
            ipc.off('thinking_stream', onThinkingStream);
            ipc.off('assistant_stream', onAssistantStream);
            ipc.off('assistant_message', onAssistantMessage);
            ipc.off('tool_use', onToolUse);
            ipc.off('tool_result', onToolResult);
            ipc.off('agent_state_changed', onAgentStateChanged);
            ipc.off('permission_requested', onPermissionRequested);
            ipc.off('error', onError);
        };
    }, []);
    // Handle live input changes for slash menu
    const handleInputChange = useCallback((text) => {
        // Detect slash command prefix: starts with "/" and no space yet
        if (text.startsWith('/') && !text.includes(' ')) {
            const filter = text.slice(1); // Remove leading "/"
            setSlashFilter(filter);
            setShowSlashMenu(true);
        }
        else if (showSlashMenu) {
            setShowSlashMenu(false);
            setSlashFilter('');
        }
    }, [showSlashMenu]);
    // Handle user input
    const handleSubmit = useCallback((text) => {
        appDebug(`handleSubmit called: text="${text.substring(0, 50)}" showSlashMenu=${showSlashMenu}`);
        if (showSlashMenu) {
            setShowSlashMenu(false);
            setSlashFilter('');
            return;
        }
        // Handle slash commands locally
        if (text.startsWith('/')) {
            handleSlashCommand(text);
            return;
        }
        // Add user message
        const userMsg = {
            role: 'user',
            content: text,
            timestamp: Date.now(),
        };
        appDebug(`Adding user message: "${text.substring(0, 50)}"`);
        setMessages(prev => {
            appDebug(`setMessages callback: prev length=${prev.length}, new length will be=${prev.length + 1}`);
            return [...prev, userMsg];
        });
        // Reset streaming accumulator and thinking content
        streamAccum.current = '';
        setThinkingContent('');
        setWaitingForResponse(true);
        appDebug('waitingForResponse set to true');
        // Send to backend via IPC
        const ipc = getIPC();
        appDebug(`Sending user_message via IPC: connected=${ipc.isConnected}`);
        ipc.notify('user_message', { content: text });
        appDebug('IPC notify called for user_message');
    }, [showSlashMenu]);
    const handleSlashCommand = useCallback((command) => {
        const parts = command.split(' ');
        const cmd = parts[0].toLowerCase();
        const ipc = getIPC();
        switch (cmd) {
            case '/clear':
                setMessages([]);
                setThinkingContent('');
                setWaitingForResponse(false);
                streamAccum.current = '';
                ipc.notify('clear', {});
                break;
            case '/help':
                setMessages(prev => [...prev, {
                        role: 'system',
                        content: [
                            'Keyboard shortcuts:',
                            '  Enter        Send message',
                            '  Shift+Enter  New line',
                            '  Esc          Interrupt',
                            '  Ctrl+C       Clear chat',
                            '  Ctrl+Q       Quit',
                            '  Up/Down      History',
                            '',
                            'Commands:',
                            '  /clear       Clear conversation',
                            '  /help        Show this help',
                            '  /model       Switch model',
                            '  /sessions    Browse sessions',
                            '  /plan        Switch to plan mode',
                            '  /code        Switch to code mode',
                        ].join('\n'),
                        timestamp: Date.now(),
                    }]);
                break;
            case '/model':
                // Open model selection modal
                ipc.send('get_models', {}).then((result) => {
                    const models = result.models || [];
                    if (models.length === 0) {
                        setMessages(prev => [...prev, {
                                role: 'system',
                                content: 'No models available.',
                                timestamp: Date.now(),
                            }]);
                    }
                    else {
                        setAvailableModels(models);
                        setShowModelModal(true);
                        setInputDisabled(true);
                    }
                }).catch((err) => {
                    setMessages(prev => [...prev, {
                            role: 'system',
                            content: `Error fetching models: ${err.message}`,
                            timestamp: Date.now(),
                        }]);
                });
                break;
            case '/sessions':
                // Open session selection modal
                ipc.send('list_sessions', {}).then((result) => {
                    const sessions = result.sessions || [];
                    if (sessions.length === 0) {
                        setMessages(prev => [...prev, {
                                role: 'system',
                                content: 'No saved sessions yet.',
                                timestamp: Date.now(),
                            }]);
                    }
                    else {
                        setAvailableSessions(sessions);
                        setShowSessionModal(true);
                        setInputDisabled(true);
                    }
                }).catch((err) => {
                    setMessages(prev => [...prev, {
                            role: 'system',
                            content: `Error fetching sessions: ${err.message}`,
                            timestamp: Date.now(),
                        }]);
                });
                break;
            case '/plan':
                ipc.notify('toggle_mode', { mode: 'plan' });
                setAgentState(prev => ({ ...prev, mode: 'plan' }));
                setMessages(prev => [...prev, {
                        role: 'system',
                        content: 'Switched to PLAN mode. The agent will focus on planning and design without executing tools.',
                        timestamp: Date.now(),
                    }]);
                break;
            case '/code':
                ipc.notify('toggle_mode', { mode: 'code' });
                setAgentState(prev => ({ ...prev, mode: 'code' }));
                setMessages(prev => [...prev, {
                        role: 'system',
                        content: 'Switched to CODE mode. The agent will execute tools and make changes.',
                        timestamp: Date.now(),
                    }]);
                break;
            case '/config':
                setMessages(prev => [...prev, {
                        role: 'system',
                        content: '/config is not implemented yet.',
                        timestamp: Date.now(),
                    }]);
                break;
            case '/compact':
                if (messages.length === 0) {
                    setMessages(prev => [...prev, {
                            role: 'system',
                            content: 'No messages to compact.',
                            timestamp: Date.now(),
                        }]);
                }
                else {
                    setMessages(prev => [...prev, {
                            role: 'system',
                            content: 'Compacting conversation...',
                            timestamp: Date.now(),
                        }]);
                    ipc.send('compact_conversation', {}).then((result) => {
                        if (result.error) {
                            setMessages(prev => [...prev, {
                                    role: 'system',
                                    content: `Compaction failed: ${result.error}`,
                                    timestamp: Date.now(),
                                }]);
                        }
                        else {
                            // Replace messages with the summary
                            const summary = result.summary || '';
                            setMessages([{
                                    role: 'system',
                                    content: `[Conversation Summary]\n\n${summary}\n\n(${result.message_count} message(s) in backend after compaction)`,
                                    timestamp: Date.now(),
                                }]);
                        }
                    }).catch((err) => {
                        setMessages(prev => [...prev, {
                                role: 'system',
                                content: `Compaction error: ${err.message}`,
                                timestamp: Date.now(),
                            }]);
                    });
                }
                break;
            case '/theme':
                setMessages(prev => [...prev, {
                        role: 'system',
                        content: '/theme is not implemented yet.',
                        timestamp: Date.now(),
                    }]);
                break;
            case '/doctor':
                setMessages(prev => [...prev, {
                        role: 'system',
                        content: '/doctor is not implemented yet.',
                        timestamp: Date.now(),
                    }]);
                break;
            case '/mcp':
                setMessages(prev => [...prev, {
                        role: 'system',
                        content: '/mcp is not implemented yet.',
                        timestamp: Date.now(),
                    }]);
                break;
            default:
                setMessages(prev => [...prev, {
                        role: 'system',
                        content: `Unknown command: ${cmd}`,
                        timestamp: Date.now(),
                    }]);
                break;
        }
    }, []);
    // Keyboard shortcuts
    useInput((input, key) => {
        // Ctrl+Q - quit
        if (key.ctrl && input === 'q') {
            appDebug('Ctrl+Q: emitting SIGTERM to quit');
            process.emit('SIGTERM');
            return;
        }
        // Ctrl+C - clear or interrupt
        if (key.ctrl && input === 'c') {
            if (agentState.status !== AGENT_IDLE) {
                appDebug('Ctrl+C: interrupting');
                const ipc = getIPC();
                ipc.notify('interrupt', {});
                setAgentState(prev => ({
                    ...prev,
                    status: AGENT_IDLE,
                    isStreaming: false,
                }));
                setThinkingContent('');
                setWaitingForResponse(false);
            }
            else {
                appDebug('Ctrl+C: clearing');
                setMessages([]);
                setThinkingContent('');
                setWaitingForResponse(false);
                streamAccum.current = '';
                const ipc = getIPC();
                ipc.notify('clear', {});
            }
        }
        // Escape - interrupt
        if (key.escape && !showSlashMenu) {
            if (agentState.status !== AGENT_IDLE) {
                appDebug('Escape: interrupting');
                const ipc = getIPC();
                ipc.notify('interrupt', {});
                setAgentState(prev => ({
                    ...prev,
                    status: AGENT_IDLE,
                    isStreaming: false,
                }));
                setThinkingContent('');
            }
        }
    });
    return (_jsxs(Box, { flexDirection: "column", width: "100%", height: "100%", children: [_jsx(StatusBar, { agentState: agentState, columns: dimensions.columns }), _jsx(PersistentHeader, {}), _jsxs(Box, { flexDirection: "column", flexGrow: 1, children: [_jsx(Box, { flexShrink: 0, width: "100%", alignItems: "center", children: _jsx(WelcomeScreen, { columns: dimensions.columns }) }), _jsx(Box, { flexDirection: "column", flexGrow: 1, overflow: "hidden", children: _jsx(MessageList, { messages: messages, terminalHeight: dimensions.rows, isThinking: agentState.status === AGENT_THINKING, thinkingContent: thinkingContent, waitingForResponse: waitingForResponse }) })] }), showSessionModal && (_jsx(SessionSelectModal, { sessions: availableSessions, currentSessionId: agentState.sessionId, onSelect: (sessionId) => {
                    const ipc = getIPC();
                    ipc.send('load_session', { session_id: sessionId }).then((result) => {
                        if (result.error) {
                            setMessages(prev => [...prev, {
                                    role: 'system',
                                    content: `Error loading session: ${result.error}`,
                                    timestamp: Date.now(),
                                }]);
                        }
                        else {
                            // Replace current messages with loaded session
                            const loadedMessages = result.messages || [];
                            setMessages(loadedMessages.map((msg) => ({
                                ...msg,
                                timestamp: msg.timestamp || Date.now(),
                            })));
                            setMessages(prev => [...prev, {
                                    role: 'system',
                                    content: `Loaded session: ${result.title || sessionId}`,
                                    timestamp: Date.now(),
                                }]);
                        }
                        setShowSessionModal(false);
                        setInputDisabled(false);
                    }).catch((err) => {
                        setMessages(prev => [...prev, {
                                role: 'system',
                                content: `Failed to load session: ${err.message}`,
                                timestamp: Date.now(),
                            }]);
                        setShowSessionModal(false);
                        setInputDisabled(false);
                    });
                }, onClose: () => {
                    setShowSessionModal(false);
                    setInputDisabled(false);
                } })), showModelModal && (_jsx(ModelSelectModal, { models: availableModels, currentModel: agentState.model, onSelect: (model) => {
                    const ipc = getIPC();
                    ipc.notify('switch_model', { model });
                    setAgentState(prev => ({ ...prev, model }));
                    setShowModelModal(false);
                    setInputDisabled(false);
                    setMessages(prev => [...prev, {
                            role: 'system',
                            content: `Switched to model: ${model}`,
                            timestamp: Date.now(),
                        }]);
                }, onClose: () => {
                    setShowModelModal(false);
                    setInputDisabled(false);
                } })), permissionRequest && (_jsx(PermissionDialog, { request: permissionRequest, onAllow: () => {
                    const ipc = getIPC();
                    ipc.notify('permission_response', { id: permissionRequest.id, action: 'allow' });
                    setPermissionRequest(null);
                    setInputDisabled(false);
                }, onDeny: () => {
                    const ipc = getIPC();
                    ipc.notify('permission_response', { id: permissionRequest.id, action: 'deny' });
                    setPermissionRequest(null);
                    setInputDisabled(false);
                }, onAlwaysAllow: () => {
                    const ipc = getIPC();
                    ipc.notify('permission_response', { id: permissionRequest.id, action: 'always_allow' });
                    setPermissionRequest(null);
                    setInputDisabled(false);
                } })), showSlashMenu && (_jsx(SlashMenu, { filter: slashFilter, onSelect: (cmd) => {
                    setShowSlashMenu(false);
                    setSlashFilter('');
                    handleSubmit(cmd);
                }, onClose: () => {
                    setShowSlashMenu(false);
                    setSlashFilter('');
                } })), _jsx(PromptInput, { onSubmit: handleSubmit, onChange: handleInputChange, isDisabled: inputDisabled || showModelModal || showSessionModal, placeholder: "", slashMenuActive: showSlashMenu }), _jsx(HelpBar, { columns: dimensions.columns })] }));
};
//# sourceMappingURL=App.js.map
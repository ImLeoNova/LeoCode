#!/usr/bin/env node
import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
/**
 * LeoCode Demo - Shows different UI states for visual testing
 * Run with: npx tsx src/demo.tsx
 */
import React, { useState, useEffect } from 'react';
import { Box, Text, useInput, useStdout } from 'ink';
import { theme } from './styles/theme.js';
import { WelcomeScreen } from './components/WelcomeScreen.js';
import { MessageList } from './components/MessageList.js';
import { PromptInput } from './components/PromptInput.js';
import { StatusBar } from './components/StatusBar.js';
import { HelpBar } from './components/HelpBar.js';
import { PermissionDialog } from './components/PermissionDialog.js';
import { SlashMenu } from './components/SlashMenu.js';
import { render } from 'ink';
const DEMO_MESSAGES = [
    {
        role: 'user',
        content: 'Read the main.py file and explain what it does',
        timestamp: Date.now(),
    },
    {
        role: 'tool_use',
        content: 'Read main.py',
        toolName: 'read_file',
        toolState: 'success',
        toolPath: 'main.py',
        timestamp: Date.now(),
    },
    {
        role: 'tool_result',
        content: `  1 │ #!/usr/bin/env python3
  2 │ """LeoCode - AI Coding Agent"""
  3 │
  4 │ import asyncio
  5 │ from leocode.agent import Agent
  6 │ from leocode.config import Config
  7 │
  8 │
  9 │ def main():
 10 │     config = Config.load()
 11 │     agent = Agent(config)
 12 │     asyncio.run(agent.run())
 13 │
 14 │
 14 │ if __name__ == "__main__":
 15 │     main()`,
        toolState: 'success',
        timestamp: Date.now(),
    },
    {
        role: 'assistant',
        content: `This is the main entry point for LeoCode. Here's what it does:

1. **Imports** the Agent class and Config from the leocode package
2. **Loads configuration** from the user's config file
3. **Creates an Agent instance** with that configuration
4. **Runs the agent** asynchronously

The agent handles the main loop: receiving user input, calling the LLM, executing tools, and rendering the terminal UI.`,
        timestamp: Date.now(),
    },
    {
        role: 'user',
        content: 'Now edit the file to add a version check',
        timestamp: Date.now(),
    },
    {
        role: 'tool_use',
        content: 'Edit main.py',
        toolName: 'edit_file',
        toolState: 'running',
        toolPath: 'main.py',
        toolInput: { old: 'def main():', new: 'def main():\n    print(f"LeoCode v{__version__}")' },
        timestamp: Date.now(),
    },
];
const DEMO_PERMISSION = {
    id: 'perm-1',
    toolName: 'shell_command',
    description: 'Run npm install in the project directory',
    params: { command: 'npm install' },
    risk: 'medium',
};
function DemoApp() {
    const [state, setState] = useState(0);
    const { stdout } = useStdout();
    const [dims, setDims] = useState({ columns: stdout.columns || 120, rows: stdout.rows || 40 });
    useEffect(() => {
        const handleResize = () => {
            setDims({ columns: stdout.columns || 120, rows: stdout.rows || 40 });
        };
        stdout.on('resize', handleResize);
        return () => { stdout.off('resize', handleResize); };
    }, [stdout]);
    const [messages, setMessages] = useState([]);
    const [showPermission, setShowPermission] = useState(false);
    const [showSlash, setShowSlash] = useState(false);
    const [agentState, setAgentState] = useState({
        status: 'idle',
        model: 'claude-sonnet-4-20250514',
        sessionId: 'demo',
        tokensUsed: 1234,
        costAccumulated: 0.0234,
        isStreaming: false,
    });
    useInput((input, key) => {
        if (key.tab) {
            setState(prev => (prev + 1) % 5);
            setMessages([]);
            setShowPermission(false);
            setShowSlash(false);
        }
    });
    // Simulate different states
    useEffect(() => {
        if (state === 1) {
            // Show messages
            setMessages(DEMO_MESSAGES.slice(0, 3));
        }
        else if (state === 2) {
            // Show full conversation
            setMessages(DEMO_MESSAGES);
        }
        else if (state === 3) {
            // Show working indicator with a user message
            setMessages([{ role: 'user', content: 'Explain this codebase', timestamp: Date.now() }]);
        }
        else if (state === 4) {
            // Show slash menu
            setMessages([]);
            setShowSlash(true);
        }
    }, [state]);
    const stateLabels = ['Welcome', 'Messages', 'Full Chat', 'Working', 'Slash Menu'];
    return (_jsxs(Box, { flexDirection: "column", width: "100%", height: "100%", children: [_jsx(StatusBar, { agentState: agentState, columns: dims.columns }), _jsx(Box, { flexDirection: "column", flexGrow: 1, overflow: "hidden", children: state === 0 ? (_jsx(WelcomeScreen, { columns: dims.columns })) : (_jsx(MessageList, { messages: messages, terminalHeight: dims.rows, isThinking: state === 2, thinkingContent: "", waitingForResponse: state === 3 })) }), showPermission && (_jsx(PermissionDialog, { request: DEMO_PERMISSION, onAllow: () => setShowPermission(false), onDeny: () => setShowPermission(false), onAlwaysAllow: () => setShowPermission(false) })), showSlash && (_jsx(SlashMenu, { filter: "/", onSelect: () => setShowSlash(false), onClose: () => setShowSlash(false) })), _jsx(PromptInput, { onSubmit: (text) => {
                    setMessages(prev => [...prev, { role: 'user', content: text, timestamp: Date.now() }]);
                }, placeholder: state === 0 ? 'Type a message...' : '' }), _jsx(HelpBar, { columns: dims.columns }), _jsx(Box, { paddingLeft: 1, children: _jsxs(Text, { color: theme.fg.dim, children: ["Tab: next state (", stateLabels[(state + 1) % 5], ") | Current: ", stateLabels[state]] }) })] }));
}
const { waitUntilExit } = render(React.createElement(DemoApp), { exitOnCtrlC: true });
waitUntilExit().then(() => process.exit(0));
//# sourceMappingURL=demo.js.map
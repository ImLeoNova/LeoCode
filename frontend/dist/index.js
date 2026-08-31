#!/usr/bin/env node
/**
 * LeoCode - AI Coding Assistant
 * Terminal UI Frontend
 *
 * High-fidelity reimplementation of Claude Code's terminal experience,
 * branded as LeoCode.
 */
import React from 'react';
import { render } from 'ink';
import { App } from './components/App.js';
const { unmount, waitUntilExit } = render(React.createElement(App), {
    exitOnCtrlC: false,
});
// Handle process signals
process.on('SIGINT', () => {
    unmount();
    process.exit(0);
});
process.on('SIGTERM', () => {
    unmount();
    process.exit(0);
});
// Handle uncaught errors gracefully
process.on('uncaughtException', (err) => {
    console.error('LeoCode error:', err.message);
    unmount();
    process.exit(1);
});
waitUntilExit().then(() => {
    process.exit(0);
});
//# sourceMappingURL=index.js.map
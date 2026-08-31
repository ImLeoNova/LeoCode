import React from 'react';
import { AgentState } from '../lib/types.js';
interface StatusBarProps {
    agentState: AgentState;
    columns: number;
}
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
export declare const StatusBar: React.FC<StatusBarProps>;
export {};
//# sourceMappingURL=StatusBar.d.ts.map
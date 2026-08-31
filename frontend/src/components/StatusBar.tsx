import React from 'react';
import { Box, Text } from 'ink';
import { theme } from '../styles/theme.js';
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
export const StatusBar: React.FC<StatusBarProps> = ({ agentState, columns }) => {
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

  return (
    <Box
      flexDirection="row"
      justifyContent="space-between"
      paddingLeft={2}
      paddingRight={2}
      paddingTop={0}
      paddingBottom={0}
      flexShrink={0}
    >
      <Box>
        <Text color={theme.fg.muted}>{model}</Text>
        <Text color={theme.fg.dim}> · </Text>
        <Text color={mode === 'plan' ? theme.status.warning : theme.status.success}>
          {mode.toUpperCase()}
        </Text>
      </Box>

      <Box>
        {tokenStr && (
          <Text color={theme.fg.dim}>
            {tokenStr} tokens
          </Text>
        )}
        {tokenStr && costStr && (
          <Text color={theme.fg.dim}> · </Text>
        )}
        {costStr && (
          <Text color={theme.fg.dim}>
            {costStr}
          </Text>
        )}
      </Box>
    </Box>
  );
};

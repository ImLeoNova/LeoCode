import React from 'react';
import { Box, Text } from 'ink';
import { theme } from '../styles/theme.js';
import { APP_NAME, APP_VERSION } from '../lib/constants.js';

/**
 * CompactHeader - Persistent branding header for active sessions
 * 
 * Claude Code style: minimal, single-line branding with the hint message
 * Always visible at the top, never disappears once chat starts
 */
export const CompactHeader: React.FC = () => {
  return (
    <Box flexDirection="column" paddingLeft={2} paddingTop={1} paddingBottom={1}>
      <Box>
        <Text color={theme.accent.brand} bold>{APP_NAME}</Text>
        <Text color={theme.fg.dim}> v{APP_VERSION}</Text>
      </Box>
      <Box marginTop={1}>
        <Text color={theme.fg.dim}>
          Type a message to start, or use{' '}
          <Text color={theme.fg.muted}>/help</Text>
          {' '}for commands.
        </Text>
      </Box>
    </Box>
  );
};

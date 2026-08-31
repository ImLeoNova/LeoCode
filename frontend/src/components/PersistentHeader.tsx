import React from 'react';
import { Box, Text } from 'ink';
import { theme } from '../styles/theme.js';
import { APP_NAME, APP_VERSION } from '../lib/constants.js';

/**
 * PersistentHeader - ALWAYS visible header with branding and hint
 * 
 * This component is NEVER unmounted or conditionally hidden.
 * It appears at the top of every screen state: idle, chatting, streaming, etc.
 * No props control its visibility - it's permanently rendered.
 */
export const PersistentHeader: React.FC = () => {
  return (
    <Box flexDirection="column" paddingLeft={2} paddingTop={1} paddingBottom={1} flexShrink={0}>
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

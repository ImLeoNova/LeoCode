import React from 'react';
import { Box, Text } from 'ink';
import { theme } from '../styles/theme.js';

/**
 * HelpBar - Bottom help bar showing keyboard shortcuts
 * Claude Code style: compact, single line, minimal
 * With proper left/right padding so nothing touches the terminal edges
 */
export const HelpBar: React.FC<{ columns?: number }> = ({ columns = 120 }) => {
  return (
    <Box
      flexDirection="row"
      justifyContent="center"
      paddingLeft={2}
      paddingRight={2}
      paddingTop={0}
      paddingBottom={0}
      flexShrink={0}
    >
      <Text color={theme.fg.dim}>
        <Text color={theme.fg.muted}>Enter</Text> send · <Text color={theme.fg.muted}>Shift+Enter</Text> newline · <Text color={theme.fg.muted}>Esc</Text> interrupt · <Text color={theme.fg.muted}>Ctrl+Q</Text> quit · <Text color={theme.fg.muted}>/help</Text> commands
      </Text>
    </Box>
  );
};

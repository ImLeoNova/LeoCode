import React from 'react';
import { Box, Text } from 'ink';
import { theme } from '../styles/theme.js';
import { APP_NAME, APP_VERSION } from '../lib/constants.js';

const ASCII_LOGO_MIN_WIDTH = 64;

// Keep this as ONE multi-line string, not an array of separate lines.
// Ink measures a single Text node's width using the widest embedded line
// (see the `widest-line` dependency), which is what lets Box's
// alignItems="center" center the whole block correctly as one unit.
// Splitting it into multiple <Text> elements makes each line wrap/measure
// independently, which is what was breaking the shape.
const ASCII_LOGO = [
  '██╗     ███████╗ ██████╗  ██████╗ ██████╗ ██████╗ ███████╗',
  '██║     ██╔════╝██╔═══██╗██╔════╝██╔═══██╗██╔══██╗██╔════╝',
  '██║     █████╗  ██║   ██║██║     ██║   ██║██║  ██║█████╗  ',
  '██║     ██╔══╝  ██║   ██║██║     ██║   ██║██║  ██║██╔══╝  ',
  '███████╗███████╗╚██████╔╝╚██████╗╚██████╔╝██████╔╝███████╗',
  '╚══════╝╚══════╝ ╚═════╝  ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝',
].join('\n');

/**
 * WelcomeScreen - Full welcome banner (shown only on initial idle state)
 * Claude Code style: centered, spacious, low contrast
 */
export const WelcomeScreen: React.FC<{ columns?: number }> = ({ columns = 120 }) => {
  const showWideLogo = columns >= ASCII_LOGO_MIN_WIDTH;

  return (
    <Box flexDirection="column" width="100%" paddingTop={2} paddingBottom={1}>
      <Box flexDirection="column" width="100%" alignItems="center">
        {showWideLogo ? (
          // wrap="truncate-end" is critical here: without it, Ink's default
          // wrap="wrap" can reflow the block-drawing characters the moment
          // available width is even 1 column short of 60, which staircases
          // the whole logo. truncate-end just clips instead of reflowing.
          <Text color={theme.accent.brand} bold wrap="truncate-end">
            {ASCII_LOGO}
          </Text>
        ) : (
          <Text color={theme.accent.brand} bold>
            {APP_NAME} v{APP_VERSION}
          </Text>
        )}
      </Box>

      <Box marginTop={1} flexDirection="column" width="100%" alignItems="center">
        <Text color={theme.fg.dim}>
          v{APP_VERSION}
        </Text>
      </Box>

      <Box marginTop={2} flexDirection="column" width="100%" alignItems="center">
        <Text color={theme.fg.dim}>
          {'─'.repeat(50)}
        </Text>
      </Box>

      <Box marginTop={2} flexDirection="column" width="100%" alignItems="center">
        <Text color={theme.fg.secondary}>
          Type a message to start, or use{' '}
          <Text color={theme.accent.brand} bold>/help</Text>
          {' '}for commands.
        </Text>
      </Box>

      <Box marginTop={2} flexDirection="column" width="100%" alignItems="center">
        <Text color={theme.fg.dim}>
          Ctrl+<Text color={theme.fg.muted}>N</Text> new chat · Ctrl+<Text color={theme.fg.muted}>M</Text> model · Ctrl+<Text color={theme.fg.muted}>P</Text> commands · Ctrl+<Text color={theme.fg.muted}>Q</Text> quit · <Text color={theme.fg.muted}>Esc</Text> interrupt
        </Text>
      </Box>
    </Box>
  );
};
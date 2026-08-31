import React, { useState, useMemo } from 'react';
import { Box, Text, useInput } from 'ink';
import { theme } from '../styles/theme.js';
import { SLASH_COMMANDS } from '../lib/constants.js';

interface SlashMenuProps {
  filter: string;
  onSelect: (command: string) => void;
  onClose: () => void;
}

/**
 * SlashMenu - Claude Code-style autocomplete for slash commands
 *
 * Appears above the input when "/" is typed.
 * Compact rows, keyboard navigation, highlighted match.
 */
export const SlashMenu: React.FC<SlashMenuProps> = ({
  filter,
  onSelect,
  onClose,
}) => {
  const [selectedIndex, setSelectedIndex] = useState(0);

  const filtered = useMemo(() => {
    if (!filter) return SLASH_COMMANDS;
    const lower = filter.toLowerCase();
    return SLASH_COMMANDS.filter(
      cmd => cmd.name.toLowerCase().includes(lower) ||
             cmd.description.toLowerCase().includes(lower)
    );
  }, [filter]);

  // Reset selection when filter changes
  React.useEffect(() => {
    setSelectedIndex(0);
  }, [filter]);

  useInput((input, key) => {
    if (key.upArrow) {
      setSelectedIndex(prev => Math.max(0, prev - 1));
    } else if (key.downArrow) {
      setSelectedIndex(prev => Math.min(filtered.length - 1, prev + 1));
    } else if (key.return) {
      if (filtered[selectedIndex]) {
        onSelect(filtered[selectedIndex].name);
      }
    } else if (key.escape) {
      onClose();
    } else if (key.tab) {
      if (filtered[selectedIndex]) {
        onSelect(filtered[selectedIndex].name);
      }
    }
  });

  if (filtered.length === 0) return null;

  return (
    <Box
      flexDirection="column"
      borderStyle="round"
      borderColor={theme.border.default}
      paddingLeft={0}
      paddingRight={0}
      paddingTop={0}
      paddingBottom={0}
      marginBottom={0}
    >
      {filtered.map((cmd, i) => {
        const isSelected = i === selectedIndex;
        const matchStart = cmd.name.toLowerCase().indexOf(filter.toLowerCase());
        const matchEnd = matchStart + filter.length;

        return (
          <Box key={cmd.name} paddingLeft={1} paddingRight={1}>
            {isSelected ? (
              <Text color={theme.accent.primary} bold>
                {'▶ '}
              </Text>
            ) : (
              <Text color={theme.fg.dim}>
                {'  '}
              </Text>
            )}
            <Text color={isSelected ? theme.fg.bright : theme.fg.secondary}>
              {cmd.name}
            </Text>
            <Text color={theme.fg.dim}>
              {'  '}{cmd.description}
            </Text>
          </Box>
        );
      })}
    </Box>
  );
};

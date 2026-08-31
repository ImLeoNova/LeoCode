import React, { useState, useEffect } from 'react';
import { Box, Text, useInput } from 'ink';
import { theme } from '../styles/theme.js';

interface Model {
  id: string;
  name: string;
}

interface ModelSelectModalProps {
  models: string[];
  currentModel: string;
  onSelect: (model: string) => void;
  onClose: () => void;
}

/**
 * ModelSelectModal - Real model picker modal
 * 
 * Features:
 * - Live search/filter (substring match, case-insensitive)
 * - Scrollable list with Up/Down navigation
 * - Current model highlighted with ●
 * - Enter to confirm, Esc to cancel
 * 
 * Styled consistently with PermissionDialog (bordered overlay).
 */
export const ModelSelectModal: React.FC<ModelSelectModalProps> = ({
  models,
  currentModel,
  onSelect,
  onClose,
}) => {
  const [filter, setFilter] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);

  // Filter models based on search query
  const filteredModels = filter.trim()
    ? models.filter(m => m.toLowerCase().includes(filter.toLowerCase()))
    : models;

  // Auto-select current model on mount
  useEffect(() => {
    const currentIndex = filteredModels.findIndex(m => m === currentModel);
    if (currentIndex >= 0) {
      setSelectedIndex(currentIndex);
    }
  }, []);

  // Keep selection in bounds when filter changes
  useEffect(() => {
    if (selectedIndex >= filteredModels.length && filteredModels.length > 0) {
      setSelectedIndex(filteredModels.length - 1);
    }
  }, [filteredModels.length, selectedIndex]);

  useInput((input, key) => {
    // Navigation
    if (key.upArrow) {
      setSelectedIndex(prev => Math.max(0, prev - 1));
    } else if (key.downArrow) {
      setSelectedIndex(prev => Math.min(filteredModels.length - 1, prev + 1));
    } else if (key.return) {
      // Confirm selection
      if (filteredModels.length > 0 && selectedIndex < filteredModels.length) {
        onSelect(filteredModels[selectedIndex]);
      }
    } else if (key.escape) {
      // Cancel
      onClose();
    } else if (key.backspace || key.delete) {
      // Handle backspace in filter
      setFilter(prev => prev.slice(0, -1));
      setSelectedIndex(0);
    } else if (input && !key.ctrl && !key.meta) {
      // Append to filter (printable characters only)
      if (input.length === 1 && input.charCodeAt(0) >= 32) {
        setFilter(prev => prev + input);
        setSelectedIndex(0);
      }
    }
  });

  const maxVisible = 12;
  const startIndex = Math.max(0, Math.min(selectedIndex - Math.floor(maxVisible / 2), filteredModels.length - maxVisible));
  const visibleModels = filteredModels.slice(startIndex, startIndex + maxVisible);

  return (
    <Box
      flexDirection="column"
      borderStyle="round"
      borderColor={theme.accent.brand}
      paddingLeft={1}
      paddingRight={1}
      paddingTop={0}
      paddingBottom={0}
      marginTop={1}
      marginBottom={1}
      width={80}
    >
      {/* Title */}
      <Box>
        <Text color={theme.accent.brand} bold> Select Model </Text>
      </Box>

      {/* Subtitle */}
      <Box paddingTop={0}>
        <Text color={theme.fg.dim}>
          Type to filter · Enter to choose · Esc to cancel
        </Text>
      </Box>

      {/* Search input */}
      <Box paddingTop={0}>
        <Text color={theme.fg.muted}>Search: </Text>
        <Text color={theme.fg.primary}>{filter}</Text>
        <Text color={theme.status.processing}>▊</Text>
      </Box>

      {/* Divider */}
      <Box paddingTop={0}>
        <Text color={theme.fg.dim}>{'─'.repeat(74)}</Text>
      </Box>

      {/* Model list */}
      <Box flexDirection="column" paddingTop={0} paddingBottom={0}>
        {filteredModels.length === 0 ? (
          <Text color={theme.fg.muted}> No models match your search</Text>
        ) : (
          visibleModels.map((model, i) => {
            const actualIndex = startIndex + i;
            const isSelected = actualIndex === selectedIndex;
            const isCurrent = model === currentModel;
            const marker = isCurrent ? '● ' : '  ';

            return (
              <Box key={model}>
                {isSelected ? (
                  <Text color={theme.accent.brand} bold inverse>
                    {' '}{marker}{model}{' '}
                  </Text>
                ) : (
                  <Text color={isCurrent ? theme.fg.primary : theme.fg.secondary}>
                    {' '}{marker}{model}
                  </Text>
                )}
              </Box>
            );
          })
        )}
      </Box>

      {/* Footer with count */}
      <Box paddingTop={0}>
        <Text color={theme.fg.dim}>
          {filteredModels.length} {filteredModels.length === 1 ? 'model' : 'models'}
          {filter && ` (filtered from ${models.length})`}
        </Text>
      </Box>
    </Box>
  );
};

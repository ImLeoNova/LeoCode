import React, { useState, useEffect } from 'react';
import { Box, Text, useInput } from 'ink';
import { theme } from '../styles/theme.js';

interface Session {
  id: string;
  title: string;
  timestamp: string;
}

interface SessionSelectModalProps {
  sessions: Session[];
  currentSessionId?: string;
  onSelect: (sessionId: string) => void;
  onClose: () => void;
}

/**
 * SessionSelectModal - Real session picker modal
 * 
 * Features:
 * - Scrollable list with Up/Down navigation
 * - Current session highlighted with ●
 * - Enter to resume, Esc to cancel
 * 
 * Styled consistently with ModelSelectModal and PermissionDialog.
 */
export const SessionSelectModal: React.FC<SessionSelectModalProps> = ({
  sessions,
  currentSessionId = '',
  onSelect,
  onClose,
}) => {
  const [selectedIndex, setSelectedIndex] = useState(0);

  // Auto-select current session on mount
  useEffect(() => {
    const currentIndex = sessions.findIndex(s => s.id === currentSessionId);
    if (currentIndex >= 0) {
      setSelectedIndex(currentIndex);
    }
  }, []);

  useInput((input, key) => {
    // Navigation
    if (key.upArrow) {
      setSelectedIndex(prev => Math.max(0, prev - 1));
    } else if (key.downArrow) {
      setSelectedIndex(prev => Math.min(sessions.length - 1, prev + 1));
    } else if (key.return) {
      // Confirm selection
      if (sessions.length > 0 && selectedIndex < sessions.length) {
        onSelect(sessions[selectedIndex].id);
      }
    } else if (key.escape) {
      // Cancel
      onClose();
    }
  });

  const maxVisible = 12;
  const startIndex = Math.max(0, Math.min(selectedIndex - Math.floor(maxVisible / 2), sessions.length - maxVisible));
  const visibleSessions = sessions.slice(startIndex, startIndex + maxVisible);

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
        <Text color={theme.accent.brand} bold> Saved Sessions </Text>
      </Box>

      {/* Subtitle */}
      <Box paddingTop={0}>
        <Text color={theme.fg.dim}>
          Enter to resume · Esc to close
        </Text>
      </Box>

      {/* Divider */}
      <Box paddingTop={0}>
        <Text color={theme.fg.dim}>{'─'.repeat(74)}</Text>
      </Box>

      {/* Session list */}
      <Box flexDirection="column" paddingTop={0} paddingBottom={0}>
        {sessions.length === 0 ? (
          <Text color={theme.fg.muted}> No saved sessions yet</Text>
        ) : (
          visibleSessions.map((session, i) => {
            const actualIndex = startIndex + i;
            const isSelected = actualIndex === selectedIndex;
            const isCurrent = session.id === currentSessionId;
            const marker = isCurrent ? '● ' : '  ';
            
            // Truncate title to fit
            const title = session.title.replace(/\n/g, ' ').trim().substring(0, 68);

            return (
              <Box key={session.id}>
                {isSelected ? (
                  <Text color={theme.accent.brand} bold inverse>
                    {' '}{marker}{title}{' '}
                  </Text>
                ) : (
                  <Text color={isCurrent ? theme.fg.primary : theme.fg.secondary}>
                    {' '}{marker}{title}
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
          {sessions.length} saved {sessions.length === 1 ? 'session' : 'sessions'}
        </Text>
      </Box>
    </Box>
  );
};

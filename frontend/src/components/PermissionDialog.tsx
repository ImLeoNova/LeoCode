import React, { useState } from 'react';
import { Box, Text, useInput } from 'ink';
import { theme } from '../styles/theme.js';
import { PermissionRequest } from '../lib/types.js';

interface PermissionDialogProps {
  request: PermissionRequest;
  onAllow: () => void;
  onDeny: () => void;
  onAlwaysAllow: () => void;
}

/**
 * PermissionDialog - Claude Code-style permission prompt
 *
 * Shows what tool is being requested, parameters, and choices.
 * Keyboard-driven: Left/Right to select, Enter to confirm.
 */
export const PermissionDialog: React.FC<PermissionDialogProps> = ({
  request,
  onAllow,
  onDeny,
  onAlwaysAllow,
}) => {
  const [selectedIndex, setSelectedIndex] = useState(0);

  const choices = [
    { label: 'Allow', key: 'allow', action: onAllow, color: theme.permission.allow },
    { label: 'Deny', key: 'deny', action: onDeny, color: theme.permission.deny },
    { label: 'Always Allow', key: 'always', action: onAlwaysAllow, color: theme.permission.warning },
  ];

  useInput((input, key) => {
    if (key.leftArrow) {
      setSelectedIndex(prev => Math.max(0, prev - 1));
    } else if (key.rightArrow) {
      setSelectedIndex(prev => Math.min(choices.length - 1, prev + 1));
    } else if (key.return) {
      choices[selectedIndex].action();
    } else if (input === 'y' || input === 'Y') {
      onAllow();
    } else if (input === 'n' || input === 'N') {
      onDeny();
    } else if (input === 'a' || input === 'A') {
      onAlwaysAllow();
    }
  });

  const riskColor = {
    safe: theme.status.success,
    low: theme.status.info,
    medium: theme.status.warning,
    high: theme.status.error,
    critical: theme.status.error,
  }[request.risk] || theme.status.warning;

  return (
    <Box
      flexDirection="column"
      borderStyle="round"
      borderColor={riskColor}
      paddingLeft={1}
      paddingRight={1}
      paddingTop={0}
      paddingBottom={0}
      marginTop={1}
      marginBottom={1}
    >
      <Box>
        <Text color={riskColor} bold> ⚠ Permission Required </Text>
      </Box>

      <Box flexDirection="column" paddingTop={0}>
        <Text color={theme.fg.primary}>
          Tool: <Text bold>{request.toolName}</Text>
        </Text>
        <Text color={theme.fg.secondary}>
          {request.description}
        </Text>
        {request.params && (
          <Text color={theme.fg.dim}>
            {typeof request.params === 'string'
              ? request.params
              : JSON.stringify(request.params)}
          </Text>
        )}
      </Box>

      <Box paddingTop={0}>
        {choices.map((choice, i) => (
          <Text key={choice.key}>
            {i === selectedIndex ? (
              <Text color={choice.color} bold inverse> {choice.label} </Text>
            ) : (
              <Text color={theme.fg.muted}> {choice.label} </Text>
            )}
            {'  '}
          </Text>
        ))}
      </Box>

      <Box>
        <Text color={theme.fg.dim}>
          Press <Text color={theme.fg.muted}>Y</Text> allow,{' '}
          <Text color={theme.fg.muted}>N</Text> deny,{' '}
          <Text color={theme.fg.muted}>A</Text> always allow
        </Text>
      </Box>
    </Box>
  );
};

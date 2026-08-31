import React, { useState, useRef, useCallback, useEffect } from 'react';
import { Box, Text, useInput, useStdin } from 'ink';
import { theme } from '../styles/theme.js';

interface PromptInputProps {
  onSubmit: (text: string) => void;
  onChange?: (text: string) => void;
  isDisabled?: boolean;
  placeholder?: string;
  slashMenuActive?: boolean;
}

/**
 * PromptInput - Claude Code-style input composer
 *
 * Reproduces Claude Code's input behavior:
 * - Bottom-anchored
 * - Prompt marker ">" on the left
 * - Multiline support (Shift+Enter for newline)
 * - Autocomplete for slash commands
 * - Cursor movement with arrow keys
 * - History navigation with Up/Down
 */
export const PromptInput: React.FC<PromptInputProps> = ({
  onSubmit,
  onChange,
  isDisabled = false,
  placeholder = '',
  slashMenuActive = false,
}) => {
  const [value, setValue] = useState('');
  const [cursorPos, setCursorPos] = useState(0);
  const [history, setHistory] = useState<string[]>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  const [isMultiline, setIsMultiline] = useState(false);

  const lines = value.split('\n');
  const currentLine = lines[lines.length - 1];
  const lineCount = lines.length;

  useInput((input, key) => {
    if (isDisabled) return;

    // Enter - submit (unless shift is held for multiline)
    // If slash menu is active, let it handle Enter instead
    if (key.return && !key.shift) {
      if (slashMenuActive) return; // Let SlashMenu handle it
      if (value.trim()) {
        onSubmit(value);
        setHistory(prev => [...prev, value]);
        setValue('');
        setCursorPos(0);
        setHistoryIndex(-1);
      }
      return;
    }

    // Backspace - handle both BS (\x08) and DEL (\x7f)
    // Most modern terminals send DEL (\x7f) for backspace, which Ink maps to key.delete
    // Ink's parse-keypress: \b -> key.backspace, \x7f -> key.delete
    // For non-alphanumeric keys, input is set to '' by use-input.js, so we check key properties only
    if (key.backspace || key.delete) {
      if (cursorPos > 0) {
        const before = value.slice(0, cursorPos - 1);
        const after = value.slice(cursorPos);
        const newValue = before + after;
        setValue(newValue);
        setCursorPos(cursorPos - 1);
        if (onChange) {
          onChange(newValue);
        }
      } else if (lines.length > 1) {
        const prevLine = lines[lines.length - 2];
        const newLines = lines.slice(0, -1);
        const newContent = newLines.join('\n');
        setValue(newContent);
        setCursorPos(prevLine.length);
        if (onChange) {
          onChange(newContent);
        }
      }
      return;
    }

    // Delete key (forward delete) - escape sequence \x1b[3~
    // Note: key.delete also matches backspace on some terminals (\x7f),
    // so we specifically check for the escape sequence here
    if (input === '\x1b[3~' || input === '\x1b[3n') {
      if (cursorPos < value.length) {
        const before = value.slice(0, cursorPos);
        const after = value.slice(cursorPos + 1);
        setValue(before + after);
      }
      return;
    }

    // Arrow keys
    if (key.upArrow) {
      if (slashMenuActive) return; // Let SlashMenu handle it
      if (history.length > 0 && historyIndex < history.length - 1) {
        const newIndex = historyIndex + 1;
        setHistoryIndex(newIndex);
        const cmd = history[history.length - 1 - newIndex];
        setValue(cmd);
        setCursorPos(cmd.length);
      }
      return;
    }

    if (key.downArrow) {
      if (slashMenuActive) return; // Let SlashMenu handle it
      if (historyIndex > 0) {
        const newIndex = historyIndex - 1;
        setHistoryIndex(newIndex);
        const cmd = history[history.length - 1 - newIndex];
        setValue(cmd);
        setCursorPos(cmd.length);
      } else if (historyIndex === 0) {
        setHistoryIndex(-1);
        setValue('');
        setCursorPos(0);
      }
      return;
    }

    if (key.leftArrow) {
      if (cursorPos > 0) setCursorPos(cursorPos - 1);
      return;
    }

    if (key.rightArrow) {
      if (cursorPos < value.length) setCursorPos(cursorPos + 1);
      return;
    }

    // Home/End via Ctrl+A/Ctrl+E
    if (key.ctrl && input === 'a') {
      // Go to start of current line
      const lineStart = value.lastIndexOf('\n', cursorPos - 1) + 1;
      setCursorPos(lineStart);
      return;
    }

    if (key.ctrl && input === 'e') {
      // Go to end of current line
      const lineEnd = value.indexOf('\n', cursorPos);
      setCursorPos(lineEnd === -1 ? value.length : lineEnd);
      return;
    }

    // Ctrl+U - clear line
    if (key.ctrl && input === 'u') {
      const lineStart = value.lastIndexOf('\n', cursorPos - 1) + 1;
      const before = value.slice(0, lineStart);
      const after = value.slice(cursorPos);
      const newValue = before + after;
      setValue(newValue);
      setCursorPos(lineStart);
      if (onChange) {
        onChange(newValue);
      }
      return;
    }

    // Ctrl+C - handled by parent
    if (key.ctrl && input === 'c') {
      return;
    }

    // Ctrl+D - exit (handled by parent)
    if (key.ctrl && input === 'd') {
      return;
    }

    // Regular character input
    if (input && !key.ctrl && !key.meta) {
      const before = value.slice(0, cursorPos);
      const after = value.slice(cursorPos);
      const newValue = before + input + after;
      setValue(newValue);
      setCursorPos(cursorPos + input.length);
      if (onChange) {
        onChange(newValue);
      }
    }
  });

  // Build the display with cursor
  const renderInput = () => {
    if (isDisabled) {
      return (
        <Text color={theme.fg.muted}>
          {placeholder || '(waiting...)'}
        </Text>
      );
    }

    if (!value && !isDisabled) {
      return (
        <Text color={theme.fg.dim}>
          {placeholder || ''}
        </Text>
      );
    }

    // Show text with cursor indicator
    const beforeCursor = value.slice(0, cursorPos);
    const atCursor = value[cursorPos] || ' ';
    const afterCursor = value.slice(cursorPos + 1);

    return (
      <Text>
        <Text color={theme.fg.primary}>{beforeCursor}</Text>
        <Text color={theme.bg.default} backgroundColor={theme.fg.primary}>{atCursor}</Text>
        <Text color={theme.fg.primary}>{afterCursor}</Text>
      </Text>
    );
  };

  return (
    <Box
      flexDirection="row"
      borderStyle="single"
      borderColor={theme.border.default}
      paddingTop={0}
      paddingBottom={0}
      paddingLeft={1}
      paddingRight={1}
      marginTop={1}
      flexShrink={0}
    >
      <Text color={theme.accent.brand} bold>{'> '}</Text>
      <Box flexDirection="column" flexGrow={1}>
        {renderInput()}
      </Box>
    </Box>
  );
};

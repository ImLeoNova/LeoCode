import React, { useRef, useMemo } from 'react';
import { Box, Text } from 'ink';
import { theme } from '../styles/theme.js';
import { Message } from '../lib/types.js';
import { WorkingIndicator } from './WorkingIndicator.js';

/**
 * Renders a single message in the transcript.
 * Claude Code style: no bubbles, no avatars, terminal-native presentation.
 * User messages: colored ">" prefix + primary text, with horizontal padding
 */
const UserMessage: React.FC<{ message: Message }> = ({ message }) => {
  return (
    <Box flexDirection="column" paddingLeft={2} paddingRight={2} marginBottom={1}>
      <Box>
        <Text color={theme.accent.brand} bold>{'> '}</Text>
        <Text color={theme.fg.primary}>{message.content}</Text>
      </Box>
    </Box>
  );
};

/**
 * Strips <thinking>...</thinking> tags and their content from assistant text.
 */
function stripThinkingTags(text: string): string {
  return text.replace(/<thinking>[\s\S]*?<\/thinking>/g, '').trim();
}

/**
 * Assistant messages: no prefix, indented slightly, muted color for softer visual weight
 */
const AssistantMessage: React.FC<{ message: Message }> = ({ message }) => {
  const content = stripThinkingTags(message.content || '');
  const isStreaming = message.streaming;

  return (
    <Box flexDirection="column" paddingLeft={2} paddingRight={2} marginBottom={1}>
      <Text color={theme.fg.secondary} wrap="wrap">
        {content}
      </Text>
      {isStreaming && <Text color={theme.status.processing}>▊</Text>}
    </Box>
  );
};

/**
 * Tool use messages: single-line rounded border, subtle/muted color, compact display
 * This is the ONE place where bordered elements are appropriate
 */
const ToolUseMessage: React.FC<{ message: Message }> = ({ message }) => {
  const toolName = message.toolName || 'tool';
  const state = message.toolState || 'pending';

  const stateIcon = {
    pending: '○',
    running: '◌',
    success: '●',
    error: '●',
  }[state] || '○';

  const stateColor = {
    pending: theme.tool.pending,
    running: theme.tool.running,
    success: theme.tool.success,
    error: theme.tool.error,
  }[state] || theme.tool.pending;

  return (
    <Box flexDirection="column" marginLeft={2} marginRight={2} marginTop={1} marginBottom={1} borderStyle="round" borderColor={theme.border.muted} paddingLeft={1} paddingRight={1}>
      <Box>
        <Text color={stateColor}>{stateIcon} </Text>
        <Text color={theme.fg.muted} bold>{toolName}</Text>
        {message.toolPath && (
          <Text color={theme.fg.dim}> {message.toolPath}</Text>
        )}
      </Box>
      {message.toolInput && (
        <Box paddingTop={0}>
          <Text color={theme.fg.dim} wrap="wrap">
            {typeof message.toolInput === 'string'
              ? message.toolInput
              : JSON.stringify(message.toolInput, null, 2)}
          </Text>
        </Box>
      )}
    </Box>
  );
};

/**
 * Tool result messages: indented under the tool call, muted color
 */
const ToolResultMessage: React.FC<{ message: Message }> = ({ message }) => {
  const state = message.toolState || 'success';
  const stateColor = state === 'error' ? theme.tool.error : theme.tool.success;

  return (
    <Box flexDirection="column" paddingLeft={4} paddingRight={2} marginBottom={1}>
      <Text color={theme.fg.dim} wrap="wrap">
        {message.content}
      </Text>
    </Box>
  );
};

/**
 * Diff messages: indented, colored by diff type
 */
const DiffMessage: React.FC<{ message: Message }> = ({ message }) => {
  const lines = (message.content || '').split('\n');

  return (
    <Box flexDirection="column" paddingLeft={2} paddingRight={2} marginBottom={1}>
      {lines.map((line, i) => {
        if (line.startsWith('+') && !line.startsWith('+++')) {
          return (
            <Text key={i} color={theme.diff.addedText} wrap="wrap">
              {line}
            </Text>
          );
        } else if (line.startsWith('-') && !line.startsWith('---')) {
          return (
            <Text key={i} color={theme.diff.removedText} wrap="wrap">
              {line}
            </Text>
          );
        } else if (line.startsWith('@@')) {
          return (
            <Text key={i} color={theme.status.info} wrap="wrap">
              {line}
            </Text>
          );
        } else if (line.startsWith('diff') || line.startsWith('index') || line.startsWith('---') || line.startsWith('+++')) {
          return (
            <Text key={i} color={theme.fg.muted} wrap="wrap">
              {line}
            </Text>
          );
        }
        return (
          <Text key={i} color={theme.fg.secondary} wrap="wrap">
            {line}
          </Text>
        );
      })}
    </Box>
  );
};

/**
 * System messages: muted, italic, indented
 */
const SystemMessage: React.FC<{ message: Message }> = ({ message }) => {
  return (
    <Box paddingLeft={2} paddingRight={2} marginBottom={1}>
      <Text color={theme.fg.muted} italic>
        {message.content}
      </Text>
    </Box>
  );
};

/**
 * ThinkingBlock - Displays real reasoning/thinking content from the model.
 * Styled distinct from the final answer: dimmed, italic, gray text.
 * Added proper spacing around it.
 */
const ThinkingBlock: React.FC<{ content: string }> = ({ content }) => {
  if (!content) return null;

  const lines = content.split('\n');

  return (
    <Box flexDirection="column" paddingLeft={2} paddingRight={2} marginTop={1} marginBottom={1}>
      <Text color={theme.fg.dim} bold italic>
        thinking
      </Text>
      {lines.map((line, i) => (
        <Text key={i} color={theme.fg.muted} italic wrap="wrap">
          {line || ' '}
        </Text>
      ))}
    </Box>
  );
};

/**
 * MessageList - The main transcript component
 * Renders all messages in the conversation.
 * Implements virtual scrolling (only renders visible messages).
 */
interface MessageListProps {
  messages: Message[];
  terminalHeight: number;
  isThinking: boolean;
  thinkingContent: string;
  waitingForResponse: boolean;
}

export const MessageList: React.FC<MessageListProps> = ({
  messages,
  terminalHeight,
  isThinking,
  thinkingContent,
  waitingForResponse,
}) => {
  const scrollRef = useRef<any>(null);

  // Calculate available height for messages
  // Reserve: status bar (1) + help bar (1) + input (min 3)
  const reservedLines = 5;
  const availableHeight = Math.max(terminalHeight - reservedLines, 5);

  // Virtual scrolling: only render visible messages + overscan
  const visibleMessages = useMemo(() => {
    return messages;
  }, [messages]);

  // Determine what to show in the thinking/loading area
  const hasAssistantContent = messages.some(m => m.role === 'assistant');

  // Show WorkingIndicator when waiting for response (before any thinking content arrives)
  const showWorkingIndicator = (waitingForResponse || isThinking) && !thinkingContent && !hasAssistantContent;

  // Show ThinkingBlock when real thinking content is streaming (distinct from the animated phrase)
  const showThinkingBlock = thinkingContent.length > 0 && !hasAssistantContent;

  return (
    <Box
      flexDirection="column"
      flexGrow={1}
      ref={scrollRef}
      overflow="hidden"
      paddingTop={1}
    >
      {visibleMessages.map((msg, i) => {
        const key = msg.id || `msg-${i}`;

        switch (msg.role) {
          case 'user':
            return <UserMessage key={key} message={msg} />;
          case 'assistant':
            return <AssistantMessage key={key} message={msg} />;
          case 'tool_use':
            return <ToolUseMessage key={key} message={msg} />;
          case 'tool_result':
            return <ToolResultMessage key={key} message={msg} />;
          case 'diff':
            return <DiffMessage key={key} message={msg} />;
          case 'system':
            return <SystemMessage key={key} message={msg} />;
          default:
            return <SystemMessage key={key} message={msg} />;
        }
      })}

      {/* Thinking/loading indicator area */}
      {showWorkingIndicator && (
        <Box paddingLeft={2} marginTop={1}>
          <WorkingIndicator />
        </Box>
      )}

      {/* Real thinking content from <thinking> tags */}
      {showThinkingBlock && (
        <ThinkingBlock content={thinkingContent} />
      )}
    </Box>
  );
};

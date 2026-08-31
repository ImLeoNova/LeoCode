import React from 'react';
import { Message } from '../lib/types.js';
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
export declare const MessageList: React.FC<MessageListProps>;
export {};
//# sourceMappingURL=MessageList.d.ts.map
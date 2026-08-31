import React from 'react';
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
export declare const PromptInput: React.FC<PromptInputProps>;
export {};
//# sourceMappingURL=PromptInput.d.ts.map
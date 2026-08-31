import React from 'react';
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
export declare const SlashMenu: React.FC<SlashMenuProps>;
export {};
//# sourceMappingURL=SlashMenu.d.ts.map
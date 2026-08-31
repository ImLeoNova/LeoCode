import React from 'react';
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
export declare const SessionSelectModal: React.FC<SessionSelectModalProps>;
export {};
//# sourceMappingURL=SessionSelectModal.d.ts.map
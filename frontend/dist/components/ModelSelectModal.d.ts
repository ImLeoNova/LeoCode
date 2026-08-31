import React from 'react';
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
export declare const ModelSelectModal: React.FC<ModelSelectModalProps>;
export {};
//# sourceMappingURL=ModelSelectModal.d.ts.map
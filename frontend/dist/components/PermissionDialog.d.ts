import React from 'react';
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
export declare const PermissionDialog: React.FC<PermissionDialogProps>;
export {};
//# sourceMappingURL=PermissionDialog.d.ts.map
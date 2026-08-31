/**
 * LeoCode Backend Bridge
 * Handles communication with the Python backend
 */
import { Message, AgentState, PermissionRequest } from './types.js';
export declare class BackendBridge {
    private ipc;
    private messageHandlers;
    private stateHandlers;
    private permissionHandlers;
    constructor();
    private setupListeners;
    sendMessage(content: string): Promise<void>;
    interrupt(): Promise<void>;
    respondPermission(id: string, action: 'allow' | 'deny' | 'always_allow'): Promise<void>;
    onMessage(handler: (msg: Message) => void): void;
    onStateChange(handler: (state: Partial<AgentState>) => void): void;
    onPermission(handler: (req: PermissionRequest) => void): void;
    getModels(): Promise<string[]>;
    switchModel(model: string): Promise<void>;
    getSessions(): Promise<any[]>;
    loadSession(sessionId: string): Promise<void>;
}
//# sourceMappingURL=backend.d.ts.map
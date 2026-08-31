/**
 * LeoCode Backend Bridge
 * Handles communication with the Python backend
 */

import { IPCClient, getIPC } from './ipc.js';
import { Message, AgentState, PermissionRequest } from './types.js';

export class BackendBridge {
  private ipc: IPCClient;
  private messageHandlers: ((msg: Message) => void)[] = [];
  private stateHandlers: ((state: Partial<AgentState>) => void)[] = [];
  private permissionHandlers: ((req: PermissionRequest) => void)[] = [];

  constructor() {
    this.ipc = getIPC();
    this.setupListeners();
  }

  private setupListeners() {
    // Listen for streaming messages from backend
    this.ipc.on('assistant_message', (params) => {
      const msg: Message = {
        role: 'assistant',
        content: params.content,
        streaming: params.streaming,
        timestamp: Date.now(),
      };
      this.messageHandlers.forEach(h => h(msg));
    });

    // Listen for tool use events
    this.ipc.on('tool_use', (params) => {
      const msg: Message = {
        role: 'tool_use',
        content: params.description || params.name,
        toolName: params.name,
        toolState: params.state || 'running',
        toolPath: params.path,
        toolInput: params.input,
        timestamp: Date.now(),
      };
      this.messageHandlers.forEach(h => h(msg));
    });

    // Listen for tool results
    this.ipc.on('tool_result', (params) => {
      const msg: Message = {
        role: 'tool_result',
        content: params.result,
        toolName: params.name,
        toolState: params.error ? 'error' : 'success',
        timestamp: Date.now(),
      };
      this.messageHandlers.forEach(h => h(msg));
    });

    // Listen for diff events
    this.ipc.on('diff_created', (params) => {
      const msg: Message = {
        role: 'diff',
        content: params.diff,
        timestamp: Date.now(),
      };
      this.messageHandlers.forEach(h => h(msg));
    });

    // Listen for agent state changes
    this.ipc.on('agent_state_changed', (params) => {
      this.stateHandlers.forEach(h => h(params));
    });

    // Listen for permission requests
    this.ipc.on('permission_requested', (params) => {
      const req: PermissionRequest = {
        id: params.id,
        toolName: params.tool_name,
        description: params.description,
        params: params.params,
        risk: params.risk || 'medium',
      };
      this.permissionHandlers.forEach(h => h(req));
    });

    // Listen for thinking indicators
    this.ipc.on('thinking', (params) => {
      this.stateHandlers.forEach(h => h({
        status: 'thinking',
        isStreaming: true,
      }));
    });

    // Listen for errors
    this.ipc.on('error', (params) => {
      const msg: Message = {
        role: 'system',
        content: `Error: ${params.message}`,
        timestamp: Date.now(),
      };
      this.messageHandlers.forEach(h => h(msg));
    });
  }

  // Send user message to backend
  async sendMessage(content: string) {
    await this.ipc.send('user_message', { content });
  }

  // Send interrupt signal
  async interrupt() {
    await this.ipc.notify('interrupt', {});
  }

  // Send permission response
  async respondPermission(id: string, action: 'allow' | 'deny' | 'always_allow') {
    await this.ipc.send('permission_response', { id, action });
  }

  // Register message handler
  onMessage(handler: (msg: Message) => void) {
    this.messageHandlers.push(handler);
  }

  // Register state handler
  onStateChange(handler: (state: Partial<AgentState>) => void) {
    this.stateHandlers.push(handler);
  }

  // Register permission handler
  onPermission(handler: (req: PermissionRequest) => void) {
    this.permissionHandlers.push(handler);
  }

  // Get available models
  async getModels(): Promise<string[]> {
    const result = await this.ipc.send('get_models', {});
    return result?.models || [];
  }

  // Switch model
  async switchModel(model: string) {
    await this.ipc.send('switch_model', { model });
  }

  // Get sessions
  async getSessions(): Promise<any[]> {
    const result = await this.ipc.send('get_sessions', {});
    return result?.sessions || [];
  }

  // Load session
  async loadSession(sessionId: string) {
    await this.ipc.send('load_session', { session_id: sessionId });
  }
}

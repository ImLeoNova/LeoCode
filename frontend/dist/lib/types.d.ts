/**
 * LeoCode Type Definitions
 */
export interface Message {
    id?: string;
    role: 'user' | 'assistant' | 'system' | 'tool_use' | 'tool_result' | 'diff';
    content: string;
    timestamp?: number;
    streaming?: boolean;
    toolName?: string;
    toolState?: 'pending' | 'running' | 'success' | 'error';
    toolPath?: string;
    toolInput?: any;
    toolResult?: any;
    thinking?: boolean;
    thinkingContent?: string;
}
export interface ToolCall {
    id: string;
    name: string;
    input: any;
    state: 'pending' | 'running' | 'success' | 'error';
    result?: any;
    error?: string;
    path?: string;
}
export interface AgentState {
    status: 'idle' | 'thinking' | 'streaming' | 'tool_use' | 'complete' | 'error';
    model: string;
    sessionId: string;
    tokensUsed: number;
    costAccumulated: number;
    isStreaming: boolean;
    mode?: 'code' | 'plan';
    currentTool?: ToolCall;
}
export interface Config {
    model: string;
    temperature: number;
    maxTokens: number;
    apiKey?: string;
    baseUrl?: string;
    theme: string;
    permissionPolicy: 'auto' | 'ask' | 'deny';
}
export interface PermissionRequest {
    id: string;
    toolName: string;
    description: string;
    params: any;
    risk: 'safe' | 'low' | 'medium' | 'high' | 'critical';
}
export interface SlashCommand {
    name: string;
    description: string;
}
//# sourceMappingURL=types.d.ts.map
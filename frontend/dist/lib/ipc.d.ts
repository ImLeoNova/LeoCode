/**
 * LeoCode IPC Client
 * JSON-RPC over Unix socket for communication with Python backend.
 *
 * Key design: messages are queued until the socket is connected.
 * This prevents silent message loss during startup race conditions.
 */
export interface IPCMessage {
    jsonrpc: '2.0';
    id?: number;
    method?: string;
    params?: any;
    result?: any;
    error?: {
        code: number;
        message: string;
        data?: any;
    };
}
export type IPCEventHandler = (params: any) => void;
export declare class IPCClient {
    private messageId;
    private pending;
    private handlers;
    private socket;
    private connected;
    private buffer;
    private messageQueue;
    private onConnectCallbacks;
    private findSocketRetries;
    private static MAX_FIND_RETRIES;
    constructor();
    private connect;
    private findSocket;
    private connectToSocket;
    private flushQueue;
    private processBuffer;
    private handleMessage;
    send(method: string, params?: any): Promise<any>;
    notify(method: string, params?: any): void;
    private writeDirect;
    on(method: string, handler: IPCEventHandler): void;
    off(method: string, handler: IPCEventHandler): void;
    onConnect(callback: () => void): void;
    get isConnected(): boolean;
    close(): void;
}
export declare function getIPC(): IPCClient;
//# sourceMappingURL=ipc.d.ts.map
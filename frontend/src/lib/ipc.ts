/**
 * LeoCode IPC Client
 * JSON-RPC over Unix socket for communication with Python backend.
 *
 * Key design: messages are queued until the socket is connected.
 * This prevents silent message loss during startup race conditions.
 */

import * as net from 'net';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';

const DEBUG_LOG = '/tmp/leocode-ipc-debug.log';

function ipcDebug(msg: string) {
  const line = `[IPC ${new Date().toISOString()}] ${msg}\n`;
  try {
    fs.appendFileSync(DEBUG_LOG, line);
  } catch (_) {}
}

export interface IPCMessage {
  jsonrpc: '2.0';
  id?: number;
  method?: string;
  params?: any;
  result?: any;
  error?: { code: number; message: string; data?: any };
}

export type IPCEventHandler = (params: any) => void;

export class IPCClient {
  private messageId = 0;
  private pending = new Map<number, { resolve: (r: any) => void; reject: (e: Error) => void }>();
  private handlers = new Map<string, IPCEventHandler[]>();
  private socket: net.Socket | null = null;
  private connected = false;
  private buffer = '';
  private messageQueue: IPCMessage[] = [];  // Buffer messages until connected
  private onConnectCallbacks: (() => void)[] = [];
  private findSocketRetries = 0;
  private static MAX_FIND_RETRIES = 50;

  constructor() {
    ipcDebug('IPCClient constructed, starting connection...');
    this.connect();
  }

  private connect() {
    // Find the socket path written by the Python backend
    const pid = process.env.LEOCODE_BACKEND_PID;
    if (!pid) {
      ipcDebug('No LEOCODE_BACKEND_PID env var, falling back to findSocket');
      this.findSocket();
      return;
    }

    const sockPath = path.join(os.tmpdir(), `leocode-${pid}.sock`);
    ipcDebug(`Connecting to socket: ${sockPath} (PID=${pid})`);
    this.connectToSocket(sockPath);
  }

  private findSocket() {
    if (this.findSocketRetries >= IPCClient.MAX_FIND_RETRIES) {
      ipcDebug(`ERROR: Gave up finding socket after ${IPCClient.MAX_FIND_RETRIES} retries`);
      return;
    }
    this.findSocketRetries++;

    // Look for leocode-*.path files in tmp
    try {
      const tmpDir = os.tmpdir();
      const files = fs.readdirSync(tmpDir);
      const pathFiles = files.filter(f => f.startsWith('leocode-') && f.endsWith('.path'));

      if (pathFiles.length === 0) {
        ipcDebug(`findSocket attempt ${this.findSocketRetries}: no .path files yet, retrying...`);
        setTimeout(() => this.findSocket(), 200);
        return;
      }

      // Rank candidates by mtime (newest first), not by lexicographic filename
      // sort — PIDs don't sort correctly as strings (e.g. "19069" > "18665").
      const candidates = pathFiles
        .map(f => {
          const fullPath = path.join(tmpDir, f);
          let mtimeMs = 0;
          try {
            mtimeMs = fs.statSync(fullPath).mtimeMs;
          } catch (_) {
            // File may have been removed between readdir and stat; skip it.
          }
          return { file: f, fullPath, mtimeMs };
        })
        .sort((a, b) => b.mtimeMs - a.mtimeMs);

      // Walk from newest to oldest, skipping entries whose socket file no
      // longer exists (a dead/orphaned backend left the .path file behind).
      for (const candidate of candidates) {
        let sockPath: string;
        try {
          sockPath = fs.readFileSync(candidate.fullPath, 'utf-8').trim();
        } catch (_) {
          continue;
        }
        if (!sockPath || !fs.existsSync(sockPath)) {
          ipcDebug(`findSocket skipping stale entry: ${candidate.file} -> ${sockPath || '(empty)'}`);
          continue;
        }
        ipcDebug(`findSocket found: ${candidate.file} -> ${sockPath}`);
        this.connectToSocket(sockPath);
        return;
      }

      ipcDebug(`findSocket attempt ${this.findSocketRetries}: no live sockets among ${pathFiles.length} candidate(s), retrying...`);
      setTimeout(() => this.findSocket(), 200);
    } catch (e) {
      ipcDebug(`findSocket error: ${e}`);
      setTimeout(() => this.findSocket(), 200);
    }
  }

  private connectToSocket(sockPath: string) {
    ipcDebug(`connectToSocket: creating connection to ${sockPath}`);
    this.socket = net.createConnection(sockPath);

    this.socket.on('connect', () => {
      ipcDebug('Socket CONNECTED');
      this.connected = true;
      this.findSocketRetries = 0;

      // Flush any queued messages
      this.flushQueue();

      // Notify callbacks
      for (const cb of this.onConnectCallbacks) {
        try { cb(); } catch (_) {}
      }
    });

    this.socket.on('data', (data: Buffer) => {
      this.buffer += data.toString();
      this.processBuffer();
    });

    this.socket.on('close', () => {
      ipcDebug('Socket CLOSED');
      this.connected = false;
      // Try to reconnect
      setTimeout(() => this.findSocket(), 500);
    });

    this.socket.on('error', (err: Error) => {
      ipcDebug(`Socket ERROR: ${err.message}`);
      if (!this.connected) {
        setTimeout(() => this.findSocket(), 300);
      }
    });
  }

  private flushQueue() {
    if (this.messageQueue.length === 0) return;
    ipcDebug(`Flushing ${this.messageQueue.length} queued messages`);
    const queue = [...this.messageQueue];
    this.messageQueue = [];
    for (const msg of queue) {
      this.writeDirect(msg);
    }
  }

  private processBuffer() {
    const lines = this.buffer.split('\n');
    this.buffer = lines.pop() || '';

    for (const line of lines) {
      if (!line.trim()) continue;
      try {
        const msg: IPCMessage = JSON.parse(line);
        ipcDebug(`IPC RECV: method=${msg.method || '(response)'} id=${msg.id ?? 'none'}`);
        this.handleMessage(msg);
      } catch (e) {
        ipcDebug(`IPC parse error: ${e}`);
      }
    }
  }

  private handleMessage(msg: IPCMessage) {
    // Response to a request we sent
    if (msg.id !== undefined && this.pending.has(msg.id)) {
      const p = this.pending.get(msg.id)!;
      this.pending.delete(msg.id);
      if (msg.error) {
        ipcDebug(`IPC response ERROR for id=${msg.id}: ${msg.error.message}`);
        p.reject(new Error(msg.error.message));
      } else {
        ipcDebug(`IPC response OK for id=${msg.id}`);
        p.resolve(msg.result);
      }
      return;
    }

    // Notification from backend
    if (msg.method) {
      ipcDebug(`IPC notification: method=${msg.method}`);
      const handlers = this.handlers.get(msg.method) || [];
      for (const handler of handlers) {
        handler(msg.params);
      }
      // Wildcard handlers
      const wildcardHandlers = this.handlers.get('*') || [];
      for (const handler of wildcardHandlers) {
        handler({ method: msg.method, params: msg.params });
      }
    }
  }

  send(method: string, params?: any): Promise<any> {
    const id = ++this.messageId;
    ipcDebug(`IPC SEND (request): method=${method} id=${id} connected=${this.connected}`);
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject });
      const msg: IPCMessage = { jsonrpc: '2.0', id, method, params };
      if (this.connected) {
        this.writeDirect(msg);
      } else {
        ipcDebug(`IPC SEND queued (not connected): method=${method} id=${id}`);
        this.messageQueue.push(msg);
      }
    });
  }

  notify(method: string, params?: any) {
    ipcDebug(`IPC NOTIFY: method=${method} connected=${this.connected}`);
    const msg: IPCMessage = { jsonrpc: '2.0', method, params };
    if (this.connected) {
      this.writeDirect(msg);
    } else {
      ipcDebug(`IPC NOTIFY queued (not connected): method=${method}`);
      this.messageQueue.push(msg);
    }
  }

  private writeDirect(msg: IPCMessage) {
    if (!this.socket || !this.connected) {
      ipcDebug(`writeDirect BLOCKED: socket=${!!this.socket} connected=${this.connected}`);
      return;
    }
    try {
      const data = JSON.stringify(msg) + '\n';
      this.socket.write(data);
      ipcDebug(`writeDirect OK: ${msg.method || `response to id=${msg.id}`}`);
    } catch (e) {
      ipcDebug(`writeDirect ERROR: ${e}`);
    }
  }

  on(method: string, handler: IPCEventHandler) {
    if (!this.handlers.has(method)) {
      this.handlers.set(method, []);
    }
    this.handlers.get(method)!.push(handler);
  }

  off(method: string, handler: IPCEventHandler) {
    const handlers = this.handlers.get(method);
    if (handlers) {
      const idx = handlers.indexOf(handler);
      if (idx >= 0) handlers.splice(idx, 1);
    }
  }

  onConnect(callback: () => void) {
    if (this.connected) {
      callback();
    } else {
      this.onConnectCallbacks.push(callback);
    }
  }

  get isConnected() {
    return this.connected;
  }

  close() {
    this.socket?.destroy();
    this.connected = false;
    this.messageQueue = [];
  }
}

let instance: IPCClient | null = null;

export function getIPC(): IPCClient {
  if (!instance) {
    instance = new IPCClient();
  }
  return instance;
}
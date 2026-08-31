"""
LeoCode IPC Server
JSON-RPC over Unix socket for communication between Python backend and TypeScript frontend.
"""

import json
import os
import asyncio
import socket
import tempfile
import logging
from typing import Any, Callable, Optional
from dataclasses import dataclass

DEBUG_LOG = "/tmp/leocode-backend-debug.log"
logger = logging.getLogger("leocode.ipc")


def ipc_debug(msg: str):
    """Write to debug log file."""
    try:
        with open(DEBUG_LOG, "a") as f:
            f.write(f"[IPC-SERVER {__import__('datetime').datetime.now().isoformat()}] {msg}\n")
    except Exception:
        pass


@dataclass
class IPCMessage:
    jsonrpc: str = "2.0"
    id: Optional[int] = None
    method: Optional[str] = None
    params: Optional[dict] = None
    result: Any = None
    error: Optional[dict] = None

    def to_dict(self) -> dict:
        d = {"jsonrpc": self.jsonrpc}
        if self.id is not None:
            d["id"] = self.id
        if self.method is not None:
            d["method"] = self.method
        if self.params is not None:
            d["params"] = self.params
        if self.result is not None:
            d["result"] = self.result
        if self.error is not None:
            d["error"] = self.error
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "IPCMessage":
        return cls(
            jsonrpc=d.get("jsonrpc", "2.0"),
            id=d.get("id"),
            method=d.get("method"),
            params=d.get("params"),
            result=d.get("result"),
            error=d.get("error"),
        )


class IPCServer:
    """
    JSON-RPC server over Unix domain socket.
    The TypeScript frontend connects as a client.
    """

    def __init__(self):
        self.handlers: dict[str, Callable] = {}
        self.socket_path: Optional[str] = None
        self._server: Optional[asyncio.AbstractServer] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._running = False
        self._ready_data: dict = {}  # Data to send on client connect

    def _get_socket_path(self) -> str:
        """Get or create a Unix socket path."""
        if self.socket_path:
            return self.socket_path
        # Use a deterministic path based on PID so the frontend can find it
        self.socket_path = os.path.join(
            tempfile.gettempdir(),
            f"leocode-{os.getpid()}.sock"
        )
        # Clean up old socket
        try:
            os.unlink(self.socket_path)
        except FileNotFoundError:
            pass
        return self.socket_path

    def setup(self):
        """Create socket path file synchronously (call before start())."""
        sock_path = self._get_socket_path()
        path_file = os.path.join(tempfile.gettempdir(), f"leocode-{os.getpid()}.path")
        with open(path_file, "w") as f:
            f.write(sock_path)

    def set_ready(self, data: dict):
        """Set data to send when client connects."""
        self._ready_data = data

    def register(self, method: str, handler: Callable):
        """Register a handler for an RPC method."""
        self.handlers[method] = handler

    async def send(self, method: str, params: Any = None) -> bool:
        """Send a notification to the frontend. Returns True if sent, False if no writer."""
        ipc_debug(f"SEND: method={method} has_writer={self._writer is not None}")
        if not self._writer:
            ipc_debug(f"SEND BLOCKED: no writer for method={method}")
            return False
        msg = IPCMessage(method=method, params=params)
        line = json.dumps(msg.to_dict()) + "\n"
        try:
            self._writer.write(line.encode())
            await self._writer.drain()
        except (BrokenPipeError, ConnectionResetError):
            self._writer = None
            return False
        return True

    async def respond(self, msg_id: int, result: Any):
        """Send a response to a request from the frontend."""
        if not self._writer:
            return
        msg = IPCMessage(id=msg_id, result=result)
        line = json.dumps(msg.to_dict()) + "\n"
        try:
            self._writer.write(line.encode())
            await self._writer.drain()
        except (BrokenPipeError, ConnectionResetError):
            pass

    async def respond_error(self, msg_id: int, code: int, message: str, data: Any = None):
        """Send an error response."""
        if not self._writer:
            return
        msg = IPCMessage(
            id=msg_id,
            error={"code": code, "message": message, "data": data},
        )
        line = json.dumps(msg.to_dict()) + "\n"
        try:
            self._writer.write(line.encode())
            await self._writer.drain()
        except (BrokenPipeError, ConnectionResetError):
            pass

    async def start(self):
        """Start listening on Unix socket. Call setup() first."""
        self._running = True
        sock_path = self._get_socket_path()

        self._server = await asyncio.start_unix_server(
            self._handle_client,
            path=sock_path,
        )

        async with self._server:
            await self._server.serve_forever()

    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle a client connection."""
        ipc_debug(f"CLIENT CONNECTED: {writer.get_extra_info('peername')}")
        self._writer = writer
        # Send ready data to newly connected client
        if self._ready_data:
            await self.send("ready", self._ready_data)
        try:
            while self._running:
                line = await reader.readline()
                if not line:
                    break

                line_str = line.decode().strip()
                if not line_str:
                    continue

                try:
                    data = json.loads(line_str)
                    msg = IPCMessage.from_dict(data)
                    await self._handle_message(msg)
                except json.JSONDecodeError:
                    continue
        except (ConnectionResetError, BrokenPipeError):
            pass
        finally:
            self._writer = None
            writer.close()

    async def _handle_message(self, msg: IPCMessage):
        """Handle an incoming message."""
        ipc_debug(f"HANDLE: method={msg.method} id={msg.id} params_keys={list(msg.params.keys()) if msg.params else 'None'}")
        if msg.method and msg.id is not None:
            handler = self.handlers.get(msg.method)
            if handler:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        result = await handler(msg.params or {})
                    else:
                        result = handler(msg.params or {})
                    await self.respond(msg.id, result)
                except Exception as e:
                    await self.respond_error(msg.id, -1, str(e))
            else:
                await self.respond_error(msg.id, -32601, f"Method not found: {msg.method}")

        elif msg.method:
            handler = self.handlers.get(msg.method)
            if handler:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(msg.params or {})
                    else:
                        handler(msg.params or {})
                except Exception:
                    pass

    def stop(self):
        """Stop the server."""
        self._running = False
        if self.socket_path:
            try:
                os.unlink(self.socket_path)
            except FileNotFoundError:
                pass
        path_file = os.path.join(tempfile.gettempdir(), f"leocode-{os.getpid()}.path")
        try:
            os.unlink(path_file)
        except FileNotFoundError:
            pass


_server: Optional[IPCServer] = None


def get_ipc_server() -> IPCServer:
    global _server
    if _server is None:
        _server = IPCServer()
    return _server

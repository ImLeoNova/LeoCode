"""MCP (Model Context Protocol) client for tool integration."""

import json
import asyncio
from typing import Any, Optional
from .config import Config


class MCPTool:
    def __init__(self, name: str, description: str, parameters: dict, server_name: str):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.server_name = server_name

    def to_openai_schema(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class MCPServer:
    def __init__(self, name: str, command: str, args: list[str] | None = None, env: dict | None = None):
        self.name = name
        self.command = command
        self.args = args or []
        self.env = env or {}
        self.process: Optional[asyncio.subprocess.Process] = None
        self.tools: list[MCPTool] = []
        self.connected = False
        self._request_id = 0

    async def connect(self) -> bool:
        try:
            env = {**dict(__import__("os").environ), **self.env}
            self.process = await asyncio.create_subprocess_exec(
                self.command, *self.args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )
            self._request_id = 1
            await self._send_request("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "leocode", "version": "1.0.0"},
            })
            resp = await self._read_response()
            if resp and "result" in resp:
                await self._send_request("notifications/initialized", {})
                await self._discover_tools()
                self.connected = True
                return True
        except Exception:
            pass
        return False

    async def _discover_tools(self):
        try:
            await self._send_request("tools/list", {})
            resp = await self._read_response()
            if resp and "result" in resp:
                for tool in resp["result"].get("tools", []):
                    self.tools.append(MCPTool(
                        name=tool["name"],
                        description=tool.get("description", ""),
                        parameters=tool.get("inputSchema", {"type": "object", "properties": {}}),
                        server_name=self.name,
                    ))
        except Exception:
            pass

    async def call_tool(self, tool_name: str, arguments: dict) -> str:
        try:
            await self._send_request("tools/call", {
                "name": tool_name,
                "arguments": arguments,
            })
            resp = await self._read_response()
            if resp and "result" in resp:
                content = resp["result"].get("content", [])
                parts = []
                for c in content:
                    if c.get("type") == "text":
                        parts.append(c["text"])
                return "\n".join(parts) if parts else json.dumps(resp["result"])
            elif resp and "error" in resp:
                return f"MCP error: {resp['error']}"
        except Exception as e:
            return f"MCP call error: {e}"
        return "No response from MCP server"

    async def _send_request(self, method: str, params: dict):
        if not self.process or not self.process.stdin:
            return
        msg = json.dumps({"jsonrpc": "2.0", "id": self._request_id, "method": method, "params": params})
        self._request_id += 1
        self.process.stdin.write(f"{msg}\n".encode())
        await self.process.stdin.drain()

    async def _read_response(self) -> Optional[dict]:
        if not self.process or not self.process.stdout:
            return None
        try:
            line = await asyncio.wait_for(self.process.stdout.readline(), timeout=10)
            if line:
                return json.loads(line.decode())
        except (asyncio.TimeoutError, json.JSONDecodeError):
            pass
        return None

    async def disconnect(self):
        if self.process:
            try:
                self.process.terminate()
                await asyncio.wait_for(self.process.wait(), timeout=5)
            except Exception:
                try:
                    self.process.kill()
                except Exception:
                    pass
        self.connected = False
        self.tools = []


class MCPManager:
    def __init__(self, config: Config):
        self.config = config
        self.servers: dict[str, MCPServer] = {}

    async def connect_all(self):
        for srv_cfg in self.config.mcp_servers:
            if isinstance(srv_cfg, dict):
                server = MCPServer(
                    name=srv_cfg.get("name", "unknown"),
                    command=srv_cfg.get("command", ""),
                    args=srv_cfg.get("args", []),
                    env=srv_cfg.get("env", {}),
                )
                if await server.connect():
                    self.servers[server.name] = server

    def get_all_tools(self) -> list[MCPTool]:
        tools = []
        for server in self.servers.values():
            tools.extend(server.tools)
        return tools

    def get_openai_tools(self) -> list[dict]:
        return [t.to_openai_schema() for t in self.get_all_tools()]

    async def call_tool(self, full_name: str, arguments: dict) -> str:
        if "/" in full_name:
            server_name, tool_name = full_name.split("/", 1)
        else:
            for server in self.servers.values():
                for tool in server.tools:
                    if tool.name == full_name:
                        server_name = server.name
                        tool_name = full_name
                        break
                else:
                    continue
                break
            else:
                return f"Tool '{full_name}' not found"

        server = self.servers.get(server_name)
        if not server or not server.connected:
            return f"Server '{server_name}' not connected"
        return await server.call_tool(tool_name, arguments)

    async def disconnect_all(self):
        for server in self.servers.values():
            await server.disconnect()
        self.servers.clear()

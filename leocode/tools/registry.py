"""Central Tool Registry — single source of truth for all tools."""

from __future__ import annotations

import logging
from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine, Optional

from ..permissions import RiskLevel

log = logging.getLogger(__name__)


class ToolCategory(str, Enum):
    FILESYSTEM = "filesystem"
    SEARCH = "search"
    EXECUTION = "execution"
    AGENT = "agent"
    WEB = "web"
    CODE_INTEL = "code_intel"
    EXTENSIBILITY = "extensibility"
    MCP = "mcp"
    PLUGIN = "plugin"


class ToolSource(str, Enum):
    BUILTIN = "builtin"
    MCP = "mcp"
    PLUGIN = "plugin"
    CUSTOM = "custom"


@dataclass
class RetryPolicy:
    max_retries: int = 0
    backoff_base: float = 1.0
    backoff_max: float = 30.0


@dataclass
class ToolMetadata:
    id: str
    name: str
    description: str
    category: ToolCategory
    input_schema: dict
    output_schema: dict = field(default_factory=lambda: {"type": "string"})
    risk_level: RiskLevel = RiskLevel.LOW
    timeout: float = 30.0
    retry_policy: RetryPolicy = field(default_factory=RetryPolicy)
    supports_streaming: bool = False
    supports_cancellation: bool = False
    source: ToolSource = ToolSource.BUILTIN
    enabled: bool = True

    def to_openai_schema(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.id,
                "description": self.description,
                "parameters": self.input_schema,
            },
        }


ToolExecutor = Callable[[str, dict[str, Any]], Coroutine[Any, Any, str]]
AsyncToolExecutor = Callable[[str, dict[str, Any]], Coroutine[Any, Any, str]]


class ToolRegistry:
    """Central registry for all tools — built-in, MCP, plugin, custom."""

    def __init__(self):
        self._tools: dict[str, ToolMetadata] = {}
        self._executors: dict[str, ToolExecutor] = {}
        self._categories: dict[ToolCategory, list[str]] = {}

    def register(self, metadata: ToolMetadata, executor: ToolExecutor):
        self._tools[metadata.id] = metadata
        self._executors[metadata.id] = executor
        self._categories.setdefault(metadata.category, []).append(metadata.id)
        log.debug(f"Registered tool: {metadata.id} ({metadata.category.value})")

    def unregister(self, tool_id: str):
        if tool_id in self._tools:
            meta = self._tools.pop(tool_id)
            self._executors.pop(tool_id, None)
            tool_list = self._categories.get(meta.category, [])
            if tool_id in tool_list:
                tool_list.remove(tool_id)

    def resolve(self, tool_id: str) -> Optional[ToolMetadata]:
        return self._tools.get(tool_id)

    def get(self, tool_id: str) -> Optional[ToolMetadata]:
        return self._tools.get(tool_id)

    def list_all(self) -> list[ToolMetadata]:
        return list(self._tools.values())

    def list_enabled(self) -> list[ToolMetadata]:
        return [t for t in self._tools.values() if t.enabled]

    def exists(self, tool_id: str) -> bool:
        return tool_id in self._tools

    def discover(
        self,
        category: Optional[ToolCategory] = None,
        enabled_only: bool = True,
    ) -> list[ToolMetadata]:
        tools = self._tools.values()
        if enabled_only:
            tools = [t for t in tools if t.enabled]
        if category:
            tools = [t for t in tools if t.category == category]
        return list(tools)

    def get_openai_tools(self, enabled_only: bool = True) -> list[dict]:
        tools = self._tools.values()
        if enabled_only:
            tools = [t for t in tools if t.enabled]
        return [t.to_openai_schema() for t in tools]

    def get_executor(self, tool_id: str) -> Optional[ToolExecutor]:
        return self._executors.get(tool_id)

    async def execute(self, tool_id: str, args: dict[str, Any]) -> str:
        executor = self._executors.get(tool_id)
        if not executor:
            return f"Unknown tool: {tool_id}"
        return await executor(tool_id, args)

    def get_by_source(self, source: ToolSource) -> list[ToolMetadata]:
        return [t for t in self._tools.values() if t.source == source]

    def count(self) -> int:
        return len(self._tools)

    def summary(self) -> str:
        by_cat = {}
        for t in self._tools.values():
            by_cat.setdefault(t.category.value, []).append(t.id)
        lines = [f"Tools ({len(self._tools)} total):"]
        for cat, ids in sorted(by_cat.items()):
            lines.append(f"  {cat}: {', '.join(ids)}")
        return "\n".join(lines)

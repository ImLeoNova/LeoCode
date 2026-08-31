"""Configuration management for Leocode."""

import json
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

CONFIG_DIR = Path.home() / ".config" / "leocode"
CONFIG_FILE = CONFIG_DIR / "config.json"
CONVERSATIONS_DIR = CONFIG_DIR / "conversations"
RAG_DIR = CONFIG_DIR / "rag"

DEFAULT_CONFIG = {
    "base_url": "http://localhost:20128/v1",
    "api_key": "sk-895537f63fde664f-0vwekv-d61ce87b",
    "model": "glm-5",
    "temperature": 0.7,
    "max_tokens": 4096,
    "system_prompt": "You are LeoCode, a professional AI coding agent. You are terse, precise, and action-oriented. Write code directly. Explain only when asked.",
    "rag_enabled": True,
    "web_search_enabled": True,
    "mcp_enabled": True,
    "agent_mode": True,
    "theme": "dark",
    "mcp_servers": [],
    "rag_chunks": 5,
    "rag_chunk_size": 1000,
    "permission_policy": "balanced",
    "tool_timeout": 30,
    "max_retries": 1,
    "max_concurrent_tools": 5,
}


@dataclass
class Config:
    base_url: str = "http://localhost:20128/v1"
    api_key: str = "sk-895537f63fde664f-0vwekv-d61ce87b"
    model: str = "glm-5"
    temperature: float = 0.7
    max_tokens: int = 4096
    system_prompt: str = "You are LeoCode, a professional AI coding agent. You are terse, precise, and action-oriented. Write code directly. Explain only when asked."
    rag_enabled: bool = True
    web_search_enabled: bool = True
    mcp_enabled: bool = True
    agent_mode: bool = True
    theme: str = "dark"
    mcp_servers: list = field(default_factory=list)
    rag_chunks: int = 5
    rag_chunk_size: int = 1000
    permission_policy: str = "balanced"
    tool_timeout: int = 30
    max_retries: int = 1
    max_concurrent_tools: int = 5

    def save(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONVERSATIONS_DIR.mkdir(parents=True, exist_ok=True)
        RAG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(json.dumps(self.__dict__, indent=2))

    @classmethod
    def load(cls) -> "Config":
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONVERSATIONS_DIR.mkdir(parents=True, exist_ok=True)
        RAG_DIR.mkdir(parents=True, exist_ok=True)
        if CONFIG_FILE.exists():
            try:
                data = json.loads(CONFIG_FILE.read_text())
                return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
            except (json.JSONDecodeError, TypeError):
                pass
        cfg = cls()
        cfg.save()
        return cfg


def get_config() -> Config:
    return Config.load()

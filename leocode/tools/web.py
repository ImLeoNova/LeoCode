"""Web tools — fetch URL content."""

from __future__ import annotations

from typing import Any

from .registry import ToolMetadata, ToolCategory, RetryPolicy
from ..permissions import RiskLevel


def register_web_tools(registry, working_dir: str):
    """Register web tools into the registry."""

    async def execute_fetch(tool_id: str, args: dict) -> str:
        return await _tool_fetch(args)

    registry.register(
        ToolMetadata(
            id="fetch",
            name="Fetch",
            description="Fetch and parse content from a URL.",
            category=ToolCategory.WEB,
            input_schema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to fetch"},
                    "max_chars": {"type": "integer", "description": "Max chars to return", "default": 50000},
                },
                "required": ["url"],
            },
            risk_level=RiskLevel.LOW,
            timeout=30.0,
            retry_policy=RetryPolicy(max_retries=1, backoff_base=2.0),
        ),
        execute_fetch,
    )


async def _tool_fetch(args: dict) -> str:
    url = args.get("url", "")
    if not url:
        return "Error: No URL provided"
    max_chars = args.get("max_chars", 50000)

    try:
        import httpx
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            content_type = resp.headers.get("content-type", "")
            body = resp.text
            if len(body) > max_chars:
                body = body[:max_chars] + f"\n... (truncated at {max_chars} chars)"
            return f"URL: {url}\nStatus: {resp.status_code}\nType: {content_type}\n\n{body}"
    except ImportError:
        return "Error: httpx not installed"
    except Exception as e:
        return f"Error fetching URL: {e}"

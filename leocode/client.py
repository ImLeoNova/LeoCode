"""9Router API client - OpenAI-compatible chat, models, streaming, and tool calls."""

import json
import httpx
from typing import AsyncIterator, Optional, Any
from openai import AsyncOpenAI
from .config import Config


class ToolCallDelta:
    __slots__ = ("index", "id", "name", "arguments")

    def __init__(self, index: int = 0, id: str = "", name: str = "", arguments: str = ""):
        self.index = index
        self.id = id
        self.name = name
        self.arguments = arguments


class StreamChunk:
    __slots__ = ("content", "tool_calls", "finish_reason", "thinking")

    def __init__(
        self,
        content: str = "",
        tool_calls: list[ToolCallDelta] | None = None,
        finish_reason: str | None = None,
        thinking: str = "",
    ):
        self.content = content
        self.tool_calls = tool_calls or []
        self.finish_reason = finish_reason
        self.thinking = thinking


class RouterClient:
    def __init__(self, config: Config):
        self.config = config
        self._client: Optional[AsyncOpenAI] = None

    @property
    def client(self) -> AsyncOpenAI:
        if self._client is None:
            self._client = AsyncOpenAI(
                base_url=self.config.base_url,
                api_key=self.config.api_key,
                timeout=120.0,
            )
        return self._client

    def reconnect(self):
        self._client = None

    async def list_models(self) -> list[dict]:
        try:
            async with httpx.AsyncClient(timeout=15) as http:
                r = await http.get(
                    f"{self.config.base_url}/models",
                    headers={"Authorization": f"Bearer {self.config.api_key}"},
                )
                r.raise_for_status()
                data = r.json()
                models = data.get("data", [])
                return [{"id": m["id"], "owned_by": m.get("owned_by", "")} for m in models]
        except Exception:
            return []

    async def chat(
        self,
        messages: list[dict],
        model: str = "",
        temperature: float | None = None,
        max_tokens: int | None = None,
        stream: bool = True,
        tools: list[dict] | None = None,
    ) -> AsyncIterator[str]:
        model = model or self.config.model
        temp = temperature if temperature is not None else self.config.temperature
        tokens = max_tokens or self.config.max_tokens

        kwargs: dict[str, Any] = dict(
            model=model,
            messages=messages,
            temperature=temp,
            max_tokens=tokens,
            stream=stream,
        )
        if tools:
            kwargs["tools"] = tools

        if stream:
            response = await self.client.chat.completions.create(**kwargs)
            async for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        else:
            response = await self.client.chat.completions.create(**kwargs)
            if response.choices:
                content = response.choices[0].message.content or ""
                yield content

    async def chat_stream(
        self,
        messages: list[dict],
        model: str = "",
        temperature: float | None = None,
        max_tokens: int | None = None,
        tools: list[dict] | None = None,
    ) -> AsyncIterator[StreamChunk]:
        """Stream with full tool call delta support."""
        model = model or self.config.model
        temp = temperature if temperature is not None else self.config.temperature
        tokens = max_tokens or self.config.max_tokens

        kwargs: dict[str, Any] = dict(
            model=model,
            messages=messages,
            temperature=temp,
            max_tokens=tokens,
            stream=True,
        )
        if tools:
            kwargs["tools"] = tools

        response = await self.client.chat.completions.create(**kwargs)
        async for chunk in response:
            delta = chunk.choices[0].delta if chunk.choices else None
            finish = chunk.choices[0].finish_reason if chunk.choices else None

            content = delta.content if delta and delta.content else ""
            tool_calls = []

            if delta and delta.tool_calls:
                for tc in delta.tool_calls:
                    td = ToolCallDelta(
                        index=tc.index or 0,
                        id=tc.id or "",
                        name=tc.function.name if tc.function and tc.function.name else "",
                        arguments=tc.function.arguments if tc.function and tc.function.arguments else "",
                    )
                    tool_calls.append(td)

            yield StreamChunk(
                content=content,
                tool_calls=tool_calls,
                finish_reason=finish,
            )

    async def chat_sync(
        self,
        messages: list[dict],
        model: str = "",
        temperature: float | None = None,
        max_tokens: int | None = None,
        tools: list[dict] | None = None,
    ) -> str:
        chunks = []
        async for chunk in self.chat(
            messages, model=model, temperature=temperature,
            max_tokens=max_tokens, stream=False, tools=tools,
        ):
            chunks.append(chunk)
        return "".join(chunks)

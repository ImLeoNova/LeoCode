"""Web search via 9Router's search endpoint or fallback to Brave."""

import httpx
from typing import Optional


class WebSearch:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.removesuffix("/v1")
        self.api_key = api_key

    async def search(self, query: str, num_results: int = 5) -> list[dict]:
        results = await self._search_9router(query, num_results)
        if not results:
            results = await self._search_fallback(query, num_results)
        return results

    async def _search_9router(self, query: str, num: int) -> list[dict]:
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                r = await client.post(
                    f"{self.base_url}/v1/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "model": "",
                        "messages": [
                            {"role": "system", "content": "You are a web search assistant. Return search results as JSON array with fields: title, url, snippet. Return only the JSON array."},
                            {"role": "user", "content": f"Search the web for: {query}\nReturn {num} results as JSON array."},
                        ],
                        "temperature": 0.1,
                        "max_tokens": 2000,
                    },
                )
                r.raise_for_status()
                content = r.json()["choices"][0]["message"]["content"]
                import json
                import re
                json_match = re.search(r'\[.*\]', content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
        except Exception:
            pass
        return []

    async def _search_fallback(self, query: str, num: int) -> list[dict]:
        try:
            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                r = await client.get(
                    "https://api.search.brave.com/res/v1/web/search",
                    headers={"Accept": "application/json"},
                    params={"q": query, "count": num},
                )
                if r.status_code == 200:
                    data = r.json()
                    results = []
                    for item in data.get("web", {}).get("results", [])[:num]:
                        results.append({
                            "title": item.get("title", ""),
                            "url": item.get("url", ""),
                            "snippet": item.get("description", ""),
                        })
                    return results
        except Exception:
            pass
        return []

    async def fetch_url(self, url: str) -> str:
        try:
            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                r = await client.get(url)
                return r.text[:50000]
        except Exception as e:
            return f"Error fetching URL: {e}"

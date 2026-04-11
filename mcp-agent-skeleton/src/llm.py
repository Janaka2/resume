from __future__ import annotations

import os
from typing import Any

import requests


class DummyLLM:
    """Fallback LLM shim.

    Replace this class with your preferred provider SDK or API.
    """

    def complete(self, messages: list[dict[str, str]]) -> str:
        last_user = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        return f"[DummyLLM] I received: {last_user}"


class OpenAIHTTP:
    """Simple HTTP-based example for easy replacement.

    This intentionally uses plain requests to keep dependencies minimal.
    """

    def __init__(self, model: str | None = None) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.model = model or os.getenv("MODEL_NAME", "gpt-4.1-mini")

    def complete(self, messages: list[dict[str, str]]) -> str:
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is missing")

        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "messages": messages,
                "temperature": 0.2,
            },
            timeout=60,
        )
        response.raise_for_status()
        payload: dict[str, Any] = response.json()
        return payload["choices"][0]["message"]["content"]

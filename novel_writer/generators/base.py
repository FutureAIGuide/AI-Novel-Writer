"""Base class shared by all AI generators."""

from __future__ import annotations

from openai import OpenAI

from novel_writer.config import Config


class BaseGenerator:
    """Thin wrapper around the OpenAI client with shared helpers."""

    def __init__(self, client: OpenAI | None = None) -> None:
        Config.validate()
        self._client = client or OpenAI(api_key=Config.OPENAI_API_KEY)

    def _chat(self, system_prompt: str, user_prompt: str) -> str:
        """Send a chat completion request and return the text response."""
        response = self._client.chat.completions.create(
            model=Config.OPENAI_MODEL,
            max_tokens=Config.OPENAI_MAX_TOKENS,
            temperature=Config.OPENAI_TEMPERATURE,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.choices[0].message.content or ""

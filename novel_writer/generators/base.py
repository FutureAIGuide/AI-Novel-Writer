"""Base class shared by all AI generators."""

from __future__ import annotations

import logging
from collections.abc import Iterator
from typing import TYPE_CHECKING

from openai import OpenAI

from novel_writer.config import Config

if TYPE_CHECKING:
    from novel_writer.settings.models import AppSettings

logger = logging.getLogger(__name__)


class BaseGenerator:
    """Thin wrapper around an AI client with shared helpers.

    Provider selection is driven by the settings file
    (``~/.config/ai-novel-writer/settings.json``).  When no settings file
    exists the generator falls back to the ``OPENAI_*`` environment
    variables for full backward compatibility.

    An explicit *client* can be supplied (e.g. in tests) to bypass all
    automatic provider detection.
    """

    def __init__(self, client: OpenAI | None = None) -> None:
        self._app_settings: AppSettings | None = None
        if client is not None:
            # Direct injection (testing / legacy usage) — use OpenAI compat path
            Config.validate()
            self._client: OpenAI | object = client
            self._model: str = Config.OPENAI_MODEL
            self._max_tokens: int = Config.OPENAI_MAX_TOKENS
            self._temperature: float = Config.OPENAI_TEMPERATURE
            self._provider: str = "openai"
            self._use_openai_compat: bool = True
            return

        # Auto-detect provider from settings file
        try:
            from novel_writer.settings.manager import SettingsManager

            mgr = SettingsManager()
            if mgr.exists():
                settings = mgr.load()
                self._app_settings = settings
                self._provider = settings.active_provider
                self._setup_from_settings(settings)
                return
        except (ImportError, FileNotFoundError, OSError):
            pass  # settings module not available or file unreadable — fall through

        # Legacy: OpenAI via environment variables
        Config.validate()
        self._provider = "openai"
        self._use_openai_compat = True
        self._client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self._model = Config.OPENAI_MODEL
        self._max_tokens = Config.OPENAI_MAX_TOKENS
        self._temperature = Config.OPENAI_TEMPERATURE

    @property
    def provider(self) -> str:
        """Active provider key (e.g. ``openai``, ``ollama``)."""
        return self._provider

    @property
    def supports_streaming(self) -> bool:
        """True when token streaming is available (OpenAI-compatible path)."""
        return bool(self._use_openai_compat)

    # ------------------------------------------------------------------
    # Provider setup
    # ------------------------------------------------------------------

    def _setup_from_settings(self, settings: object) -> None:
        """Configure the client from *settings* based on the active provider."""
        from novel_writer.settings.models import AppSettings

        assert isinstance(settings, AppSettings)
        provider = settings.active_provider

        if provider == "openai":
            self._setup_openai(settings)
        elif provider == "anthropic":
            self._setup_anthropic(settings)
        elif provider == "google_ai":
            self._setup_google_ai(settings)
        elif provider == "openrouter":
            self._setup_openrouter(settings)
        elif provider == "lm_studio":
            self._setup_lm_studio(settings)
        elif provider == "ollama":
            self._setup_ollama(settings)
        else:
            raise ValueError(f"Unknown provider: {provider!r}")

    def _setup_openai(self, settings: object) -> None:
        from novel_writer.settings.models import AppSettings

        assert isinstance(settings, AppSettings)
        cfg = settings.openai
        api_key = cfg.api_key or Config.OPENAI_API_KEY
        if not api_key:
            raise ValueError(
                "OpenAI API key is not set. "
                "Run: novel-writer settings set-provider openai --api-key sk-..."
            )
        self._client = OpenAI(
            api_key=api_key,
            base_url=cfg.endpoint_url or None,
        )
        self._model = cfg.model or Config.OPENAI_MODEL
        self._max_tokens = cfg.max_tokens
        self._temperature = cfg.temperature
        self._use_openai_compat = True

    def _setup_anthropic(self, settings: object) -> None:
        try:
            import anthropic  # type: ignore[import]
        except ImportError as exc:
            raise ImportError(
                "The 'anthropic' package is required for Anthropic support. "
                "Run: pip install anthropic"
            ) from exc
        from novel_writer.settings.models import AppSettings

        assert isinstance(settings, AppSettings)
        cfg = settings.anthropic
        if not cfg.api_key:
            raise ValueError(
                "Anthropic API key is not set. "
                "Run: novel-writer settings set-provider anthropic --api-key <key>"
            )
        self._client = anthropic.Anthropic(api_key=cfg.api_key)
        self._model = cfg.model
        self._max_tokens = cfg.max_tokens
        self._temperature = 1.0  # Anthropic uses a different default scale
        self._use_openai_compat = False

    def _setup_google_ai(self, settings: object) -> None:
        try:
            import google.generativeai as genai  # type: ignore[import]
        except ImportError as exc:
            raise ImportError(
                "The 'google-generativeai' package is required for Google AI support. "
                "Run: pip install google-generativeai"
            ) from exc
        from novel_writer.settings.models import AppSettings

        assert isinstance(settings, AppSettings)
        cfg = settings.google_ai
        if not cfg.api_key:
            raise ValueError(
                "Google AI API key is not set. "
                "Run: novel-writer settings set-provider google_ai --api-key <key>"
            )
        genai.configure(api_key=cfg.api_key)
        self._client = genai.GenerativeModel(cfg.model)
        self._model = cfg.model
        self._max_tokens = 2048
        self._temperature = 0.8
        self._use_openai_compat = False

    def _setup_openrouter(self, settings: object) -> None:
        from novel_writer.settings.models import AppSettings

        assert isinstance(settings, AppSettings)
        cfg = settings.openrouter
        if not cfg.api_key:
            raise ValueError(
                "OpenRouter API key is not set. "
                "Run: novel-writer settings set-provider openrouter --api-key <key>"
            )
        self._client = OpenAI(
            api_key=cfg.api_key,
            base_url="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": cfg.site_url or "https://github.com/FutureAIGuide/AI-Novel-Writer",
                "X-Title": cfg.site_name or "AI Novel Writer",
            },
        )
        self._model = cfg.model
        self._max_tokens = cfg.max_tokens
        self._temperature = cfg.temperature
        self._use_openai_compat = True

    def _setup_lm_studio(self, settings: object) -> None:
        from novel_writer.settings.models import AppSettings

        assert isinstance(settings, AppSettings)
        cfg = settings.lm_studio
        endpoint = cfg.endpoint_url or "http://localhost:1234/v1"
        self._client = OpenAI(api_key="lm-studio", base_url=endpoint)
        self._model = cfg.model or "local-model"
        self._max_tokens = cfg.max_tokens
        self._temperature = cfg.temperature
        self._use_openai_compat = True

    def _setup_ollama(self, settings: object) -> None:
        from novel_writer.settings.models import AppSettings

        assert isinstance(settings, AppSettings)
        cfg = settings.ollama
        base = (cfg.endpoint_url or "http://localhost:11434").rstrip("/")
        self._client = OpenAI(api_key="ollama", base_url=f"{base}/v1")
        self._model = cfg.model or "llama3"
        self._max_tokens = cfg.max_tokens
        self._temperature = cfg.temperature
        self._use_openai_compat = True

    # ------------------------------------------------------------------
    # Shared chat helper
    # ------------------------------------------------------------------

    def _chat(self, system_prompt: str, user_prompt: str) -> str:
        """Send a chat completion request and return the text response."""
        if self._use_openai_compat:
            return self._chat_openai_compat(system_prompt, user_prompt)
        if self._provider == "anthropic":
            return self._chat_anthropic(system_prompt, user_prompt)
        if self._provider == "google_ai":
            return self._chat_google_ai(system_prompt, user_prompt)
        raise RuntimeError(f"No chat implementation for provider: {self._provider!r}")

    def _chat_openai_compat(self, system_prompt: str, user_prompt: str) -> str:
        """OpenAI-compatible chat completion (openai, openrouter, lm_studio, ollama)."""
        assert isinstance(self._client, OpenAI)
        text = self._openai_compat_completion_text(system_prompt, user_prompt)
        if not text.strip():
            logger.warning(
                "Empty completion from provider=%s model=%s; retrying once",
                self._provider,
                self._model,
            )
            text = self._openai_compat_completion_text(system_prompt, user_prompt)
        if not text.strip():
            raise RuntimeError(
                f"The model returned no text (provider={self._provider!r}, model={self._model!r}). "
                "Check that the local server is running and the model is loaded."
            )
        return text

    def _openai_compat_completion_text(self, system_prompt: str, user_prompt: str) -> str:
        assert isinstance(self._client, OpenAI)
        response = self._client.chat.completions.create(
            model=self._model,
            max_tokens=self._max_tokens,
            temperature=self._temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.choices[0].message.content or ""

    def stream_chat(self, system_prompt: str, user_prompt: str) -> Iterator[str]:
        """Yield text fragments from a streamed chat completion (OpenAI-compatible only)."""
        if not self._use_openai_compat:
            yield self._chat(system_prompt, user_prompt)
            return
        assert isinstance(self._client, OpenAI)
        stream = self._client.chat.completions.create(
            model=self._model,
            max_tokens=self._max_tokens,
            temperature=self._temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            stream=True,
        )
        assembled: list[str] = []
        for chunk in stream:
            choice = chunk.choices[0] if chunk.choices else None
            if choice is None:
                continue
            delta = getattr(choice, "delta", None)
            piece = getattr(delta, "content", None) if delta is not None else None
            if piece:
                assembled.append(piece)
                yield piece
        full = "".join(assembled)
        if not full.strip():
            logger.warning(
                "Empty streamed completion from provider=%s model=%s",
                self._provider,
                self._model,
            )
            # Fallback: one non-streaming attempt
            full = self._chat_openai_compat(system_prompt, user_prompt)
            yield full

    def _chat_anthropic(self, system_prompt: str, user_prompt: str) -> str:
        """Anthropic Messages API."""
        response = self._client.messages.create(  # type: ignore[attr-defined]
            model=self._model,
            max_tokens=self._max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        block = response.content[0]
        return getattr(block, "text", str(block))

    def _chat_google_ai(self, system_prompt: str, user_prompt: str) -> str:
        """Google Generative AI."""
        combined = f"{system_prompt}\n\n{user_prompt}"
        response = self._client.generate_content(combined)  # type: ignore[attr-defined]
        return response.text

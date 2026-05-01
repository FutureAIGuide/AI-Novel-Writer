"""Settings models for AI Novel Writer.

Defines Pydantic models for each supported AI provider along with
their built-in model identifiers.
"""

from __future__ import annotations

from typing import List
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Built-in model identifier catalogues
# ---------------------------------------------------------------------------

OPENAI_MODELS: List[str] = [
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4-turbo",
    "gpt-4",
    "gpt-3.5-turbo",
]

ANTHROPIC_MODELS: List[str] = [
    "claude-3-5-sonnet-20241022",
    "claude-3-5-haiku-20241022",
    "claude-3-opus-20240229",
    "claude-3-sonnet-20240229",
    "claude-3-haiku-20240307",
]

GOOGLE_AI_MODELS: List[str] = [
    "gemini-1.5-pro",
    "gemini-1.5-flash",
    "gemini-pro",
    "gemini-pro-vision",
]

OPENROUTER_MODELS: List[str] = [
    "openai/gpt-4o",
    "openai/gpt-4-turbo",
    "anthropic/claude-3.5-sonnet",
    "anthropic/claude-3-haiku",
    "meta-llama/llama-3.1-8b-instruct",
    "meta-llama/llama-3.1-70b-instruct",
    "mistralai/mistral-7b-instruct",
    "mistralai/mixtral-8x7b-instruct",
    "google/gemini-pro",
    "google/gemini-flash-1.5",
]

OLLAMA_MODELS: List[str] = [
    "llama3",
    "llama3.1",
    "llama3.2",
    "mistral",
    "mistral-nemo",
    "codellama",
    "phi3",
    "phi3.5",
    "neural-chat",
    "gemma2",
    "qwen2",
    "deepseek-coder",
    "dolphin-mixtral",
]

# Human-readable names for each provider key
PROVIDER_NAMES: dict[str, str] = {
    "openai": "OpenAI",
    "anthropic": "Anthropic",
    "google_ai": "Google AI (Gemini)",
    "openrouter": "OpenRouter",
    "lm_studio": "LM Studio (Local)",
    "ollama": "Ollama (Local)",
}

# ---------------------------------------------------------------------------
# Per-provider configuration models
# ---------------------------------------------------------------------------


class OpenAISettings(BaseModel):
    """Configuration for the OpenAI API provider."""

    enabled: bool = Field(default=False, description="Whether this provider is enabled")
    api_key: str = Field(default="", description="OpenAI API key (sk-...)")
    model: str = Field(default="gpt-4o", description="Model identifier")
    endpoint_url: str = Field(
        default="",
        description="Custom endpoint URL (leave blank for the official API)",
    )
    max_tokens: int = Field(default=2048, description="Maximum tokens per request")
    temperature: float = Field(
        default=0.8, description="Creativity level (0.0–1.0)", ge=0.0, le=2.0
    )


class AnthropicSettings(BaseModel):
    """Configuration for the Anthropic API provider."""

    enabled: bool = Field(default=False)
    api_key: str = Field(default="", description="Anthropic API key")
    model: str = Field(
        default="claude-3-5-sonnet-20241022", description="Claude model identifier"
    )
    endpoint_url: str = Field(default="", description="Custom endpoint URL")
    max_tokens: int = Field(default=2048)


class GoogleAISettings(BaseModel):
    """Configuration for the Google AI (Gemini) provider."""

    enabled: bool = Field(default=False)
    api_key: str = Field(default="", description="Google AI API key")
    model: str = Field(default="gemini-1.5-pro", description="Gemini model identifier")
    region: str = Field(default="", description="Optional region/location")


class OpenRouterSettings(BaseModel):
    """Configuration for the OpenRouter API provider."""

    enabled: bool = Field(default=False)
    api_key: str = Field(default="", description="OpenRouter API key")
    model: str = Field(
        default="openai/gpt-4o", description="Model identifier (provider/model format)"
    )
    site_url: str = Field(
        default="", description="Your site URL for OpenRouter attribution"
    )
    site_name: str = Field(
        default="AI Novel Writer", description="Your app name for OpenRouter attribution"
    )
    max_tokens: int = Field(default=2048, description="Maximum tokens per request")
    temperature: float = Field(
        default=0.8, description="Creativity level (0.0–2.0 for OpenAI-compatible APIs)",
        ge=0.0,
        le=2.0,
    )


class LMStudioSettings(BaseModel):
    """Configuration for LM Studio (local AI server)."""

    enabled: bool = Field(default=False)
    endpoint_url: str = Field(
        default="http://localhost:1234/v1",
        description="LM Studio server endpoint (OpenAI-compatible)",
    )
    model: str = Field(
        default="",
        description="Model identifier as reported by LM Studio (leave blank to auto-detect)",
    )
    max_tokens: int = Field(default=2048, description="Maximum tokens per request")
    temperature: float = Field(
        default=0.8, description="Creativity level (0.0–2.0)", ge=0.0, le=2.0
    )


class OllamaSettings(BaseModel):
    """Configuration for Ollama (local AI server)."""

    enabled: bool = Field(default=False)
    endpoint_url: str = Field(
        default="http://localhost:11434",
        description="Ollama server base URL",
    )
    model: str = Field(default="llama3", description="Ollama model name")
    max_tokens: int = Field(default=2048, description="Maximum tokens per request")
    temperature: float = Field(
        default=0.8, description="Creativity level (0.0–2.0)", ge=0.0, le=2.0
    )


# ---------------------------------------------------------------------------
# Top-level application settings
# ---------------------------------------------------------------------------


class AppSettings(BaseModel):
    """Top-level application settings container."""

    active_provider: str = Field(
        default="openai",
        description=(
            "The provider used for all AI generation. "
            "One of: openai, anthropic, google_ai, openrouter, lm_studio, ollama"
        ),
    )
    openai: OpenAISettings = Field(default_factory=OpenAISettings)
    anthropic: AnthropicSettings = Field(default_factory=AnthropicSettings)
    google_ai: GoogleAISettings = Field(default_factory=GoogleAISettings)
    openrouter: OpenRouterSettings = Field(default_factory=OpenRouterSettings)
    lm_studio: LMStudioSettings = Field(default_factory=LMStudioSettings)
    ollama: OllamaSettings = Field(default_factory=OllamaSettings)
    output_dir: str = Field(default="stories", description="Directory where stories are saved")
    studio_context_budget_tokens: int = Field(
        default=0,
        description=(
            "Approximate max prompt tokens for studio AI context packing "
            "(0 = auto from provider: lower for lm_studio/ollama)"
        ),
        ge=0,
    )

    def get_active_provider_settings(
        self,
    ) -> OpenAISettings | AnthropicSettings | GoogleAISettings | OpenRouterSettings | LMStudioSettings | OllamaSettings:
        """Return the settings object for the currently active provider."""
        return getattr(self, self.active_provider)

    def requires_api_key(self) -> bool:
        """Return True if the active provider requires an API key."""
        return self.active_provider not in ("lm_studio", "ollama")

    def is_configured(self) -> bool:
        """Return True if the active provider is adequately configured."""
        provider = self.active_provider
        if provider in ("lm_studio", "ollama"):
            return True  # Local providers just need an endpoint
        cfg = self.get_active_provider_settings()
        return bool(getattr(cfg, "api_key", ""))

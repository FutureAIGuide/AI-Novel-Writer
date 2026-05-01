"""Settings package for AI Novel Writer."""

from novel_writer.settings.models import (
    AppSettings,
    OpenAISettings,
    AnthropicSettings,
    GoogleAISettings,
    OpenRouterSettings,
    LMStudioSettings,
    OllamaSettings,
    OPENAI_MODELS,
    ANTHROPIC_MODELS,
    GOOGLE_AI_MODELS,
    OPENROUTER_MODELS,
    OLLAMA_MODELS,
    PROVIDER_NAMES,
)
from novel_writer.settings.manager import SettingsManager

__all__ = [
    "AppSettings",
    "OpenAISettings",
    "AnthropicSettings",
    "GoogleAISettings",
    "OpenRouterSettings",
    "LMStudioSettings",
    "OllamaSettings",
    "OPENAI_MODELS",
    "ANTHROPIC_MODELS",
    "GOOGLE_AI_MODELS",
    "OPENROUTER_MODELS",
    "OLLAMA_MODELS",
    "PROVIDER_NAMES",
    "SettingsManager",
]

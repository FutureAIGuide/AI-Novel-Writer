"""Configuration management for AI Novel Writer."""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration loaded from environment variables.

    When a settings file exists (managed via ``novel-writer settings``),
    the active provider's values take precedence over these environment
    variables.  Environment variables remain as a convenient fallback for
    the default OpenAI provider.
    """

    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")
    OPENAI_MAX_TOKENS: int = int(os.getenv("OPENAI_MAX_TOKENS", "2048"))
    OPENAI_TEMPERATURE: float = float(os.getenv("OPENAI_TEMPERATURE", "0.8"))

    OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", "stories")

    @classmethod
    def validate(cls) -> None:
        """Raise ValueError if required configuration is missing.

        Accepts configuration from either:
        - The settings file (``~/.config/ai-novel-writer/settings.json``)
        - Environment variables (``OPENAI_API_KEY``)
        """
        # Check settings file first
        try:
            from novel_writer.settings.manager import SettingsManager

            mgr = SettingsManager()
            if mgr.exists():
                settings = mgr.load()
                if settings.is_configured():
                    return  # settings file has a fully configured provider
        except (ImportError, FileNotFoundError, OSError):
            pass  # settings module not available or file unreadable — fall through

        # Fall back to the legacy environment variable
        if not cls.OPENAI_API_KEY:
            raise ValueError(
                "No AI provider is configured. Either:\n"
                "  • Copy .env.example to .env and set OPENAI_API_KEY, or\n"
                "  • Run: novel-writer settings set-provider openai --api-key sk-..."
            )

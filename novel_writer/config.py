"""Configuration management for AI Novel Writer."""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration loaded from environment variables."""

    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")
    OPENAI_MAX_TOKENS: int = int(os.getenv("OPENAI_MAX_TOKENS", "2048"))
    OPENAI_TEMPERATURE: float = float(os.getenv("OPENAI_TEMPERATURE", "0.8"))

    OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", "stories")

    @classmethod
    def validate(cls) -> None:
        """Raise ValueError if required configuration is missing."""
        if not cls.OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY is not set. "
                "Copy .env.example to .env and add your API key."
            )

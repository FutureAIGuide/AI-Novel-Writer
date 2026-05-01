"""Settings persistence for AI Novel Writer.

Handles saving and loading :class:`AppSettings` to/from a JSON file.
API keys are stored with simple Base-64 obfuscation so they are not
stored in plain text.  For stronger protection, prefer environment
variables or a secrets manager.
"""

from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from typing import Any

from novel_writer.settings.models import AppSettings

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_OBS_PREFIX = "obs:"

# Field names that contain sensitive data and should be obfuscated
_SENSITIVE_FIELDS = ("api_key",)

# Provider keys that may contain api_key fields
_PROVIDER_KEYS = ("openai", "anthropic", "google_ai", "openrouter")


def _obfuscate(value: str) -> str:
    """Encode a string with Base-64 and add a recognisable prefix."""
    return _OBS_PREFIX + base64.b64encode(value.encode()).decode()


def _deobfuscate(value: str) -> str:
    """Reverse :func:`_obfuscate`.  Returns *value* unchanged if not encoded."""
    if value.startswith(_OBS_PREFIX):
        try:
            return base64.b64decode(value[len(_OBS_PREFIX):]).decode()
        except Exception:
            return value
    return value


def _encode_sensitive(data: dict[str, Any]) -> None:
    """Obfuscate all api_key fields inside *data* in-place."""
    for provider in _PROVIDER_KEYS:
        if provider in data:
            for field in _SENSITIVE_FIELDS:
                raw = data[provider].get(field, "")
                if raw and not raw.startswith(_OBS_PREFIX):
                    data[provider][field] = _obfuscate(raw)


def _decode_sensitive(data: dict[str, Any]) -> None:
    """Decode all obfuscated api_key fields inside *data* in-place."""
    for provider in _PROVIDER_KEYS:
        if provider in data:
            for field in _SENSITIVE_FIELDS:
                raw = data[provider].get(field, "")
                if raw:
                    data[provider][field] = _deobfuscate(raw)


# ---------------------------------------------------------------------------
# SettingsManager
# ---------------------------------------------------------------------------


class SettingsManager:
    """Persist :class:`AppSettings` to a local JSON configuration file.

    The default settings file lives at
    ``~/.config/ai-novel-writer/settings.json`` and can be overridden
    with the ``AI_NOVEL_WRITER_SETTINGS`` environment variable.
    """

    DEFAULT_PATH: Path = (
        Path.home() / ".config" / "ai-novel-writer" / "settings.json"
    )

    def __init__(self, settings_path: str | Path | None = None) -> None:
        env_path = os.getenv("AI_NOVEL_WRITER_SETTINGS")
        self.settings_path = Path(
            settings_path or env_path or self.DEFAULT_PATH
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load(self) -> AppSettings:
        """Load :class:`AppSettings` from the config file.

        Returns a default :class:`AppSettings` instance if the file does
        not exist yet.
        """
        if not self.settings_path.exists():
            return AppSettings()
        try:
            data: dict[str, Any] = json.loads(self.settings_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return AppSettings()
        _decode_sensitive(data)
        return AppSettings(**data)

    def save(self, settings: AppSettings) -> None:
        """Persist *settings* to the config file.

        The parent directory is created automatically if it does not exist.
        """
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)
        data = settings.model_dump()
        _encode_sensitive(data)
        self.settings_path.write_text(
            json.dumps(data, indent=2), encoding="utf-8"
        )

    def exists(self) -> bool:
        """Return *True* if the settings file exists."""
        return self.settings_path.exists()

    def delete(self) -> None:
        """Delete the settings file if it exists."""
        if self.settings_path.exists():
            self.settings_path.unlink()

    def export_safe(self, output_path: str | Path) -> None:
        """Export settings *without* API keys to *output_path* (backup).

        All api_key fields are replaced with an empty string in the export
        so that backups can be shared without exposing credentials.
        """
        settings = self.load()
        data = settings.model_dump()
        for provider in _PROVIDER_KEYS:
            if provider in data:
                for field in _SENSITIVE_FIELDS:
                    data[provider][field] = ""
        Path(output_path).write_text(json.dumps(data, indent=2), encoding="utf-8")

    def import_from(self, input_path: str | Path) -> AppSettings:
        """Import settings from *input_path* and merge with existing settings.

        API keys in the current settings are preserved when the imported
        file omits them (empty string).
        """
        current = self.load()
        raw = json.loads(Path(input_path).read_text(encoding="utf-8"))
        _decode_sensitive(raw)
        imported = AppSettings(**raw)

        # Preserve existing keys when import does not supply them
        for provider in _PROVIDER_KEYS:
            current_cfg = getattr(current, provider)
            imported_cfg = getattr(imported, provider)
            if not getattr(imported_cfg, "api_key", ""):
                existing_key = getattr(current_cfg, "api_key", "")
                if existing_key:
                    imported_cfg.api_key = existing_key

        self.save(imported)
        return imported

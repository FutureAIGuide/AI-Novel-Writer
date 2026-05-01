"""Tests for the settings system (models, manager, and CLI)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from novel_writer.settings.models import (
    ANTHROPIC_MODELS,
    GOOGLE_AI_MODELS,
    OLLAMA_MODELS,
    OPENAI_MODELS,
    OPENROUTER_MODELS,
    PROVIDER_NAMES,
    AppSettings,
    AnthropicSettings,
    GoogleAISettings,
    LMStudioSettings,
    OllamaSettings,
    OpenAISettings,
    OpenRouterSettings,
)
from novel_writer.settings.manager import (
    SettingsManager,
    _deobfuscate,
    _obfuscate,
)
from novel_writer.settings.cli import settings_cli


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_settings_path(tmp_path: Path) -> Path:
    return tmp_path / "settings.json"


@pytest.fixture
def mgr(tmp_settings_path: Path) -> SettingsManager:
    return SettingsManager(settings_path=tmp_settings_path)


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------


class TestProviderModels:
    def test_openai_defaults(self) -> None:
        cfg = OpenAISettings()
        assert cfg.model == "gpt-4o"
        assert cfg.max_tokens == 2048
        assert cfg.temperature == 0.8
        assert not cfg.enabled
        assert cfg.api_key == ""

    def test_anthropic_defaults(self) -> None:
        cfg = AnthropicSettings()
        assert "claude" in cfg.model
        assert not cfg.enabled

    def test_google_ai_defaults(self) -> None:
        cfg = GoogleAISettings()
        assert "gemini" in cfg.model

    def test_lm_studio_defaults(self) -> None:
        cfg = LMStudioSettings()
        assert "1234" in cfg.endpoint_url

    def test_ollama_defaults(self) -> None:
        cfg = OllamaSettings()
        assert "11434" in cfg.endpoint_url
        assert cfg.model == "llama3"

    def test_openrouter_defaults(self) -> None:
        cfg = OpenRouterSettings()
        assert cfg.model.startswith("openai/")

    def test_app_settings_defaults(self) -> None:
        settings = AppSettings()
        assert settings.active_provider == "openai"
        assert isinstance(settings.openai, OpenAISettings)
        assert isinstance(settings.anthropic, AnthropicSettings)

    def test_app_settings_requires_api_key_for_cloud(self) -> None:
        settings = AppSettings(active_provider="openai")
        assert settings.requires_api_key() is True

    def test_app_settings_no_api_key_for_local(self) -> None:
        settings = AppSettings(active_provider="lm_studio")
        assert settings.requires_api_key() is False
        settings2 = AppSettings(active_provider="ollama")
        assert settings2.requires_api_key() is False

    def test_is_configured_local_providers(self) -> None:
        settings = AppSettings(active_provider="lm_studio")
        assert settings.is_configured() is True
        settings2 = AppSettings(active_provider="ollama")
        assert settings2.is_configured() is True

    def test_is_configured_cloud_without_key(self) -> None:
        settings = AppSettings(active_provider="openai")
        assert settings.is_configured() is False

    def test_is_configured_cloud_with_key(self) -> None:
        settings = AppSettings(active_provider="openai")
        settings.openai.api_key = "sk-test"
        assert settings.is_configured() is True

    def test_get_active_provider_settings(self) -> None:
        settings = AppSettings(active_provider="anthropic")
        cfg = settings.get_active_provider_settings()
        assert isinstance(cfg, AnthropicSettings)


class TestBuiltinModels:
    def test_openai_models_not_empty(self) -> None:
        assert len(OPENAI_MODELS) >= 3
        assert "gpt-4o" in OPENAI_MODELS

    def test_anthropic_models_not_empty(self) -> None:
        assert len(ANTHROPIC_MODELS) >= 3
        assert any("claude" in m for m in ANTHROPIC_MODELS)

    def test_google_ai_models_not_empty(self) -> None:
        assert len(GOOGLE_AI_MODELS) >= 2
        assert any("gemini" in m for m in GOOGLE_AI_MODELS)

    def test_openrouter_models_not_empty(self) -> None:
        assert len(OPENROUTER_MODELS) >= 5

    def test_ollama_models_not_empty(self) -> None:
        assert len(OLLAMA_MODELS) >= 5
        assert "llama3" in OLLAMA_MODELS
        assert "mistral" in OLLAMA_MODELS

    def test_provider_names_covers_all(self) -> None:
        expected = {"openai", "anthropic", "google_ai", "openrouter", "lm_studio", "ollama"}
        assert set(PROVIDER_NAMES.keys()) == expected


# ---------------------------------------------------------------------------
# Obfuscation helpers
# ---------------------------------------------------------------------------


class TestObfuscation:
    def test_roundtrip(self) -> None:
        secret = "sk-supersecretkey1234"
        assert _deobfuscate(_obfuscate(secret)) == secret

    def test_obfuscated_has_prefix(self) -> None:
        encoded = _obfuscate("hello")
        assert encoded.startswith("obs:")

    def test_deobfuscate_passthrough_plain(self) -> None:
        plain = "not-encoded"
        assert _deobfuscate(plain) == plain

    def test_deobfuscate_empty(self) -> None:
        assert _deobfuscate("") == ""

    def test_obfuscate_empty(self) -> None:
        encoded = _obfuscate("")
        assert _deobfuscate(encoded) == ""


# ---------------------------------------------------------------------------
# SettingsManager tests
# ---------------------------------------------------------------------------


class TestSettingsManager:
    def test_load_returns_defaults_when_no_file(self, mgr: SettingsManager) -> None:
        settings = mgr.load()
        assert isinstance(settings, AppSettings)
        assert settings.active_provider == "openai"

    def test_exists_false_initially(self, mgr: SettingsManager) -> None:
        assert mgr.exists() is False

    def test_save_creates_file(self, mgr: SettingsManager) -> None:
        mgr.save(AppSettings())
        assert mgr.settings_path.exists()

    def test_exists_after_save(self, mgr: SettingsManager) -> None:
        mgr.save(AppSettings())
        assert mgr.exists() is True

    def test_save_load_roundtrip(self, mgr: SettingsManager) -> None:
        settings = AppSettings(active_provider="anthropic")
        settings.anthropic.api_key = "ant-key-123"
        settings.anthropic.model = "claude-3-opus-20240229"
        mgr.save(settings)

        loaded = mgr.load()
        assert loaded.active_provider == "anthropic"
        assert loaded.anthropic.api_key == "ant-key-123"
        assert loaded.anthropic.model == "claude-3-opus-20240229"

    def test_api_key_obfuscated_on_disk(self, mgr: SettingsManager) -> None:
        settings = AppSettings()
        settings.openai.api_key = "sk-plaintext"
        mgr.save(settings)

        raw = json.loads(mgr.settings_path.read_text())
        stored = raw["openai"]["api_key"]
        assert stored != "sk-plaintext"
        assert stored.startswith("obs:")

    def test_api_key_deobfuscated_on_load(self, mgr: SettingsManager) -> None:
        settings = AppSettings()
        settings.openai.api_key = "sk-plaintext"
        mgr.save(settings)

        loaded = mgr.load()
        assert loaded.openai.api_key == "sk-plaintext"

    def test_delete(self, mgr: SettingsManager) -> None:
        mgr.save(AppSettings())
        mgr.delete()
        assert not mgr.settings_path.exists()

    def test_delete_noop_when_missing(self, mgr: SettingsManager) -> None:
        mgr.delete()  # Should not raise

    def test_export_safe_strips_keys(self, mgr: SettingsManager, tmp_path: Path) -> None:
        settings = AppSettings()
        settings.openai.api_key = "sk-secret"
        mgr.save(settings)

        out = tmp_path / "backup.json"
        mgr.export_safe(out)

        data = json.loads(out.read_text())
        assert data["openai"]["api_key"] == ""

    def test_import_from_preserves_existing_keys(
        self, mgr: SettingsManager, tmp_path: Path
    ) -> None:
        # Save current settings with a key
        current = AppSettings()
        current.openai.api_key = "sk-existing"
        mgr.save(current)

        # Create an import file without the key
        import_data = AppSettings(active_provider="anthropic").model_dump()
        import_data["openai"]["api_key"] = ""
        import_file = tmp_path / "import.json"
        import_file.write_text(json.dumps(import_data))

        imported = mgr.import_from(import_file)
        assert imported.openai.api_key == "sk-existing"
        assert imported.active_provider == "anthropic"

    def test_load_handles_corrupt_file(self, mgr: SettingsManager) -> None:
        mgr.settings_path.parent.mkdir(parents=True, exist_ok=True)
        mgr.settings_path.write_text("{ invalid json }")
        settings = mgr.load()
        assert isinstance(settings, AppSettings)  # Falls back to defaults


# ---------------------------------------------------------------------------
# Settings CLI tests
# ---------------------------------------------------------------------------


class TestSettingsCLI:
    def _make_mgr_env(self, tmp_settings_path: Path) -> dict[str, str]:
        """Return env vars that redirect the settings file to tmp_settings_path."""
        return {"AI_NOVEL_WRITER_SETTINGS": str(tmp_settings_path)}

    def test_show_no_file(self, runner: CliRunner, tmp_settings_path: Path) -> None:
        env = self._make_mgr_env(tmp_settings_path)
        result = runner.invoke(settings_cli, ["show"], env=env)
        assert result.exit_code == 0
        assert "openai" in result.output.lower()

    def test_set_provider_openai(self, runner: CliRunner, tmp_settings_path: Path) -> None:
        env = self._make_mgr_env(tmp_settings_path)
        result = runner.invoke(
            settings_cli,
            ["set-provider", "openai", "--api-key", "sk-test", "--model", "gpt-4"],
            env=env,
        )
        assert result.exit_code == 0, result.output
        # Verify persisted
        mgr = SettingsManager(settings_path=tmp_settings_path)
        settings = mgr.load()
        assert settings.openai.api_key == "sk-test"
        assert settings.openai.model == "gpt-4"
        assert settings.openai.enabled is True

    def test_set_provider_disable(self, runner: CliRunner, tmp_settings_path: Path) -> None:
        env = self._make_mgr_env(tmp_settings_path)
        runner.invoke(
            settings_cli,
            ["set-provider", "openai", "--api-key", "sk-test"],
            env=env,
        )
        result = runner.invoke(
            settings_cli,
            ["set-provider", "openai", "--disable"],
            env=env,
        )
        assert result.exit_code == 0
        mgr = SettingsManager(settings_path=tmp_settings_path)
        settings = mgr.load()
        assert settings.openai.enabled is False

    def test_set_provider_set_active_flag(self, runner: CliRunner, tmp_settings_path: Path) -> None:
        env = self._make_mgr_env(tmp_settings_path)
        result = runner.invoke(
            settings_cli,
            ["set-provider", "ollama", "--set-active"],
            env=env,
        )
        assert result.exit_code == 0
        mgr = SettingsManager(settings_path=tmp_settings_path)
        settings = mgr.load()
        assert settings.active_provider == "ollama"

    def test_active_command(self, runner: CliRunner, tmp_settings_path: Path) -> None:
        env = self._make_mgr_env(tmp_settings_path)
        result = runner.invoke(settings_cli, ["active", "anthropic"], env=env)
        assert result.exit_code == 0
        mgr = SettingsManager(settings_path=tmp_settings_path)
        assert mgr.load().active_provider == "anthropic"

    def test_remove_command(self, runner: CliRunner, tmp_settings_path: Path) -> None:
        env = self._make_mgr_env(tmp_settings_path)
        runner.invoke(
            settings_cli,
            ["set-provider", "anthropic", "--api-key", "ant-key", "--set-active"],
            env=env,
        )
        result = runner.invoke(
            settings_cli,
            ["remove", "anthropic", "--clear-key"],
            env=env,
        )
        assert result.exit_code == 0
        mgr = SettingsManager(settings_path=tmp_settings_path)
        settings = mgr.load()
        assert settings.anthropic.enabled is False
        assert settings.anthropic.api_key == ""
        # Active provider should have been reset
        assert settings.active_provider == "openai"

    def test_list_models_openai(self, runner: CliRunner, tmp_settings_path: Path) -> None:
        env = self._make_mgr_env(tmp_settings_path)
        result = runner.invoke(settings_cli, ["list-models", "openai"], env=env)
        assert result.exit_code == 0
        assert "gpt-4o" in result.output

    def test_list_models_anthropic(self, runner: CliRunner, tmp_settings_path: Path) -> None:
        env = self._make_mgr_env(tmp_settings_path)
        result = runner.invoke(settings_cli, ["list-models", "anthropic"], env=env)
        assert result.exit_code == 0
        assert "claude" in result.output

    def test_list_models_ollama(self, runner: CliRunner, tmp_settings_path: Path) -> None:
        env = self._make_mgr_env(tmp_settings_path)
        result = runner.invoke(settings_cli, ["list-models", "ollama"], env=env)
        assert result.exit_code == 0
        assert "llama3" in result.output

    def test_list_models_lm_studio(self, runner: CliRunner, tmp_settings_path: Path) -> None:
        env = self._make_mgr_env(tmp_settings_path)
        result = runner.invoke(settings_cli, ["list-models", "lm_studio"], env=env)
        assert result.exit_code == 0
        # LM Studio has no built-in list — should show a help message
        assert "lm_studio" in result.output.lower() or "locally" in result.output.lower()

    def test_export_strips_keys(self, runner: CliRunner, tmp_settings_path: Path, tmp_path: Path) -> None:
        env = self._make_mgr_env(tmp_settings_path)
        runner.invoke(
            settings_cli,
            ["set-provider", "openai", "--api-key", "sk-secret"],
            env=env,
        )
        out_file = str(tmp_path / "backup.json")
        result = runner.invoke(
            settings_cli,
            ["export", "--output", out_file],
            env=env,
        )
        assert result.exit_code == 0
        data = json.loads(Path(out_file).read_text())
        assert data["openai"]["api_key"] == ""

    def test_import_command(self, runner: CliRunner, tmp_settings_path: Path, tmp_path: Path) -> None:
        env = self._make_mgr_env(tmp_settings_path)
        # Create an import file
        import_data = AppSettings(active_provider="ollama").model_dump()
        import_file = tmp_path / "import.json"
        import_file.write_text(json.dumps(import_data))

        result = runner.invoke(
            settings_cli,
            ["import", "--input", str(import_file)],
            env=env,
        )
        assert result.exit_code == 0
        mgr = SettingsManager(settings_path=tmp_settings_path)
        settings = mgr.load()
        assert settings.active_provider == "ollama"

    def test_import_missing_file(self, runner: CliRunner, tmp_settings_path: Path) -> None:
        env = self._make_mgr_env(tmp_settings_path)
        result = runner.invoke(
            settings_cli,
            ["import", "--input", "/nonexistent/path/settings.json"],
            env=env,
        )
        assert result.exit_code != 0

    def test_set_provider_lm_studio_endpoint(
        self, runner: CliRunner, tmp_settings_path: Path
    ) -> None:
        env = self._make_mgr_env(tmp_settings_path)
        result = runner.invoke(
            settings_cli,
            [
                "set-provider",
                "lm_studio",
                "--endpoint",
                "http://localhost:5000/v1",
                "--model",
                "my-local-model",
            ],
            env=env,
        )
        assert result.exit_code == 0
        mgr = SettingsManager(settings_path=tmp_settings_path)
        settings = mgr.load()
        assert settings.lm_studio.endpoint_url == "http://localhost:5000/v1"
        assert settings.lm_studio.model == "my-local-model"

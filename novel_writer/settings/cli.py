"""CLI commands for managing AI Novel Writer settings.

Registered as ``novel-writer settings`` via ``main.py``.
"""

from __future__ import annotations

import json
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from novel_writer.settings.manager import SettingsManager
from novel_writer.settings.models import (
    ANTHROPIC_MODELS,
    GOOGLE_AI_MODELS,
    OLLAMA_MODELS,
    OPENAI_MODELS,
    OPENROUTER_MODELS,
    PROVIDER_NAMES,
    AppSettings,
)

console = Console()

_PROVIDERS = list(PROVIDER_NAMES.keys())
_LOCAL_PROVIDERS = {"lm_studio", "ollama"}


# ---------------------------------------------------------------------------
# Settings CLI group
# ---------------------------------------------------------------------------


@click.group("settings")
def settings_cli() -> None:
    """Manage AI provider settings and API keys."""


# ---------------------------------------------------------------------------
# show — display current settings
# ---------------------------------------------------------------------------


@settings_cli.command("show")
def show() -> None:
    """Display the current settings (API keys are masked)."""
    mgr = SettingsManager()
    settings = mgr.load()

    console.print(
        Panel(
            f"[bold]Active provider:[/bold] [cyan]{PROVIDER_NAMES.get(settings.active_provider, settings.active_provider)}[/cyan]\n"
            f"[bold]Settings file:[/bold] [dim]{mgr.settings_path}[/dim]",
            title="AI Novel Writer — Settings",
            border_style="blue",
        )
    )

    table = Table(title="Provider Configuration", show_lines=True)
    table.add_column("Provider", style="bold")
    table.add_column("Enabled", justify="center")
    table.add_column("API Key", style="dim")
    table.add_column("Model")
    table.add_column("Endpoint")

    provider_map = {
        "openai": settings.openai,
        "anthropic": settings.anthropic,
        "google_ai": settings.google_ai,
        "openrouter": settings.openrouter,
        "lm_studio": settings.lm_studio,
        "ollama": settings.ollama,
    }

    for key, cfg in provider_map.items():
        name = PROVIDER_NAMES[key]
        enabled = "[green]✓[/green]" if cfg.enabled else "[dim]✗[/dim]"
        api_key = getattr(cfg, "api_key", "")
        masked = (_mask_key(api_key) if api_key else "[dim]not set[/dim]")
        model = getattr(cfg, "model", "") or "[dim]—[/dim]"
        endpoint = getattr(cfg, "endpoint_url", "") or getattr(cfg, "region", "") or "[dim]default[/dim]"
        table.add_row(name, enabled, masked, model, endpoint)

    console.print(table)


# ---------------------------------------------------------------------------
# set-provider — configure a specific AI provider
# ---------------------------------------------------------------------------


@settings_cli.command("set-provider")
@click.argument("provider", type=click.Choice(_PROVIDERS))
@click.option("--api-key", default=None, help="API key for the provider")
@click.option("--model", default=None, help="Model identifier to use")
@click.option("--endpoint", default=None, help="Custom endpoint / base URL")
@click.option("--max-tokens", type=int, default=None, help="Maximum tokens per request")
@click.option("--temperature", type=float, default=None, help="Generation temperature (0.0–2.0)")
@click.option(
    "--enable/--disable",
    default=True,
    show_default=True,
    help="Enable or disable this provider",
)
@click.option(
    "--set-active",
    is_flag=True,
    default=False,
    help="Also set this provider as the active provider",
)
def set_provider(
    provider: str,
    api_key: str | None,
    model: str | None,
    endpoint: str | None,
    max_tokens: int | None,
    temperature: float | None,
    enable: bool,
    set_active: bool,
) -> None:
    """Configure an AI provider.

    PROVIDER must be one of: openai, anthropic, google_ai, openrouter,
    lm_studio, ollama.
    """
    mgr = SettingsManager()
    settings = mgr.load()
    cfg = getattr(settings, provider)

    if api_key is not None:
        cfg.api_key = api_key
    if model is not None:
        cfg.model = model
    if endpoint is not None:
        _set_endpoint(cfg, endpoint)
    if max_tokens is not None and hasattr(cfg, "max_tokens"):
        cfg.max_tokens = max_tokens
    if temperature is not None and hasattr(cfg, "temperature"):
        cfg.temperature = temperature

    cfg.enabled = enable

    if set_active:
        settings.active_provider = provider

    mgr.save(settings)

    name = PROVIDER_NAMES[provider]
    console.print(f"[green]✓[/green] {name} settings updated.")
    if set_active:
        console.print(f"[green]✓[/green] Active provider set to [cyan]{name}[/cyan].")


# ---------------------------------------------------------------------------
# active — set the active provider
# ---------------------------------------------------------------------------


@settings_cli.command("active")
@click.argument("provider", type=click.Choice(_PROVIDERS))
def set_active(provider: str) -> None:
    """Set the active AI provider used for generation."""
    mgr = SettingsManager()
    settings = mgr.load()
    settings.active_provider = provider
    mgr.save(settings)
    name = PROVIDER_NAMES[provider]
    console.print(f"[green]✓[/green] Active provider set to [cyan]{name}[/cyan].")


# ---------------------------------------------------------------------------
# remove — clear / disable a provider
# ---------------------------------------------------------------------------


@settings_cli.command("remove")
@click.argument("provider", type=click.Choice(_PROVIDERS))
@click.option(
    "--clear-key",
    is_flag=True,
    default=False,
    help="Also clear the stored API key",
)
def remove(provider: str, clear_key: bool) -> None:
    """Disable a provider (and optionally clear its API key)."""
    mgr = SettingsManager()
    settings = mgr.load()
    cfg = getattr(settings, provider)
    cfg.enabled = False
    if clear_key and hasattr(cfg, "api_key"):
        cfg.api_key = ""
    if settings.active_provider == provider:
        settings.active_provider = "openai"
        console.print(
            "[yellow]Active provider was reset to openai.[/yellow]"
        )
    mgr.save(settings)
    name = PROVIDER_NAMES[provider]
    console.print(f"[green]✓[/green] {name} disabled.")


# ---------------------------------------------------------------------------
# list-models — display built-in model identifiers
# ---------------------------------------------------------------------------


@settings_cli.command("list-models")
@click.argument("provider", type=click.Choice(_PROVIDERS))
def list_models(provider: str) -> None:
    """List built-in model identifiers for a provider."""
    catalogue: dict[str, list[str]] = {
        "openai": OPENAI_MODELS,
        "anthropic": ANTHROPIC_MODELS,
        "google_ai": GOOGLE_AI_MODELS,
        "openrouter": OPENROUTER_MODELS,
        "lm_studio": [],
        "ollama": OLLAMA_MODELS,
    }
    models = catalogue[provider]
    name = PROVIDER_NAMES[provider]

    if not models:
        console.print(
            f"[yellow]{name}[/yellow] uses locally loaded models. "
            "Set the model identifier with:\n"
            f"  novel-writer settings set-provider {provider} --model <model-name>"
        )
        return

    mgr = SettingsManager()
    settings = mgr.load()
    current_model = getattr(getattr(settings, provider), "model", "")

    table = Table(title=f"{name} — Built-in Models")
    table.add_column("#", style="dim", justify="right")
    table.add_column("Model Identifier", style="cyan")
    table.add_column("", justify="center")

    for i, m in enumerate(models, start=1):
        active_marker = "[green]active[/green]" if m == current_model else ""
        table.add_row(str(i), m, active_marker)

    console.print(table)
    console.print(
        f"\nUse [bold]novel-writer settings set-provider {provider} --model <id>[/bold] to select a model."
    )


# ---------------------------------------------------------------------------
# test — validate connection to a provider
# ---------------------------------------------------------------------------


@settings_cli.command("test")
@click.argument("provider", type=click.Choice(_PROVIDERS))
def test_connection(provider: str) -> None:
    """Test the connection / API key for a provider."""
    mgr = SettingsManager()
    settings = mgr.load()
    name = PROVIDER_NAMES[provider]

    console.print(f"Testing connection to [cyan]{name}[/cyan]…")

    try:
        result = _run_connection_test(settings, provider)
        console.print(f"[green]✓[/green] {result}")
    except ImportError as exc:
        console.print(
            f"[red]✗[/red] Missing package for {name}: {exc}\n"
            "Install the required package and retry."
        )
        raise SystemExit(1) from exc
    except ValueError as exc:
        console.print(
            f"[red]✗[/red] Configuration error for {name}: {exc}\n"
            f"Run: novel-writer settings set-provider {provider} --api-key <key>"
        )
        raise SystemExit(1) from exc
    except Exception as exc:  # noqa: BLE001
        console.print(
            f"[red]✗[/red] Connection test failed for {name}: {exc}\n"
            "Check your API key, endpoint URL, and network connectivity."
        )
        raise SystemExit(1) from exc


# ---------------------------------------------------------------------------
# export — backup settings (without API keys)
# ---------------------------------------------------------------------------


@settings_cli.command("export")
@click.option(
    "--output",
    default="novel-writer-settings-backup.json",
    show_default=True,
    help="Output file path",
)
@click.option(
    "--include-keys",
    is_flag=True,
    default=False,
    help="Include API keys in the export (use with care!)",
)
def export_settings(output: str, include_keys: bool) -> None:
    """Export settings to a JSON backup file.

    API keys are stripped by default.  Use --include-keys to include them
    (treat the resulting file as a secret).
    """
    mgr = SettingsManager()
    out = Path(output)

    if include_keys:
        settings = mgr.load()
        out.write_text(json.dumps(settings.model_dump(), indent=2), encoding="utf-8")
        console.print(
            f"[yellow]⚠[/yellow] API keys included in export. "
            f"Keep [bold]{out}[/bold] secure."
        )
    else:
        mgr.export_safe(out)

    console.print(f"[green]✓[/green] Settings exported to [bold]{out}[/bold].")


# ---------------------------------------------------------------------------
# import — restore settings from a backup
# ---------------------------------------------------------------------------


@settings_cli.command("import")
@click.option(
    "--input",
    "input_file",
    required=True,
    help="Path to the settings backup file",
)
def import_settings(input_file: str) -> None:
    """Import settings from a JSON backup file.

    Existing API keys are preserved when the backup does not include them.
    """
    input_path = Path(input_file)
    if not input_path.exists():
        console.print(f"[red]Error:[/red] File not found: {input_path}")
        raise SystemExit(1)

    mgr = SettingsManager()
    try:
        mgr.import_from(input_path)
    except (json.JSONDecodeError, KeyError, ValueError) as exc:
        console.print(f"[red]Error:[/red] Invalid settings file: {exc}")
        raise SystemExit(1) from exc

    console.print(f"[green]✓[/green] Settings imported from [bold]{input_path}[/bold].")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _mask_key(key: str) -> str:
    """Return a masked version of *key* for display."""
    if len(key) <= 8:
        return "***"
    return key[:4] + "…" + key[-4:]


def _set_endpoint(cfg: object, endpoint: str) -> None:
    """Set the endpoint on *cfg*, supporting different field names."""
    if hasattr(cfg, "endpoint_url"):
        cfg.endpoint_url = endpoint  # type: ignore[attr-defined]
    elif hasattr(cfg, "region"):
        cfg.region = endpoint  # type: ignore[attr-defined]


def _run_connection_test(settings: AppSettings, provider: str) -> str:
    """Perform a lightweight API ping and return a success message."""
    if provider == "openai":
        return _test_openai(settings)
    if provider == "anthropic":
        return _test_anthropic(settings)
    if provider == "google_ai":
        return _test_google_ai(settings)
    if provider == "openrouter":
        return _test_openrouter(settings)
    if provider == "lm_studio":
        return _test_lm_studio(settings)
    if provider == "ollama":
        return _test_ollama(settings)
    raise ValueError(f"Unknown provider: {provider}")


def _test_openai(settings: AppSettings) -> str:
    """Test OpenAI connectivity by listing models."""
    from openai import OpenAI

    cfg = settings.openai
    if not cfg.api_key:
        raise ValueError("No API key configured for OpenAI.")
    client = OpenAI(
        api_key=cfg.api_key,
        base_url=cfg.endpoint_url or None,
    )
    models = client.models.list()
    count = sum(1 for _ in models)
    return f"OpenAI connection successful — {count} model(s) available."


def _test_anthropic(settings: AppSettings) -> str:
    """Test Anthropic connectivity."""
    try:
        import anthropic  # type: ignore[import]
    except ImportError as exc:
        raise ImportError(
            "The 'anthropic' package is not installed. "
            "Run: pip install anthropic"
        ) from exc
    cfg = settings.anthropic
    if not cfg.api_key:
        raise ValueError("No API key configured for Anthropic.")
    client = anthropic.Anthropic(api_key=cfg.api_key)
    # Minimal API check — list models endpoint
    response = client.models.list()
    count = len(response.data) if hasattr(response, "data") else 0
    return f"Anthropic connection successful — {count} model(s) available."


def _test_google_ai(settings: AppSettings) -> str:
    """Test Google AI connectivity."""
    try:
        import google.generativeai as genai  # type: ignore[import]
    except ImportError as exc:
        raise ImportError(
            "The 'google-generativeai' package is not installed. "
            "Run: pip install google-generativeai"
        ) from exc
    cfg = settings.google_ai
    if not cfg.api_key:
        raise ValueError("No API key configured for Google AI.")
    genai.configure(api_key=cfg.api_key)
    models = list(genai.list_models())
    return f"Google AI connection successful — {len(models)} model(s) available."


def _test_openrouter(settings: AppSettings) -> str:
    """Test OpenRouter connectivity (OpenAI-compatible endpoint)."""
    from openai import OpenAI

    cfg = settings.openrouter
    if not cfg.api_key:
        raise ValueError("No API key configured for OpenRouter.")
    client = OpenAI(
        api_key=cfg.api_key,
        base_url="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": cfg.site_url or "https://github.com/FutureAIGuide/AI-Novel-Writer",
            "X-Title": cfg.site_name or "AI Novel Writer",
        },
    )
    models = client.models.list()
    count = sum(1 for _ in models)
    return f"OpenRouter connection successful — {count} model(s) available."


def _test_lm_studio(settings: AppSettings) -> str:
    """Test LM Studio connectivity."""
    from openai import OpenAI

    cfg = settings.lm_studio
    endpoint = cfg.endpoint_url or "http://localhost:1234/v1"
    client = OpenAI(api_key="lm-studio", base_url=endpoint)
    models = client.models.list()
    count = sum(1 for _ in models)
    return (
        f"LM Studio connection successful at {endpoint} — {count} model(s) loaded."
    )


def _test_ollama(settings: AppSettings) -> str:
    """Test Ollama connectivity."""
    import urllib.request

    cfg = settings.ollama
    base_url = (cfg.endpoint_url or "http://localhost:11434").rstrip("/")
    url = f"{base_url}/api/tags"
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:  # noqa: S310
            data = json.loads(resp.read())
        models = data.get("models", [])
        return (
            f"Ollama connection successful at {base_url} — "
            f"{len(models)} model(s) available: "
            + ", ".join(m.get("name", "") for m in models[:5])
        )
    except OSError as exc:
        raise ConnectionError(
            f"Could not reach Ollama at {base_url}. Is it running?"
        ) from exc

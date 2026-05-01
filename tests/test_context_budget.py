"""Tests for context budgeting helpers."""

from novel_writer.utils.context_budget import (
    build_context_pack,
    default_budget_for_provider,
    estimate_tokens,
)


def test_estimate_tokens_empty() -> None:
    assert estimate_tokens("") == 0


def test_default_budget_local_vs_cloud() -> None:
    assert default_budget_for_provider("ollama") < default_budget_for_provider("openai")


def test_build_context_pack_no_trim_when_small() -> None:
    pack = build_context_pack(
        "Title: X\nGenre: Y",
        "Alice: hero.",
        "",
        budget_tokens=8000,
    )
    assert "Title: X" in pack.story_block
    assert not pack.trimmed


def test_build_context_pack_trims_large_characters() -> None:
    long_chars = "\n\n".join(f"Char{i}: " + ("word " * 200) for i in range(30))
    pack = build_context_pack(
        "Short story context.",
        long_chars,
        "",
        budget_tokens=1500,
    )
    assert pack.trimmed
    assert pack.estimated_prompt_tokens <= pack.budget_tokens + 50

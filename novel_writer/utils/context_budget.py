"""Trim story context strings to fit an approximate token budget for local models."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable

# Rough heuristic: English prose ~ 0.75 tokens per word for budgeting (conservative).
_CHARS_PER_TOKEN_EST: float = 4.0


def estimate_tokens(text: str) -> int:
    """Return a rough token count estimate for *text* (no network, no tiktoken)."""
    if not text:
        return 0
    return max(1, int(len(text) / _CHARS_PER_TOKEN_EST))


def _truncate_words(text: str, max_words: int) -> str:
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]) + "…"


@dataclass
class ContextPack:
    """Packed context for AI prompts with usage metadata."""

    story_block: str
    characters_block: str
    previous_chapters_block: str
    estimated_prompt_tokens: int
    budget_tokens: int
    trimmed: bool


def default_budget_for_provider(provider: str) -> int:
    """Default context budget (estimated tokens) when studio_context_budget_tokens is 0."""
    if provider in ("lm_studio", "ollama"):
        return 6000
    return 12000


def build_context_pack(
    story_block: str,
    characters_block: str,
    previous_chapters_block: str,
    budget_tokens: int,
    reserve_for_instructions: int = 1500,
) -> ContextPack:
    """Fit *story_block*, *characters_block*, and *previous_chapters_block* under *budget_tokens*.

    Priority: keep *story_block* intact if possible, then shrink *characters_block*, then
    *previous_chapters_block* (oldest summaries dropped first).
    """
    budget = max(512, budget_tokens - max(0, reserve_for_instructions))
    trimmed = False

    def total(s: str, c: str, p: str) -> int:
        return estimate_tokens(s) + estimate_tokens(c) + estimate_tokens(p)

    s, c, p = story_block, characters_block, previous_chapters_block
    while total(s, c, p) > budget and c:
        # Trim characters: remove trailing character blocks (double newline separated)
        parts = re.split(r"\n\n+", c)
        if len(parts) > 1:
            c = "\n\n".join(parts[:-1])
            trimmed = True
        else:
            c = _truncate_words(c, max(20, int(len(c.split()) * 0.7)))
            trimmed = True
        if total(s, c, p) <= budget:
            break

    while total(s, c, p) > budget and p:
        paras = p.split("\n\n")
        if len(paras) > 1:
            p = "\n\n".join(paras[1:])  # drop oldest block
            trimmed = True
        else:
            p = _truncate_words(p, max(30, int(len(p.split()) * 0.6)))
            trimmed = True
        if total(s, c, p) <= budget:
            break

    while total(s, c, p) > budget and s:
        s = _truncate_words(s, max(40, int(len(s.split()) * 0.75)))
        trimmed = True
        if total(s, c, p) <= budget:
            break

    est = total(s, c, p)
    return ContextPack(
        story_block=s,
        characters_block=c,
        previous_chapters_block=p,
        estimated_prompt_tokens=est,
        budget_tokens=budget,
        trimmed=trimmed,
    )


def story_context_strings(
    story_context_fn: Callable[[], str],
    characters_context_fn: Callable[[], str],
    previous_chapters_fn: Callable[[], str],
    budget_tokens: int,
    reserve_for_instructions: int = 1500,
) -> ContextPack:
    """Convenience wrapper using callables (e.g. Story methods)."""
    return build_context_pack(
        story_context_fn(),
        characters_context_fn(),
        previous_chapters_fn(),
        budget_tokens=budget_tokens,
        reserve_for_instructions=reserve_for_instructions,
    )

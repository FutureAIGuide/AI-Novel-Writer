"""Selection-based rewrite / expand / shorten / tone edits (Sudowrite-style micro-ops)."""

from __future__ import annotations

from collections.abc import Iterator

from novel_writer.generators.base import BaseGenerator
from novel_writer.models.story import Story
from novel_writer.utils.context_budget import ContextPack, build_context_pack, default_budget_for_provider


_EDIT_SYSTEM = (
    "You are a skilled fiction editor and co-author. "
    "Preserve continuity with the story bible. Output only the revised passage "
    "with no preamble or meta-commentary unless asked."
)


class SelectionEditor(BaseGenerator):
    """Rewrite, expand, shorten, or adjust tone for a selected excerpt."""

    def _pack_for_selection(self, story: Story, before_chapter: int, budget_tokens: int | None) -> ContextPack:
        previous = story.previous_chapters_context(before_chapter=before_chapter)
        prev_block = f"Previous chapters (for continuity):\n{previous}\n\n" if previous else ""
        budget = budget_tokens if budget_tokens is not None else default_budget_for_provider(self.provider)
        return build_context_pack(
            story.story_context(),
            story.characters_context(),
            prev_block,
            budget_tokens=budget,
            reserve_for_instructions=2000,
        )

    def transform_selection(
        self,
        story: Story,
        selected_text: str,
        operation: str,
        *,
        before_chapter: int = 1,
        context_budget_tokens: int | None = None,
        extra_instruction: str = "",
    ) -> str:
        """Apply *operation* to *selected_text*.

        *operation* is one of: rewrite, expand, shorten, tone_dramatic, tone_subtle.
        """
        pack = self._pack_for_selection(story, before_chapter, context_budget_tokens)
        op = operation.lower().strip()
        if op == "rewrite":
            task = "Rewrite the passage for clarity, rhythm, and voice while preserving meaning and plot."
        elif op == "expand":
            task = "Expand the passage with sensory detail, interiority, and scene texture. Add roughly 50–100% more length."
        elif op == "shorten":
            task = "Tighten the passage: remove redundancy, sharpen sentences, cut roughly 30–50% length without losing key beats."
        elif op == "tone_dramatic":
            task = "Heighten dramatic tension and stakes; keep events the same unless minor tweaks improve impact."
        elif op == "tone_subtle":
            task = "Soften and refine the tone; understated emotion; keep events the same unless minor tweaks improve nuance."
        else:
            raise ValueError(f"Unknown operation: {operation!r}")

        extra = f"\nAuthor note: {extra_instruction}\n" if extra_instruction else ""
        user = (
            f"Novel: \"{story.title}\"\n\n"
            f"Story bible:\n{pack.story_block}\n\n"
            f"Characters:\n{pack.characters_block}\n\n"
            f"{pack.previous_chapters_block}"
            f"Selected passage to edit:\n---\n{selected_text}\n---\n\n"
            f"Task: {task}{extra}\n"
            "Return only the edited passage."
        )
        return self._chat(_EDIT_SYSTEM, user)

    def transform_selection_stream(
        self,
        story: Story,
        selected_text: str,
        operation: str,
        *,
        before_chapter: int = 1,
        context_budget_tokens: int | None = None,
        extra_instruction: str = "",
    ) -> Iterator[str]:
        """Stream the edited passage (OpenAI-compatible providers stream token-wise)."""
        pack = self._pack_for_selection(story, before_chapter, context_budget_tokens)
        op = operation.lower().strip()
        if op == "rewrite":
            task = "Rewrite the passage for clarity, rhythm, and voice while preserving meaning and plot."
        elif op == "expand":
            task = "Expand the passage with sensory detail, interiority, and scene texture. Add roughly 50–100% more length."
        elif op == "shorten":
            task = "Tighten the passage: remove redundancy, sharpen sentences, cut roughly 30–50% length without losing key beats."
        elif op == "tone_dramatic":
            task = "Heighten dramatic tension and stakes; keep events the same unless minor tweaks improve impact."
        elif op == "tone_subtle":
            task = "Soften and refine the tone; understated emotion; keep events the same unless minor tweaks improve nuance."
        else:
            raise ValueError(f"Unknown operation: {operation!r}")

        extra = f"\nAuthor note: {extra_instruction}\n" if extra_instruction else ""
        user = (
            f"Novel: \"{story.title}\"\n\n"
            f"Story bible:\n{pack.story_block}\n\n"
            f"Characters:\n{pack.characters_block}\n\n"
            f"{pack.previous_chapters_block}"
            f"Selected passage to edit:\n---\n{selected_text}\n---\n\n"
            f"Task: {task}{extra}\n"
            "Return only the edited passage."
        )
        yield from self.stream_chat(_EDIT_SYSTEM, user)

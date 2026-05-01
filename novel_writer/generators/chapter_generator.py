"""Chapter AI generator for AI Novel Writer."""

from __future__ import annotations

from collections.abc import Iterator

from novel_writer.generators.base import BaseGenerator
from novel_writer.models.chapter import Chapter
from novel_writer.models.story import Story
from novel_writer.utils.context_budget import build_context_pack, default_budget_for_provider


_SYSTEM_PROMPT = (
    "You are a skilled novelist writing a full-length book. "
    "Write immersive, vivid prose that matches the established tone, voice, and style "
    "of the story. Show, don't tell. Use dialogue, action, and sensory detail. "
    "End chapters with a hook that compels the reader onward."
)


def _tail_words(text: str, max_words: int = 2500) -> str:
    """Keep the end of a long chapter for continuation prompts."""
    words = text.split()
    if len(words) <= max_words:
        return text
    return "…\n" + " ".join(words[-max_words:])


class ChapterGenerator(BaseGenerator):
    """Generates chapter content using the configured AI provider."""

    def _context_budget_tokens(self) -> int:
        if self._app_settings is not None and self._app_settings.studio_context_budget_tokens > 0:
            return self._app_settings.studio_context_budget_tokens
        return default_budget_for_provider(self.provider)

    def _packed_story_blocks(self, story: Story, before_chapter: int) -> tuple[str, str, str]:
        previous = story.previous_chapters_context(before_chapter=before_chapter)
        prev_block = f"Previous chapters (for continuity):\n{previous}\n\n" if previous else ""
        pack = build_context_pack(
            story.story_context(),
            story.characters_context(),
            prev_block,
            budget_tokens=self._context_budget_tokens(),
            reserve_for_instructions=2200,
        )
        return pack.story_block, pack.characters_block, pack.previous_chapters_block

    def generate_chapter(
        self,
        story: Story,
        chapter_number: int,
        chapter_title: str = "",
        chapter_summary: str = "",
        extra_instructions: str = "",
    ) -> Chapter:
        """Generate the full prose content for a chapter.

        Args:
            story: The Story object with context, characters, and previous chapters.
            chapter_number: The chapter number to generate.
            chapter_title: Optional title for the chapter.
            chapter_summary: A brief summary of what should happen in this chapter.
            extra_instructions: Any additional author instructions.

        Returns:
            A Chapter instance populated with generated content.
        """
        story_block, characters_block, previous_block = self._packed_story_blocks(
            story, before_chapter=chapter_number
        )
        extra_block = (
            f"Additional instructions: {extra_instructions}\n\n" if extra_instructions else ""
        )
        title_hint = f'Chapter title: "{chapter_title}"\n' if chapter_title else ""
        summary_hint = (
            f"Chapter summary / what must happen:\n{chapter_summary}\n\n"
            if chapter_summary
            else ""
        )

        user_prompt = (
            f"Write Chapter {chapter_number} of the novel \"{story.title}\".\n\n"
            f"Story context:\n{story_block}\n\n"
            f"Characters:\n{characters_block}\n\n"
            f"{previous_block}"
            f"{title_hint}"
            f"{summary_hint}"
            f"{extra_block}"
            "Write the full chapter in prose. Aim for 800-1500 words unless instructed otherwise."
        )

        content = self._chat(_SYSTEM_PROMPT, user_prompt)
        return Chapter(
            number=chapter_number,
            title=chapter_title,
            summary=chapter_summary,
            content=content,
        )

    def generate_chapter_stream(
        self,
        story: Story,
        chapter_number: int,
        chapter_title: str = "",
        chapter_summary: str = "",
        extra_instructions: str = "",
    ) -> Iterator[str]:
        """Stream chapter prose (OpenAI-compatible providers yield tokens)."""
        story_block, characters_block, previous_block = self._packed_story_blocks(
            story, before_chapter=chapter_number
        )
        extra_block = (
            f"Additional instructions: {extra_instructions}\n\n" if extra_instructions else ""
        )
        title_hint = f'Chapter title: "{chapter_title}"\n' if chapter_title else ""
        summary_hint = (
            f"Chapter summary / what must happen:\n{chapter_summary}\n\n"
            if chapter_summary
            else ""
        )
        user_prompt = (
            f"Write Chapter {chapter_number} of the novel \"{story.title}\".\n\n"
            f"Story context:\n{story_block}\n\n"
            f"Characters:\n{characters_block}\n\n"
            f"{previous_block}"
            f"{title_hint}"
            f"{summary_hint}"
            f"{extra_block}"
            "Write the full chapter in prose. Aim for 800-1500 words unless instructed otherwise."
        )
        yield from self.stream_chat(_SYSTEM_PROMPT, user_prompt)

    def continue_chapter(self, story: Story, chapter: Chapter, continuation_hint: str = "") -> str:
        """Continue writing from where a chapter left off.

        Args:
            story: The Story context.
            chapter: The chapter to continue.
            continuation_hint: Optional hint about where the story should go.

        Returns:
            Additional prose to append to the chapter.
        """
        story_block, characters_block, previous_block = self._packed_story_blocks(
            story, before_chapter=chapter.number
        )
        hint_block = f"Direction hint: {continuation_hint}\n\n" if continuation_hint else ""
        chapter_excerpt = _tail_words(chapter.content, max_words=2500)
        user_prompt = (
            f"Continue writing the following chapter of \"{story.title}\".\n\n"
            f"Story context:\n{story_block}\n\n"
            f"Characters:\n{characters_block}\n\n"
            f"{previous_block}"
            f"Chapter so far:\n{chapter_excerpt}\n\n"
            f"{hint_block}"
            "Seamlessly continue from where the text ends. Write 500-800 more words."
        )
        return self._chat(_SYSTEM_PROMPT, user_prompt)

    def continue_chapter_stream(
        self, story: Story, chapter: Chapter, continuation_hint: str = ""
    ) -> Iterator[str]:
        """Stream continuation prose."""
        story_block, characters_block, previous_block = self._packed_story_blocks(
            story, before_chapter=chapter.number
        )
        hint_block = f"Direction hint: {continuation_hint}\n\n" if continuation_hint else ""
        chapter_excerpt = _tail_words(chapter.content, max_words=2500)
        user_prompt = (
            f"Continue writing the following chapter of \"{story.title}\".\n\n"
            f"Story context:\n{story_block}\n\n"
            f"Characters:\n{characters_block}\n\n"
            f"{previous_block}"
            f"Chapter so far:\n{chapter_excerpt}\n\n"
            f"{hint_block}"
            "Seamlessly continue from where the text ends. Write 500-800 more words."
        )
        yield from self.stream_chat(_SYSTEM_PROMPT, user_prompt)

    def generate_chapter_summary(self, chapter: Chapter) -> str:
        """Generate a concise summary of a completed chapter.

        Args:
            chapter: A chapter with content already written.

        Returns:
            A 2-3 sentence summary string.
        """
        excerpt = _tail_words(chapter.content, max_words=4000)
        user_prompt = (
            f"Summarize the following chapter in 2-3 sentences, "
            "capturing the key events and emotional beats:\n\n"
            f"{excerpt}"
        )
        system = (
            "You are a literary editor. Write concise, accurate chapter summaries "
            "that capture plot points, character moments, and narrative tension."
        )
        return self._chat(system, user_prompt)

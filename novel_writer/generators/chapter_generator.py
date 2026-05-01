"""Chapter AI generator for AI Novel Writer."""

from __future__ import annotations

from novel_writer.generators.base import BaseGenerator
from novel_writer.models.chapter import Chapter
from novel_writer.models.story import Story


_SYSTEM_PROMPT = (
    "You are a skilled novelist writing a full-length book. "
    "Write immersive, vivid prose that matches the established tone, voice, and style "
    "of the story. Show, don't tell. Use dialogue, action, and sensory detail. "
    "End chapters with a hook that compels the reader onward."
)


class ChapterGenerator(BaseGenerator):
    """Generates chapter content using the OpenAI API."""

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
        previous = story.previous_chapters_context(before_chapter=chapter_number)
        previous_block = (
            f"Previous chapters (for continuity):\n{previous}\n\n" if previous else ""
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
            f"Story context:\n{story.story_context()}\n\n"
            f"Characters:\n{story.characters_context()}\n\n"
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

    def continue_chapter(self, story: Story, chapter: Chapter, continuation_hint: str = "") -> str:
        """Continue writing from where a chapter left off.

        Args:
            story: The Story context.
            chapter: The chapter to continue.
            continuation_hint: Optional hint about where the story should go.

        Returns:
            Additional prose to append to the chapter.
        """
        hint_block = f"Direction hint: {continuation_hint}\n\n" if continuation_hint else ""
        user_prompt = (
            f"Continue writing the following chapter of \"{story.title}\".\n\n"
            f"Story context:\n{story.story_context()}\n\n"
            f"Characters:\n{story.characters_context()}\n\n"
            f"Chapter so far:\n{chapter.content}\n\n"
            f"{hint_block}"
            "Seamlessly continue from where the text ends. Write 500-800 more words."
        )
        return self._chat(_SYSTEM_PROMPT, user_prompt)

    def generate_chapter_summary(self, chapter: Chapter) -> str:
        """Generate a concise summary of a completed chapter.

        Args:
            chapter: A chapter with content already written.

        Returns:
            A 2-3 sentence summary string.
        """
        user_prompt = (
            f"Summarize the following chapter in 2-3 sentences, "
            "capturing the key events and emotional beats:\n\n"
            f"{chapter.content}"
        )
        system = (
            "You are a literary editor. Write concise, accurate chapter summaries "
            "that capture plot points, character moments, and narrative tension."
        )
        return self._chat(system, user_prompt)

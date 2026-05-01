"""Story-level AI generator for AI Novel Writer."""

from __future__ import annotations

from novel_writer.generators.base import BaseGenerator
from novel_writer.models.story import Story


_SYSTEM_PROMPT = (
    "You are a professional novelist and creative writing consultant. "
    "You help authors develop compelling story ideas, rich settings, and "
    "tight narrative structures. Be specific, vivid, and original."
)


class StoryGenerator(BaseGenerator):
    """Generates high-level story elements using the OpenAI API."""

    def generate_premise(self, genre: str, keywords: str = "") -> str:
        """Generate a compelling one-paragraph story premise.

        Args:
            genre: The genre of the story (e.g. "dark fantasy").
            keywords: Optional comma-separated themes or keywords to incorporate.

        Returns:
            A one-paragraph premise string.
        """
        keyword_hint = f" Incorporate these themes/keywords: {keywords}." if keywords else ""
        user_prompt = (
            f"Generate an original and compelling one-paragraph premise for a {genre} novel."
            f"{keyword_hint} The premise should establish the protagonist, the central conflict, "
            "and the stakes."
        )
        return self._chat(_SYSTEM_PROMPT, user_prompt)

    def generate_outline(self, story: Story, num_chapters: int = 10) -> str:
        """Generate a chapter-by-chapter outline for the story.

        Args:
            story: The Story object containing title, genre, premise, and characters.
            num_chapters: Target number of chapters.

        Returns:
            A formatted outline string.
        """
        context = story.story_context()
        characters = story.characters_context()
        user_prompt = (
            f"Based on the following story details, write a {num_chapters}-chapter outline. "
            "For each chapter provide: chapter number, a short title, and a 2-3 sentence summary "
            "of key events.\n\n"
            f"Story Details:\n{context}\n\n"
            f"Characters:\n{characters}\n\n"
            f"Premise:\n{story.premise}"
        )
        return self._chat(_SYSTEM_PROMPT, user_prompt)

    def generate_setting(self, genre: str, premise: str) -> str:
        """Generate a vivid setting description.

        Args:
            genre: The genre of the story.
            premise: The story premise.

        Returns:
            A paragraph describing the world/setting.
        """
        user_prompt = (
            f"Create a vivid, immersive setting for a {genre} novel with the following premise:\n"
            f"{premise}\n\n"
            "Describe the world, time period, atmosphere, and any unique rules or features "
            "of this setting in 2-3 paragraphs."
        )
        return self._chat(_SYSTEM_PROMPT, user_prompt)

    def generate_style_notes(self, genre: str, influences: str = "") -> str:
        """Generate authorial style notes.

        Args:
            genre: The genre of the story.
            influences: Optional comma-separated list of author/book influences.

        Returns:
            Style notes as a string.
        """
        influence_hint = f" Author/book influences: {influences}." if influences else ""
        user_prompt = (
            f"Suggest detailed writing style notes for a {genre} novel.{influence_hint} "
            "Cover: narrative POV, tense, prose style, pacing, dialogue approach, and tone."
        )
        return self._chat(_SYSTEM_PROMPT, user_prompt)

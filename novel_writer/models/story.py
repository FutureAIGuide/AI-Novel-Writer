"""Story model for AI Novel Writer."""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field

from novel_writer.models.character import Character
from novel_writer.models.chapter import Chapter


class Story(BaseModel):
    """Represents a full novel/story project."""

    title: str = Field(..., description="The title of the novel")
    genre: str = Field(default="", description="Genre(s), e.g. 'fantasy', 'sci-fi thriller'")
    setting: str = Field(default="", description="Time period and world description")
    premise: str = Field(default="", description="The core premise / logline of the story")
    outline: str = Field(default="", description="High-level plot outline")
    characters: List[Character] = Field(default_factory=list)
    chapters: List[Chapter] = Field(default_factory=list)
    style_notes: str = Field(
        default="", description="Authorial style, tone, and POV preferences"
    )

    # ------------------------------------------------------------------ #
    #  Convenience helpers                                                  #
    # ------------------------------------------------------------------ #

    def add_character(self, character: Character) -> None:
        """Add a character to the story."""
        self.characters.append(character)

    def add_chapter(self, chapter: Chapter) -> None:
        """Add a chapter and keep them sorted by number."""
        self.chapters.append(chapter)
        self.chapters.sort(key=lambda c: c.number)

    def get_chapter(self, number: int) -> Optional[Chapter]:
        """Return the chapter with the given number, or None."""
        for chapter in self.chapters:
            if chapter.number == number:
                return chapter
        return None

    @property
    def total_word_count(self) -> int:
        """Return cumulative word count across all chapters."""
        return sum(c.word_count for c in self.chapters)

    def previous_chapters_context(self, before_chapter: int, max_chapters: int = 3) -> str:
        """Return a summary of the most recent chapters before *before_chapter*."""
        relevant = [c for c in self.chapters if c.number < before_chapter]
        recent = relevant[-max_chapters:]
        if not recent:
            return ""
        blocks = [c.to_summary_block() for c in recent]
        return "\n\n".join(blocks)

    def characters_context(self) -> str:
        """Return a formatted string of all characters for use in prompts."""
        if not self.characters:
            return "No characters defined yet."
        return "\n\n".join(c.to_prompt_context() for c in self.characters)

    def story_context(self) -> str:
        """Return a concise story context block for AI prompts."""
        parts = [f'Title: "{self.title}"']
        if self.genre:
            parts.append(f"Genre: {self.genre}")
        if self.setting:
            parts.append(f"Setting: {self.setting}")
        if self.premise:
            parts.append(f"Premise: {self.premise}")
        if self.style_notes:
            parts.append(f"Style: {self.style_notes}")
        return "\n".join(parts)

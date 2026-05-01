"""Chapter model for AI Novel Writer."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Chapter(BaseModel):
    """Represents a single chapter in a novel."""

    number: int = Field(..., description="Chapter number (1-indexed)")
    title: str = Field(default="", description="Chapter title")
    summary: str = Field(default="", description="Short summary of what happens in this chapter")
    content: str = Field(default="", description="Full prose content of the chapter")
    notes: str = Field(default="", description="Author notes or revision flags for this chapter")

    @property
    def word_count(self) -> int:
        """Return the approximate word count of the chapter content."""
        return len(self.content.split()) if self.content else 0

    def display_title(self) -> str:
        """Return a formatted display title."""
        if self.title:
            return f"Chapter {self.number}: {self.title}"
        return f"Chapter {self.number}"

    def to_summary_block(self) -> str:
        """Return a compact summary block for use in AI prompts."""
        header = self.display_title()
        body = self.summary or (self.content[:300] + "…" if self.content else "No content yet.")
        return f"{header}\n{body}"

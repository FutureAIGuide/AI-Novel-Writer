"""Character model for AI Novel Writer."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Character(BaseModel):
    """Represents a character in a novel."""

    name: str = Field(..., description="The character's full name")
    role: str = Field(..., description="The character's role, e.g. 'protagonist', 'antagonist'")
    description: str = Field(default="", description="Physical appearance and personality description")
    backstory: str = Field(default="", description="The character's background and history")
    motivation: str = Field(default="", description="What drives the character")
    arc: str = Field(default="", description="The character's development arc throughout the story")

    def summary(self) -> str:
        """Return a short summary suitable for use in AI prompts."""
        parts = [f"{self.name} ({self.role})"]
        if self.description:
            parts.append(self.description)
        if self.motivation:
            parts.append(f"Motivation: {self.motivation}")
        return ". ".join(parts)

    def to_prompt_context(self) -> str:
        """Return a detailed context string for AI prompts."""
        lines = [f"Name: {self.name}", f"Role: {self.role}"]
        if self.description:
            lines.append(f"Description: {self.description}")
        if self.backstory:
            lines.append(f"Backstory: {self.backstory}")
        if self.motivation:
            lines.append(f"Motivation: {self.motivation}")
        if self.arc:
            lines.append(f"Arc: {self.arc}")
        return "\n".join(lines)

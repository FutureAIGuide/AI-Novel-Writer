"""Character AI generator for AI Novel Writer."""

from __future__ import annotations

import json

from novel_writer.generators.base import BaseGenerator
from novel_writer.models.character import Character
from novel_writer.models.story import Story


_SYSTEM_PROMPT = (
    "You are an expert fiction writer specializing in character development. "
    "You create psychologically rich, believable characters with clear motivations, "
    "compelling backstories, and meaningful character arcs."
)


class CharacterGenerator(BaseGenerator):
    """Generates character profiles using the OpenAI API."""

    def generate_character(
        self,
        story: Story,
        role: str,
        hints: str = "",
    ) -> Character:
        """Generate a full character profile.

        Args:
            story: The Story object providing genre/setting context.
            role: The character's role, e.g. 'protagonist' or 'mentor'.
            hints: Optional free-text hints about the character.

        Returns:
            A populated Character instance.
        """
        hint_text = f"Additional hints: {hints}\n" if hints else ""
        user_prompt = (
            f"Create a detailed character for a {story.genre} novel titled \"{story.title}\".\n"
            f"Role: {role}\n"
            f"{hint_text}"
            f"Story premise: {story.premise}\n\n"
            "Return a JSON object with these exact keys:\n"
            "  name, role, description, backstory, motivation, arc\n"
            "All values must be strings. Do not include markdown fences."
        )
        raw = self._chat(_SYSTEM_PROMPT, user_prompt)
        data = self._parse_json(raw)
        data.setdefault("role", role)
        return Character(**data)

    def generate_relationship(
        self,
        character_a: Character,
        character_b: Character,
        story: Story,
    ) -> str:
        """Describe the relationship between two characters.

        Args:
            character_a: First character.
            character_b: Second character.
            story: Story context.

        Returns:
            A paragraph describing their relationship dynamics.
        """
        user_prompt = (
            f"In the {story.genre} novel \"{story.title}\", describe the relationship between:\n\n"
            f"{character_a.to_prompt_context()}\n\n"
            f"and\n\n"
            f"{character_b.to_prompt_context()}\n\n"
            "Write 2-3 paragraphs covering: how they met, their dynamic, "
            "tensions or bonds, and how the relationship might evolve."
        )
        return self._chat(_SYSTEM_PROMPT, user_prompt)

    @staticmethod
    def _parse_json(raw: str) -> dict:
        """Parse a JSON object from the raw AI response."""
        raw = raw.strip()
        # Strip accidental markdown code fences
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Could not parse character JSON from AI response.\n"
                f"Response was:\n{raw}"
            ) from exc

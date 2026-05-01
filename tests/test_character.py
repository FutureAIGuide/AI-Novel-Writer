"""Tests for the Character model."""

import pytest
from novel_writer.models.character import Character


@pytest.fixture
def protagonist() -> Character:
    return Character(
        name="Elara Voss",
        role="protagonist",
        description="A sharp-tongued alchemist with silver-streaked hair.",
        backstory="Raised in the war-torn borderlands, she taught herself magic from stolen texts.",
        motivation="To uncover the truth behind her mentor's disappearance.",
        arc="From self-reliant loner to reluctant leader.",
    )


class TestCharacterModel:
    def test_creation(self, protagonist: Character) -> None:
        assert protagonist.name == "Elara Voss"
        assert protagonist.role == "protagonist"

    def test_summary_contains_name_and_role(self, protagonist: Character) -> None:
        summary = protagonist.summary()
        assert "Elara Voss" in summary
        assert "protagonist" in summary

    def test_summary_contains_motivation(self, protagonist: Character) -> None:
        summary = protagonist.summary()
        assert "Motivation" in summary

    def test_to_prompt_context_contains_all_fields(self, protagonist: Character) -> None:
        ctx = protagonist.to_prompt_context()
        for field in ["Elara Voss", "protagonist", "alchemist", "mentor", "loner"]:
            assert field in ctx

    def test_defaults(self) -> None:
        char = Character(name="Ghost", role="mystery")
        assert char.description == ""
        assert char.backstory == ""
        assert char.motivation == ""
        assert char.arc == ""

    def test_summary_minimal(self) -> None:
        char = Character(name="Ghost", role="mystery")
        summary = char.summary()
        assert "Ghost" in summary
        assert "mystery" in summary
        # No motivation section expected
        assert "Motivation" not in summary

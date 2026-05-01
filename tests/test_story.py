"""Tests for the Story model."""

import pytest
from novel_writer.models.story import Story
from novel_writer.models.character import Character
from novel_writer.models.chapter import Chapter


@pytest.fixture
def base_story() -> Story:
    return Story(
        title="Ashes of the Forgotten",
        genre="dark fantasy",
        setting="A crumbling empire at the edge of a dying sun.",
        premise="An exiled alchemist must destroy the god-king who murdered her mentor.",
        style_notes="Third-person limited, past tense, literary prose with gothic undertones.",
    )


@pytest.fixture
def protagonist() -> Character:
    return Character(
        name="Elara Voss",
        role="protagonist",
        description="Sharp-tongued alchemist.",
        motivation="Avenge her mentor.",
    )


@pytest.fixture
def antagonist() -> Character:
    return Character(
        name="The God-King",
        role="antagonist",
        description="Immortal tyrant.",
        motivation="Eternal dominion.",
    )


@pytest.fixture
def chapter_one() -> Chapter:
    return Chapter(
        number=1,
        title="The Burning City",
        summary="Elara escapes the siege.",
        content="Flames licked the sky as Elara ran.",
    )


@pytest.fixture
def chapter_two() -> Chapter:
    return Chapter(
        number=2,
        title="The Road North",
        summary="Elara journeys to the old ruins.",
        content="Rain turned the road to mud.",
    )


class TestStoryModel:
    def test_creation(self, base_story: Story) -> None:
        assert base_story.title == "Ashes of the Forgotten"
        assert base_story.genre == "dark fantasy"

    def test_add_character(self, base_story: Story, protagonist: Character) -> None:
        base_story.add_character(protagonist)
        assert len(base_story.characters) == 1
        assert base_story.characters[0].name == "Elara Voss"

    def test_add_chapter_sorted(
        self,
        base_story: Story,
        chapter_two: Chapter,
        chapter_one: Chapter,
    ) -> None:
        base_story.add_chapter(chapter_two)
        base_story.add_chapter(chapter_one)
        assert base_story.chapters[0].number == 1
        assert base_story.chapters[1].number == 2

    def test_get_chapter(self, base_story: Story, chapter_one: Chapter) -> None:
        base_story.add_chapter(chapter_one)
        found = base_story.get_chapter(1)
        assert found is not None
        assert found.title == "The Burning City"

    def test_get_chapter_missing(self, base_story: Story) -> None:
        assert base_story.get_chapter(99) is None

    def test_total_word_count(
        self,
        base_story: Story,
        chapter_one: Chapter,
        chapter_two: Chapter,
    ) -> None:
        base_story.add_chapter(chapter_one)
        base_story.add_chapter(chapter_two)
        expected = chapter_one.word_count + chapter_two.word_count
        assert base_story.total_word_count == expected

    def test_total_word_count_empty(self, base_story: Story) -> None:
        assert base_story.total_word_count == 0

    def test_previous_chapters_context_empty(self, base_story: Story) -> None:
        assert base_story.previous_chapters_context(before_chapter=1) == ""

    def test_previous_chapters_context(
        self,
        base_story: Story,
        chapter_one: Chapter,
        chapter_two: Chapter,
    ) -> None:
        base_story.add_chapter(chapter_one)
        base_story.add_chapter(chapter_two)
        ctx = base_story.previous_chapters_context(before_chapter=2)
        assert "The Burning City" in ctx
        assert "The Road North" not in ctx

    def test_characters_context_empty(self, base_story: Story) -> None:
        ctx = base_story.characters_context()
        assert "No characters" in ctx

    def test_characters_context(
        self,
        base_story: Story,
        protagonist: Character,
        antagonist: Character,
    ) -> None:
        base_story.add_character(protagonist)
        base_story.add_character(antagonist)
        ctx = base_story.characters_context()
        assert "Elara Voss" in ctx
        assert "The God-King" in ctx

    def test_story_context(self, base_story: Story) -> None:
        ctx = base_story.story_context()
        assert "Ashes of the Forgotten" in ctx
        assert "dark fantasy" in ctx
        assert "premise" in ctx.lower() or "Premise" in ctx

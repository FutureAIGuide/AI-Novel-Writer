"""Tests for the Chapter model."""

import pytest
from novel_writer.models.chapter import Chapter


@pytest.fixture
def rich_chapter() -> Chapter:
    return Chapter(
        number=1,
        title="The Awakening",
        summary="Elara wakes to find her mentor gone and the city in flames.",
        content="The city burned. Elara pressed her back against cold stone and breathed.",
    )


class TestChapterModel:
    def test_creation(self, rich_chapter: Chapter) -> None:
        assert rich_chapter.number == 1
        assert rich_chapter.title == "The Awakening"

    def test_display_title_with_title(self, rich_chapter: Chapter) -> None:
        assert rich_chapter.display_title() == "Chapter 1: The Awakening"

    def test_display_title_without_title(self) -> None:
        chap = Chapter(number=3)
        assert chap.display_title() == "Chapter 3"

    def test_word_count(self, rich_chapter: Chapter) -> None:
        expected = len(rich_chapter.content.split())
        assert rich_chapter.word_count == expected

    def test_word_count_empty(self) -> None:
        chap = Chapter(number=2)
        assert chap.word_count == 0

    def test_to_summary_block_uses_summary(self, rich_chapter: Chapter) -> None:
        block = rich_chapter.to_summary_block()
        assert "The Awakening" in block
        assert rich_chapter.summary in block

    def test_to_summary_block_falls_back_to_content(self) -> None:
        chap = Chapter(number=1, content="Once upon a time in a land far away.")
        block = chap.to_summary_block()
        assert "Once upon a time" in block

    def test_to_summary_block_no_content_or_summary(self) -> None:
        chap = Chapter(number=1)
        block = chap.to_summary_block()
        assert "No content yet" in block

    def test_defaults(self) -> None:
        chap = Chapter(number=5)
        assert chap.title == ""
        assert chap.summary == ""
        assert chap.content == ""
        assert chap.notes == ""

"""Tests for the FileManager utility."""

import json
import pytest
from pathlib import Path

from novel_writer.models.story import Story
from novel_writer.models.character import Character
from novel_writer.models.chapter import Chapter
from novel_writer.utils.file_manager import FileManager


@pytest.fixture
def tmp_file_manager(tmp_path: Path) -> FileManager:
    return FileManager(output_dir=str(tmp_path))


@pytest.fixture
def sample_story() -> Story:
    story = Story(
        title="The Iron Throne",
        genre="political thriller",
        premise="A senator discovers the government is run by an AI.",
    )
    story.add_character(Character(name="Dana Kim", role="protagonist", description="Tenacious."))
    story.add_chapter(Chapter(number=1, title="First Vote", content="The chamber fell silent."))
    return story


class TestFileManager:
    def test_save_creates_file(
        self,
        tmp_file_manager: FileManager,
        sample_story: Story,
    ) -> None:
        path = tmp_file_manager.save(sample_story)
        assert path.exists()

    def test_save_load_roundtrip(
        self,
        tmp_file_manager: FileManager,
        sample_story: Story,
    ) -> None:
        tmp_file_manager.save(sample_story)
        loaded = tmp_file_manager.load("The Iron Throne")
        assert loaded.title == sample_story.title
        assert loaded.genre == sample_story.genre
        assert loaded.premise == sample_story.premise
        assert len(loaded.characters) == 1
        assert loaded.characters[0].name == "Dana Kim"
        assert len(loaded.chapters) == 1
        assert loaded.chapters[0].content == "The chamber fell silent."

    def test_load_missing_raises(self, tmp_file_manager: FileManager) -> None:
        with pytest.raises(FileNotFoundError):
            tmp_file_manager.load("Nonexistent Story Title")

    def test_list_stories_empty(self, tmp_file_manager: FileManager) -> None:
        assert tmp_file_manager.list_stories() == []

    def test_list_stories(
        self,
        tmp_file_manager: FileManager,
        sample_story: Story,
    ) -> None:
        tmp_file_manager.save(sample_story)
        titles = tmp_file_manager.list_stories()
        assert len(titles) == 1

    def test_export_text(
        self,
        tmp_file_manager: FileManager,
        sample_story: Story,
    ) -> None:
        txt_path = tmp_file_manager.export_text(sample_story)
        assert txt_path.exists()
        content = txt_path.read_text(encoding="utf-8")
        assert "THE IRON THRONE" in content
        assert "The chamber fell silent." in content

    def test_safe_title_special_chars(self, tmp_file_manager: FileManager) -> None:
        story = Story(title="Hello: World! (2024)", genre="drama", premise="p")
        path = tmp_file_manager.save(story)
        assert path.exists()
        # Should be loadable from path
        loaded = tmp_file_manager.load_from_path(path)
        assert loaded.title == "Hello: World! (2024)"

    def test_export_markdown(
        self,
        tmp_file_manager: FileManager,
        sample_story: Story,
    ) -> None:
        tmp_file_manager.save(sample_story)
        md_path = tmp_file_manager.export_markdown(sample_story)
        assert md_path.suffix == ".md"
        text = md_path.read_text(encoding="utf-8")
        assert sample_story.title in text
        assert "First Vote" in text or "Chapter 1" in text

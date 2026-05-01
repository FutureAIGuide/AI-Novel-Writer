"""UI-facing API: load/save stories, context packing metadata, generation helpers."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from novel_writer.config import Config
from novel_writer.generators.chapter_generator import ChapterGenerator
from novel_writer.generators.selection_editor import SelectionEditor
from novel_writer.models.chapter import Chapter
from novel_writer.models.story import Story
from novel_writer.settings.manager import SettingsManager
from novel_writer.utils.context_budget import build_context_pack, default_budget_for_provider
from novel_writer.utils.file_manager import FileManager


@dataclass
class StudioSettingsInfo:
    """Subset of settings safe to expose to the studio UI."""

    active_provider: str
    model: str
    output_dir: str
    studio_context_budget_tokens: int
    supports_streaming: bool


class NovelStudioService:
    """Stable operations for the local studio (and tests)."""

    def __init__(self, output_dir: str | None = None) -> None:
        resolved = output_dir
        if resolved is None:
            try:
                mgr = SettingsManager()
                if mgr.exists():
                    resolved = mgr.load().output_dir or Config.OUTPUT_DIR
            except (OSError, ValueError):
                resolved = Config.OUTPUT_DIR
        self._output_dir = resolved or Config.OUTPUT_DIR
        self._fm = FileManager(self._output_dir)

    @property
    def output_dir(self) -> Path:
        return self._fm.output_dir

    def list_stories(self) -> list[str]:
        return self._fm.list_stories()

    def load_story(self, title: str) -> Story:
        return self._fm.load(title)

    def save_story(self, story: Story) -> Path:
        return self._fm.save(story)

    def context_pack_meta(self, story: Story, before_chapter: int) -> dict[str, Any]:
        """Return estimated token usage for the chapter prompt context."""
        mgr = SettingsManager()
        budget = 0
        provider = "openai"
        if mgr.exists():
            app = mgr.load()
            provider = app.active_provider
            if app.studio_context_budget_tokens > 0:
                budget = app.studio_context_budget_tokens
        if budget <= 0:
            budget = default_budget_for_provider(provider)
        previous = story.previous_chapters_context(before_chapter=before_chapter)
        prev_block = f"Previous chapters (for continuity):\n{previous}\n\n" if previous else ""
        pack = build_context_pack(
            story.story_context(),
            story.characters_context(),
            prev_block,
            budget_tokens=budget,
            reserve_for_instructions=2200,
        )
        return {
            "budget_tokens": pack.budget_tokens,
            "estimated_prompt_tokens": pack.estimated_prompt_tokens,
            "trimmed": pack.trimmed,
            "provider": provider,
        }

    def studio_settings_info(self) -> StudioSettingsInfo:
        gen = ChapterGenerator()
        provider = gen.provider
        model = getattr(gen, "_model", "")
        supports = gen.supports_streaming
        output_dir = Config.OUTPUT_DIR
        studio_budget = 0
        try:
            mgr = SettingsManager()
            if mgr.exists():
                app = mgr.load()
                output_dir = app.output_dir or output_dir
                studio_budget = app.studio_context_budget_tokens
        except (OSError, ValueError):
            pass
        return StudioSettingsInfo(
            active_provider=provider,
            model=str(model),
            output_dir=output_dir,
            studio_context_budget_tokens=studio_budget,
            supports_streaming=supports,
        )

    def export_markdown(self, story: Story) -> Path:
        return FileManager(self._output_dir).export_markdown(story)

    def export_docx(self, story: Story) -> Path:
        return FileManager(self._output_dir).export_docx(story)

    def export_text(self, story: Story) -> Path:
        return self._fm.export_text(story)

    def stream_generate_chapter(
        self,
        story: Story,
        chapter_number: int,
        chapter_title: str = "",
        chapter_summary: str = "",
        extra_instructions: str = "",
    ) -> Iterator[str]:
        ch_gen = ChapterGenerator()
        yield from ch_gen.generate_chapter_stream(
            story,
            chapter_number,
            chapter_title=chapter_title,
            chapter_summary=chapter_summary,
            extra_instructions=extra_instructions,
        )

    def stream_continue_chapter(
        self, story: Story, chapter: Chapter, continuation_hint: str = ""
    ) -> Iterator[str]:
        ch_gen = ChapterGenerator()
        yield from ch_gen.continue_chapter_stream(story, chapter, continuation_hint)

    def stream_transform_selection(
        self,
        story: Story,
        selected_text: str,
        operation: str,
        *,
        before_chapter: int = 1,
        extra_instruction: str = "",
    ) -> Iterator[str]:
        editor = SelectionEditor()
        budget: int | None = None
        try:
            mgr = SettingsManager()
            if mgr.exists():
                app = mgr.load()
                if app.studio_context_budget_tokens > 0:
                    budget = app.studio_context_budget_tokens
        except (OSError, ValueError):
            pass
        yield from editor.transform_selection_stream(
            story,
            selected_text,
            operation,
            before_chapter=before_chapter,
            context_budget_tokens=budget,
            extra_instruction=extra_instruction,
        )

    def finalize_chapter_stream(
        self,
        story: Story,
        chapter_number: int,
        full_text: str,
        chapter_title: str = "",
        chapter_summary: str = "",
        snapshot_before: bool = True,
    ) -> Chapter:
        """Update or create a chapter from streamed *full_text*; optionally snapshot prior body."""
        existing = story.get_chapter(chapter_number)
        if existing is not None:
            if snapshot_before and existing.content.strip():
                existing.snapshot_content("before AI chapter regenerate")
            if chapter_title:
                existing.title = chapter_title
            if chapter_summary:
                existing.summary = chapter_summary
            existing.content = full_text
            return existing
        chapter = Chapter(
            number=chapter_number,
            title=chapter_title,
            summary=chapter_summary,
            content=full_text,
        )
        story.add_chapter(chapter)
        return chapter

    def apply_selection_replace(
        self,
        story: Story,
        chapter_number: int,
        full_chapter_text: str,
        snapshot_label: str = "before AI selection edit",
    ) -> None:
        """Replace chapter *chapter_number* content with *full_chapter_text* after snapshot."""
        ch = story.get_chapter(chapter_number)
        if ch is None:
            story.add_chapter(
                Chapter(number=chapter_number, title="", summary="", content=full_chapter_text)
            )
            return
        if ch.content.strip():
            ch.snapshot_content(snapshot_label)
        ch.content = full_chapter_text

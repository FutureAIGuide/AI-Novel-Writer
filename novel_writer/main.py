"""CLI entry point for AI Novel Writer."""

from __future__ import annotations

import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table

from novel_writer.config import Config
from novel_writer.models.story import Story
from novel_writer.models.character import Character
from novel_writer.generators.story_generator import StoryGenerator
from novel_writer.generators.character_generator import CharacterGenerator
from novel_writer.generators.chapter_generator import ChapterGenerator
from novel_writer.utils.file_manager import FileManager
from novel_writer.settings.cli import settings_cli

console = Console()


# --------------------------------------------------------------------------- #
#  CLI group                                                                   #
# --------------------------------------------------------------------------- #


@click.group()
def cli() -> None:
    """AI Novel Writer — generate novels with OpenAI."""


cli.add_command(settings_cli)


# --------------------------------------------------------------------------- #
#  new — interactively create a new story project                              #
# --------------------------------------------------------------------------- #


@cli.command()
@click.option("--title", prompt="Story title", help="Title of the novel")
@click.option("--genre", prompt="Genre", help="Genre (e.g. fantasy, sci-fi, thriller)")
@click.option("--keywords", default="", help="Comma-separated themes or keywords")
@click.option("--chapters", default=10, show_default=True, help="Target number of chapters")
def new(title: str, genre: str, keywords: str, chapters: int) -> None:
    """Create a new story: generate premise, setting, outline, and characters."""
    try:
        Config.validate()
    except ValueError as exc:
        console.print(f"[red]Configuration error:[/red] {exc}")
        raise SystemExit(1) from exc

    story = Story(title=title, genre=genre)
    file_manager = FileManager(Config.OUTPUT_DIR)
    story_gen = StoryGenerator()
    char_gen = CharacterGenerator()

    with console.status("[bold green]Generating premise…"):
        story.premise = story_gen.generate_premise(genre, keywords)
    console.print(Panel(story.premise, title="Premise", border_style="cyan"))

    with console.status("[bold green]Generating setting…"):
        story.setting = story_gen.generate_setting(genre, story.premise)
    console.print(Panel(story.setting, title="Setting", border_style="cyan"))

    with console.status("[bold green]Generating style notes…"):
        story.style_notes = story_gen.generate_style_notes(genre)
    console.print(Panel(story.style_notes, title="Style Notes", border_style="cyan"))

    if Confirm.ask("Generate characters now?", default=True):
        roles = ["protagonist", "antagonist", "supporting character"]
        for role in roles:
            hints = Prompt.ask(f"Hints for {role} (optional, press Enter to skip)", default="")
            with console.status(f"[bold green]Generating {role}…"):
                char = char_gen.generate_character(story, role, hints)
            story.add_character(char)
            console.print(Panel(char.to_prompt_context(), title=f"{char.name} ({role})", border_style="magenta"))

    with console.status("[bold green]Generating chapter outline…"):
        story.outline = story_gen.generate_outline(story, num_chapters=chapters)
    console.print(Panel(story.outline, title="Chapter Outline", border_style="cyan"))

    path = file_manager.save(story)
    console.print(f"\n[bold green]✓ Story saved to:[/bold green] {path}")


# --------------------------------------------------------------------------- #
#  write — generate a specific chapter                                         #
# --------------------------------------------------------------------------- #


@cli.command()
@click.option("--title", prompt="Story title", help="Title of the existing story")
@click.option("--chapter", "chapter_number", type=int, prompt="Chapter number to write", help="Chapter number")
@click.option("--summary", default="", help="Brief summary of what happens in this chapter")
@click.option("--instructions", default="", help="Extra author instructions")
def write(title: str, chapter_number: int, summary: str, instructions: str) -> None:
    """Write a chapter for an existing story."""
    try:
        Config.validate()
    except ValueError as exc:
        console.print(f"[red]Configuration error:[/red] {exc}")
        raise SystemExit(1) from exc

    file_manager = FileManager(Config.OUTPUT_DIR)
    try:
        story = file_manager.load(title)
    except FileNotFoundError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise SystemExit(1) from exc

    if not summary:
        summary = Prompt.ask("Brief chapter summary (optional)", default="")

    chapter_gen = ChapterGenerator()
    with console.status(f"[bold green]Writing Chapter {chapter_number}…"):
        chapter = chapter_gen.generate_chapter(
            story,
            chapter_number=chapter_number,
            chapter_summary=summary,
            extra_instructions=instructions,
        )

    console.print(Panel(chapter.content, title=chapter.display_title(), border_style="green"))
    console.print(f"[dim]Word count: {chapter.word_count}[/dim]")

    story.add_chapter(chapter)

    if Confirm.ask("Generate summary for this chapter?", default=True):
        with console.status("[bold green]Summarizing chapter…"):
            chapter.summary = chapter_gen.generate_chapter_summary(chapter)
        console.print(Panel(chapter.summary, title="Chapter Summary", border_style="dim"))

    path = file_manager.save(story)
    console.print(f"\n[bold green]✓ Story saved to:[/bold green] {path}")


# --------------------------------------------------------------------------- #
#  list — show saved stories                                                   #
# --------------------------------------------------------------------------- #


@cli.command("list")
def list_stories() -> None:
    """List all saved story projects."""
    file_manager = FileManager(Config.OUTPUT_DIR)
    stories = file_manager.list_stories()
    if not stories:
        console.print("[yellow]No stories found.[/yellow] Use [bold]novel-writer new[/bold] to create one.")
        return
    table = Table(title="Saved Stories")
    table.add_column("Title", style="cyan")
    for s in stories:
        table.add_row(s)
    console.print(table)


# --------------------------------------------------------------------------- #
#  export — export story as plain text                                         #
# --------------------------------------------------------------------------- #


@cli.command()
@click.option("--title", prompt="Story title", help="Title of the story to export")
def export(title: str) -> None:
    """Export a story to a plain-text file."""
    file_manager = FileManager(Config.OUTPUT_DIR)
    try:
        story = file_manager.load(title)
    except FileNotFoundError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise SystemExit(1) from exc

    path = file_manager.export_text(story)
    console.print(f"[bold green]✓ Exported to:[/bold green] {path}")
    console.print(f"[dim]Total word count: {story.total_word_count:,}[/dim]")


# --------------------------------------------------------------------------- #
#  info — show story details                                                   #
# --------------------------------------------------------------------------- #


@cli.command()
@click.option("--title", prompt="Story title", help="Title of the story")
def info(title: str) -> None:
    """Show details about a saved story."""
    file_manager = FileManager(Config.OUTPUT_DIR)
    try:
        story = file_manager.load(title)
    except FileNotFoundError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise SystemExit(1) from exc

    console.print(Panel(story.story_context(), title=story.title, border_style="cyan"))

    if story.characters:
        console.print("\n[bold]Characters:[/bold]")
        for char in story.characters:
            desc = char.description
            desc_preview = (desc[:80] + "…") if len(desc) > 80 else (desc or "No description.")
            console.print(f"  • [magenta]{char.name}[/magenta] ({char.role}): {desc_preview}")

    if story.chapters:
        console.print("\n[bold]Chapters:[/bold]")
        for chap in story.chapters:
            console.print(f"  • [green]{chap.display_title()}[/green] — {chap.word_count:,} words")

    console.print(f"\n[dim]Total word count: {story.total_word_count:,}[/dim]")


if __name__ == "__main__":
    cli()

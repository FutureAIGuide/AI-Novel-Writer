"""Chapter model for AI Novel Writer."""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field


class ChapterHistoryEntry(BaseModel):
    """A snapshot of chapter content before a destructive edit."""

    saved_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="UTC ISO-8601 timestamp when the snapshot was taken",
    )
    label: str = Field(default="", description="Optional note (e.g. before AI rewrite)")
    content: str = Field(default="", description="Chapter body at snapshot time")


class Chapter(BaseModel):
    """Represents a single chapter in a novel."""

    number: int = Field(..., description="Chapter number (1-indexed)")
    title: str = Field(default="", description="Chapter title")
    summary: str = Field(default="", description="Short summary of what happens in this chapter")
    content: str = Field(default="", description="Full prose content of the chapter")
    notes: str = Field(default="", description="Author notes or revision flags for this chapter")
    content_history: list[ChapterHistoryEntry] = Field(
        default_factory=list,
        description="Prior snapshots of content (newest last)",
    )

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

    def snapshot_content(self, label: str = "") -> None:
        """Append the current *content* to *content_history* (cap at 20 entries)."""
        if not self.content:
            return
        self.content_history.append(
            ChapterHistoryEntry(label=label or "snapshot", content=self.content)
        )
        if len(self.content_history) > 20:
            self.content_history = self.content_history[-20:]

    def restore_latest_snapshot(self) -> bool:
        """Pop the latest history entry and set *content* to it. Returns False if empty."""
        if not self.content_history:
            return False
        entry = self.content_history.pop()
        self.content = entry.content
        return True

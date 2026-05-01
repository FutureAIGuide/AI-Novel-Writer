"""FastAPI local studio server."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field

from novel_writer.models.story import Story
from novel_writer.studio.service import NovelStudioService

_STATIC_DIR = Path(__file__).resolve().parent / "static"


class SaveStoryBody(BaseModel):
    story: dict = Field(..., description="Serialized Story JSON")


class ChapterStreamBody(BaseModel):
    title: str
    chapter_number: int = Field(..., ge=1)
    chapter_title: str = ""
    chapter_summary: str = ""
    extra_instructions: str = ""


class ContinueStreamBody(BaseModel):
    title: str
    chapter_number: int = Field(..., ge=1)
    continuation_hint: str = ""


class SelectionStreamBody(BaseModel):
    title: str
    chapter_number: int = Field(..., ge=1)
    selected_text: str
    operation: str
    extra_instruction: str = ""


def create_app(service: NovelStudioService | None = None) -> FastAPI:
    svc = service or NovelStudioService()
    app = FastAPI(title="AI Novel Writer Studio", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/")
    def index() -> FileResponse:
        index_path = _STATIC_DIR / "index.html"
        if not index_path.exists():
            raise HTTPException(status_code=404, detail="Studio UI not found")
        return FileResponse(index_path)

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/settings")
    def settings() -> dict:
        info = svc.studio_settings_info()
        return {
            "active_provider": info.active_provider,
            "model": info.model,
            "output_dir": info.output_dir,
            "studio_context_budget_tokens": info.studio_context_budget_tokens,
            "supports_streaming": info.supports_streaming,
        }

    @app.get("/api/stories")
    def list_stories() -> dict[str, list[str]]:
        return {"titles": svc.list_stories()}

    @app.get("/api/story")
    def get_story(title: str) -> dict:
        try:
            story = svc.load_story(title)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail=f"Story not found: {title!r}") from None
        return json.loads(story.model_dump_json())

    @app.post("/api/story")
    def save_story(body: SaveStoryBody) -> dict[str, str]:
        story = Story(**body.story)
        path = svc.save_story(story)
        return {"saved": str(path)}

    @app.get("/api/context-pack")
    def context_pack(title: str, before_chapter: int = 1) -> dict:
        try:
            story = svc.load_story(title)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail=f"Story not found: {title!r}") from None
        return svc.context_pack_meta(story, before_chapter=before_chapter)

    def _sse_events(sync_iter):
        for chunk in sync_iter:
            payload = json.dumps({"chunk": chunk}, ensure_ascii=False)
            yield f"data: {payload}\n\n"
        yield "data: " + json.dumps({"done": True}) + "\n\n"

    @app.post("/api/stream/chapter")
    def stream_chapter(body: ChapterStreamBody) -> StreamingResponse:
        try:
            story = svc.load_story(body.title)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail=f"Story not found: {body.title!r}") from None

        def gen():
            yield from _sse_events(
                svc.stream_generate_chapter(
                    story,
                    body.chapter_number,
                    chapter_title=body.chapter_title,
                    chapter_summary=body.chapter_summary,
                    extra_instructions=body.extra_instructions,
                )
            )

        return StreamingResponse(gen(), media_type="text/event-stream")

    @app.post("/api/stream/continue")
    def stream_continue(body: ContinueStreamBody) -> StreamingResponse:
        try:
            story = svc.load_story(body.title)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail=f"Story not found: {body.title!r}") from None
        ch = story.get_chapter(body.chapter_number)
        if ch is None:
            raise HTTPException(status_code=400, detail="Chapter does not exist yet")

        def gen():
            yield from _sse_events(svc.stream_continue_chapter(story, ch, body.continuation_hint))

        return StreamingResponse(gen(), media_type="text/event-stream")

    @app.post("/api/stream/selection")
    def stream_selection(body: SelectionStreamBody) -> StreamingResponse:
        try:
            story = svc.load_story(body.title)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail=f"Story not found: {body.title!r}") from None

        def gen():
            yield from _sse_events(
                svc.stream_transform_selection(
                    story,
                    body.selected_text,
                    body.operation,
                    before_chapter=body.chapter_number,
                    extra_instruction=body.extra_instruction,
                )
            )

        return StreamingResponse(gen(), media_type="text/event-stream")

    @app.post("/api/export/markdown")
    def export_md(title: str) -> dict[str, str]:
        try:
            story = svc.load_story(title)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail=f"Story not found: {title!r}") from None
        path = svc.export_markdown(story)
        return {"path": str(path)}

    @app.post("/api/export/docx")
    def export_docx(title: str) -> dict[str, str]:
        try:
            story = svc.load_story(title)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail=f"Story not found: {title!r}") from None
        try:
            path = svc.export_docx(story)
        except ImportError as exc:
            raise HTTPException(status_code=501, detail=str(exc)) from exc
        return {"path": str(path)}

    return app


app = create_app()

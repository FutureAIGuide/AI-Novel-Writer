"""PyInstaller entry: run the local FastAPI studio."""

from __future__ import annotations


def main() -> None:
    import uvicorn

    uvicorn.run(
        "novel_writer.studio.app:app",
        host="127.0.0.1",
        port=8765,
        reload=False,
    )


if __name__ == "__main__":
    main()

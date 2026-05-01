# AI Novel Writer

An **AI-powered novel writing assistant** built with Python and OpenAI. Generate story premises, world settings, character profiles, chapter outlines, and full chapter prose — all from your terminal.

---

## Features

- **Story generation** — produce compelling premises, immersive settings, and detailed chapter outlines.
- **Character creation** — generate psychologically rich protagonists, antagonists, and supporting cast with backstories, motivations, and arcs.
- **Chapter writing** — write full chapters (800–1,500 words) with continuity across previous chapters, or continue where a chapter left off.
- **Chapter summarisation** — auto-generate concise summaries after each chapter for easy reference.
- **Relationship mapping** — describe the dynamics between any two characters.
- **Persistent storage** — stories are saved as JSON files and can be reloaded at any time.
- **Plain-text export** — export the full manuscript as a `.txt` file.
- **Rich terminal UI** — colour-coded panels, progress spinners, and interactive prompts powered by [Rich](https://github.com/Textualize/rich) and [Click](https://click.palletsprojects.com/).

---

## Project Structure

```
AI-Novel-Writer/
├── novel_writer/
│   ├── __init__.py
│   ├── config.py                   # Environment-based configuration
│   ├── main.py                     # CLI entry point (Click)
│   ├── generators/
│   │   ├── base.py                 # Shared OpenAI client wrapper
│   │   ├── story_generator.py      # Premise, outline, setting, style
│   │   ├── character_generator.py  # Character profiles & relationships
│   │   └── chapter_generator.py   # Chapter prose & summaries
│   ├── models/
│   │   ├── story.py                # Story dataclass (Pydantic)
│   │   ├── character.py            # Character dataclass (Pydantic)
│   │   └── chapter.py             # Chapter dataclass (Pydantic)
│   └── utils/
│       └── file_manager.py         # JSON save/load + text export
├── tests/
│   ├── test_story.py
│   ├── test_character.py
│   ├── test_chapter.py
│   └── test_file_manager.py
├── .env.example
├── pyproject.toml
├── requirements.txt
└── README.md
```

---

## Requirements

- Python 3.9 or newer
- An [OpenAI API key](https://platform.openai.com/api-keys)

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/FutureAIGuide/AI-Novel-Writer.git
cd AI-Novel-Writer
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate      # macOS / Linux
.venv\Scripts\activate         # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
# or install as a package (enables the `novel-writer` command)
pip install -e .
```

### 4. Configure your API key

```bash
cp .env.example .env
# Edit .env and set OPENAI_API_KEY=sk-...
```

Available environment variables:

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | *(required)* | Your OpenAI API key |
| `OPENAI_MODEL` | `gpt-4o` | Model to use for generation |
| `OPENAI_MAX_TOKENS` | `2048` | Maximum tokens per request |
| `OPENAI_TEMPERATURE` | `0.8` | Creativity level (0.0 – 1.0) |
| `OUTPUT_DIR` | `stories` | Directory where stories are saved |

---

## Usage

### Create a new story

```bash
novel-writer new \
  --title "Ashes of the Forgotten" \
  --genre "dark fantasy" \
  --keywords "redemption, ancient gods, betrayal" \
  --chapters 12
```

The command will:

1. Generate a story premise
2. Generate a setting description
3. Generate style notes
4. Optionally generate protagonist, antagonist, and supporting characters
5. Generate a chapter-by-chapter outline
6. Save everything to `stories/Ashes_of_the_Forgotten.json`

### Write a chapter

```bash
novel-writer write \
  --title "Ashes of the Forgotten" \
  --chapter 1 \
  --summary "Elara escapes the burning city and finds a cryptic letter from her mentor."
```

### List saved stories

```bash
novel-writer list
```

### Show story details

```bash
novel-writer info --title "Ashes of the Forgotten"
```

### Export as plain text

```bash
novel-writer export --title "Ashes of the Forgotten"
# Outputs: stories/Ashes_of_the_Forgotten.txt
```

---

## Running Programmatically

You can also use the library directly in your Python scripts:

```python
from novel_writer.models.story import Story
from novel_writer.models.character import Character
from novel_writer.generators.story_generator import StoryGenerator
from novel_writer.generators.character_generator import CharacterGenerator
from novel_writer.generators.chapter_generator import ChapterGenerator
from novel_writer.utils.file_manager import FileManager

# Build a story
story = Story(title="Echoes in the Void", genre="sci-fi thriller")

# Generate a premise
gen = StoryGenerator()
story.premise = gen.generate_premise("sci-fi thriller", keywords="AI, memory, identity")

# Generate a character
char_gen = CharacterGenerator()
hero = char_gen.generate_character(story, role="protagonist")
story.add_character(hero)

# Write chapter 1
chap_gen = ChapterGenerator()
chapter = chap_gen.generate_chapter(
    story,
    chapter_number=1,
    chapter_summary="Dr Yara wakes with no memory inside a derelict space station.",
)
story.add_chapter(chapter)

# Save
fm = FileManager()
path = fm.save(story)
print(f"Saved to {path}")
```

---

## Running Tests

```bash
pip install pytest
pytest
```

---

## Contributing

1. Fork the repository and create a feature branch.
2. Install dev dependencies: `pip install -e ".[dev]"`.
3. Run the test suite before submitting a PR: `pytest`.
4. Follow PEP 8 and include type hints for all public functions.

---

## License

This project is licensed under the [MIT License](LICENSE).
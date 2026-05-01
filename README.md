# AI Novel Writer

An **AI-powered novel writing assistant** built with Python. Generate story premises, world settings, character profiles, chapter outlines, and full chapter prose — all from your terminal.

Supports **multiple AI providers**: OpenAI, Anthropic, Google AI (Gemini), OpenRouter, LM Studio (local), and Ollama (local).

---

## Features

- **Story generation** — produce compelling premises, immersive settings, and detailed chapter outlines.
- **Character creation** — generate psychologically rich protagonists, antagonists, and supporting cast with backstories, motivations, and arcs.
- **Chapter writing** — write full chapters (800–1,500 words) with continuity across previous chapters, or continue where a chapter left off.
- **Chapter summarisation** — auto-generate concise summaries after each chapter for easy reference.
- **Relationship mapping** — describe the dynamics between any two characters.
- **Persistent storage** — stories are saved as JSON files and can be reloaded at any time.
- **Plain-text export** — export the full manuscript as a `.txt` file.
- **Multi-provider AI settings** — manage API keys and model selection for OpenAI, Anthropic, Google AI, OpenRouter, LM Studio, and Ollama via `novel-writer settings`.
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
│   │   ├── base.py                 # Multi-provider AI client wrapper
│   │   ├── story_generator.py      # Premise, outline, setting, style
│   │   ├── character_generator.py  # Character profiles & relationships
│   │   └── chapter_generator.py   # Chapter prose & summaries
│   ├── models/
│   │   ├── story.py                # Story dataclass (Pydantic)
│   │   ├── character.py            # Character dataclass (Pydantic)
│   │   └── chapter.py             # Chapter dataclass (Pydantic)
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── models.py               # Provider config models & built-in model lists
│   │   ├── manager.py              # Settings persistence (JSON + key obfuscation)
│   │   └── cli.py                  # `novel-writer settings` CLI commands
│   └── utils/
│       └── file_manager.py         # JSON save/load + text export
├── tests/
│   ├── test_story.py
│   ├── test_character.py
│   ├── test_chapter.py
│   ├── test_file_manager.py
│   └── test_settings.py
├── .env.example
├── pyproject.toml
├── requirements.txt
└── README.md
```

---

## Requirements

- Python 3.9 or newer
- At least one AI provider configured (see [AI Settings](#ai-settings--multi-provider-support) below)

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

### 4. Configure your AI provider

**Option A — Environment variable (quickest for OpenAI):**

```bash
cp .env.example .env
# Edit .env and set OPENAI_API_KEY=sk-...
```

**Option B — Settings command (recommended for all providers):**

```bash
novel-writer settings set-provider openai --api-key sk-... --set-active
```

Available environment variables (fallback when no settings file exists):

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | *(required if no settings file)* | Your OpenAI API key |
| `OPENAI_MODEL` | `gpt-4o` | Model to use for generation |
| `OPENAI_MAX_TOKENS` | `2048` | Maximum tokens per request |
| `OPENAI_TEMPERATURE` | `0.8` | Creativity level (0.0 – 1.0) |
| `OUTPUT_DIR` | `stories` | Directory where stories are saved |
| `AI_NOVEL_WRITER_SETTINGS` | `~/.config/ai-novel-writer/settings.json` | Override settings file path |

---

## AI Settings — Multi-Provider Support

All provider settings are managed with the `novel-writer settings` command group.
Settings are stored in `~/.config/ai-novel-writer/settings.json` with API keys
Base-64 obfuscated (not stored in plain text).

### Show current settings

```bash
novel-writer settings show
```

### Configure a provider

```bash
# OpenAI
novel-writer settings set-provider openai \
  --api-key sk-... \
  --model gpt-4o \
  --set-active

# Anthropic (requires: pip install anthropic)
novel-writer settings set-provider anthropic \
  --api-key sk-ant-... \
  --model claude-3-5-sonnet-20241022 \
  --set-active

# Google AI / Gemini (requires: pip install google-generativeai)
novel-writer settings set-provider google_ai \
  --api-key AIza... \
  --model gemini-1.5-pro \
  --set-active

# OpenRouter
novel-writer settings set-provider openrouter \
  --api-key sk-or-... \
  --model openai/gpt-4o \
  --set-active

# LM Studio (local — no API key needed)
novel-writer settings set-provider lm_studio \
  --endpoint http://localhost:1234/v1 \
  --model my-local-model \
  --set-active

# Ollama (local — no API key needed)
novel-writer settings set-provider ollama \
  --endpoint http://localhost:11434 \
  --model llama3 \
  --set-active
```

### Switch the active provider

```bash
novel-writer settings active ollama
```

### List built-in model identifiers

```bash
novel-writer settings list-models openai
novel-writer settings list-models anthropic
novel-writer settings list-models google_ai
novel-writer settings list-models openrouter
novel-writer settings list-models ollama
```

### Test a provider connection

```bash
novel-writer settings test openai
novel-writer settings test ollama
```

### Remove / disable a provider

```bash
novel-writer settings remove anthropic --clear-key
```

### Export and import settings (backup / restore)

```bash
# Export without API keys (safe to share)
novel-writer settings export --output my-settings-backup.json

# Export including API keys (keep secure!)
novel-writer settings export --output my-settings-backup.json --include-keys

# Import (existing keys are preserved when not present in the backup)
novel-writer settings import --input my-settings-backup.json
```

### Supported providers and model identifiers

| Provider | Key Required | Built-in Models |
|---|---|---|
| **OpenAI** | Yes | gpt-4o, gpt-4o-mini, gpt-4-turbo, gpt-4, gpt-3.5-turbo |
| **Anthropic** | Yes | claude-3-5-sonnet-20241022, claude-3-5-haiku-20241022, claude-3-opus-20240229, … |
| **Google AI** | Yes | gemini-1.5-pro, gemini-1.5-flash, gemini-pro, gemini-pro-vision |
| **OpenRouter** | Yes | openai/gpt-4o, anthropic/claude-3.5-sonnet, meta-llama/llama-3.1-8b-instruct, … |
| **LM Studio** | No (local) | User-defined (whatever model you have loaded) |
| **Ollama** | No (local) | llama3, llama3.1, mistral, codellama, phi3, gemma2, qwen2, … |

> **Optional provider packages:**  
> Anthropic: `pip install anthropic`  
> Google AI: `pip install google-generativeai`  
> All other providers use the built-in `openai` package (OpenAI-compatible API).

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
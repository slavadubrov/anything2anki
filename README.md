# Anything2Anki

Generate Anki decks from plain text using an LLM (via the `aisuite` SDK). The tool reads a local text/Markdown file, asks a language model to extract clear Q&A pairs, and builds a `.apkg` file you can import into Anki.

- LLM provider: `aisuite` (OpenAI enabled by default)
- Default model: `gpt5mini`
- Output: Anki `.apkg` deck built with `genanki`

## How It Works

1. Read input file contents (UTF‑8 text/Markdown).
2. Build prompts: a fixed system prompt plus a user prompt with your learning objective and the file’s content.
3. Call the LLM using `aisuite` with the selected `--model` (default `gpt5mini`).
4. Parse the LLM response as a JSON array of objects `{ "question": ..., "answer": ... }`.
5. Create a simple Q&A Anki model and deck using `genanki`.
6. Write a Markdown preview report alongside the output showing all generated Q&A pairs.
7. Write a `.apkg` file ready to import into Anki.

If the model returns non‑JSON output or no Q&A pairs, the run fails with a helpful error. Large inputs and poorly formatted content can reduce quality; consider pruning inputs to the most relevant sections.

## Installation

This project uses [uv](https://github.com/astral-sh/uv) for dependency management.

```bash
uv sync
```

This installs dependencies and the package in editable mode. Alternatively:

```bash
uv pip install -e .
```

## Setup

Environment variables are loaded automatically from a local `.env` at the project root (see `src/anything2anki/__init__.py`). Configure provider credentials as needed for your chosen model. For OpenAI models, set `OPENAI_API_KEY`.

```bash
cp .env.example .env
echo "OPENAI_API_KEY=sk-..." >> .env
```

You can also export variables directly in your shell:

```bash
export OPENAI_API_KEY=sk-...
```

Notes:

- The project depends on `aisuite[openai]`, so OpenAI works without extra setup. Other providers can be used if supported by `aisuite` and available in your environment; pass their (optionally provider-qualified) model name to `--model`.
- Never commit real API keys; `.env` is in `.gitignore`.

## Usage

### CLI

Basic usage (output defaults to `<input>.apkg`):

```bash
anything2anki input.txt "Extract key concepts and definitions"
```

Explicit output path and model:

```bash
anything2anki input.md "Extract key concepts and definitions" \
  --output data/civics.apkg \
  --model gpt5mini

Preview only (skip .apkg, just write Markdown preview next to the would-be output path):

```bash
anything2anki input.md "Extract key concepts" --preview-only
```

```

Run as a module (useful with `uv`):

```bash
uv run python -m anything2anki data/input.md \
  "Extract all terms and definitions" -o data/output.apkg
```

CLI options:

- `file_path` (positional): Path to the input text/Markdown file.
- `learning_description` (positional): What to learn/extract (drives the prompt).
- `--output, -o`: Output `.apkg` path. Defaults to `<input>.apkg`.
- `--model, -m`: LLM model (default `gpt5mini`).
- `--preview-only`: Only generate the Markdown preview report and skip creating the `.apkg` deck.

### Python API

```python
from anything2anki import generate_anki_cards

generate_anki_cards(
    file_path="input.txt",
    learning_description="Extract key concepts and definitions",
    output_path="output.apkg",
    model="gpt5mini",  # optional, default shown
)
```

## Models

- Default: `gpt5mini`.
- Override with `--model` or the `model` argument in the Python API.
- Model naming follows `aisuite`’s conventions. If using a provider-qualified model like `openai:gpt-4o`, ensure credentials are configured.

## Workflow Details

- Prompts: see `src/anything2anki/prompts.py` for the system and user templates. The user prompt embeds your learning description and full file contents, and instructs the model to return only a JSON array.
- Parsing: the tool extracts the first `[` … last `]` slice to tolerate Markdown code fences, then parses JSON. If parsing fails, the original snippet is included in the error to aid debugging.
- Deck/model: a simple two‑field “Question / Answer” model is defined in `src/anything2anki/anki_model.py` and a deck named "Generated Deck" is created. Each Q&A becomes one note.
- Packaging: the deck is exported as `.apkg` using `genanki` and written to `--output`.

Architecture: CLI → `workflow.generate_anki_cards` → `aisuite` LLM → JSON → Markdown preview → `genanki` deck → `.apkg`.

## Project Structure

```
anything2anki/
├── src/
│   └── anything2anki/
│       ├── __init__.py      # Loads .env; exposes generate_anki_cards
│       ├── __main__.py      # Enables `python -m anything2anki`
│       ├── cli.py           # CLI entry and args
│       ├── workflow.py      # Core logic (LLM call, JSON, deck build)
│       ├── anki_model.py    # `genanki` deck/model definitions
│       └── prompts.py       # System and user prompt templates
├── tests/                   # Pytest tests (when present)
├── pyproject.toml           # Build, deps, and tooling
└── README.md
```

## Development

Install with dev tools:

```bash
uv sync --dev
```

Lint and format with Ruff:

```bash
uv run ruff check .
uv run ruff format .
```

### Tests

Place tests under `tests/` and run with:

```bash
uv run pytest tests/
```

## Requirements

- Python 3.12+
- [uv](https://github.com/astral-sh/uv)
- Provider API keys as needed (e.g., `OPENAI_API_KEY` for OpenAI models)
- Anki (to import the resulting `.apkg`)

## Tips & Limitations

- Keep inputs focused. Very large files can exceed context limits and reduce quality.
- The model must return valid JSON; custom instructions in your learning description should not conflict with that requirement.
- The deck name is currently fixed to "Generated Deck"; changeable by editing `create_deck()`.

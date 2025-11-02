# Changelog

All notable changes to this project will be documented in this file.

## Unreleased — 2025-11-02

### Added

- Schema-Guided Reasoning (SGR) workflow across three phases: generation → reflection (judge) → improvement. See `src/anything2anki/prompts.py` and `src/anything2anki/workflow.py`.
- Strong typing and validation with Pydantic v2 models for flashcards and feedback. New module: `src/anything2anki/schemas.py` (includes JSON schemas and helpers).
- Prompt specialization presets and CLI flag `--preset` to guide SGR behavior. Presets: `general|cloze|concepts|procedures|programming`. See `src/anything2anki/cli.py` and `src/anything2anki/prompts.py`.
- Tests for prompts and expanded workflow coverage, including reflection/improvement and preview-only flows. See `tests/test_prompts.py` and updates in `tests/test_workflow.py`.

### Changed

- Workflow now parses model output into validated Pydantic models (`Flashcard`, `FlashcardFeedback`) and enforces strict JSON extraction with clearer errors. See `src/anything2anki/workflow.py`.
- System prompts now embed concrete JSON schemas and SGR instructions, specialized per preset. See `src/anything2anki/prompts.py`.
- Tooling configuration refined: added `pydantic` runtime dependency; expanded dev tools and lint/format settings in `pyproject.toml`.

### Docs

- README overhauled to document the SGR pipeline, presets, CLI usage, architecture diagrams, and schemas. See `README.md`.
- AGENTS guide updated to reflect SGR-based workflow and new CLI flags. See `AGENTS.md`.

### Breaking (internal APIs)

- Functions within `anything2anki.workflow` such as `parse_ai_response`, `parse_feedback_response`, `build_anki_deck`, and helpers now operate on typed Pydantic models rather than plain `dict` structures. The top‑level CLI and public entry `generate_anki_cards(...)` remain unchanged.

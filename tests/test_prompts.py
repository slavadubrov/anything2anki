"""Tests for prompt presets and system prompt construction."""

from anything2anki.prompts import AVAILABLE_PRESETS, get_system_prompts


def test_get_system_prompts_general_includes_schema_markers():
    gen, ref, imp = get_system_prompts("general")
    # Should mention JSON/schema and be non-empty
    assert "You must produce JSON" in gen
    assert "Provide constructive feedback" in ref
    assert "Return improved flashcards" in imp


def test_get_system_prompts_variants_differ():
    gen_general, _, _ = get_system_prompts("general")
    gen_cloze, _, _ = get_system_prompts("cloze")
    assert gen_general != gen_cloze
    assert "cloze" in gen_cloze.lower()


def test_available_presets_contains_defaults():
    assert "general" in AVAILABLE_PRESETS
    for name in ("cloze", "concepts", "procedures", "programming"):
        assert name in AVAILABLE_PRESETS

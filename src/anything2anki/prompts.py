"""Prompt templates for generating structured Q&A pairs from text."""

import json
from typing import Iterable, Literal

from .schemas import (
    FEEDBACK_SCHEMA,
    FLASHCARD_SCHEMA,
    Flashcard,
    FlashcardFeedback,
    ensure_feedback_serializable,
    ensure_flashcards_serializable,
)

PresetName = Literal[
    "general",
    "cloze",
    "concepts",
    "procedures",
    "programming",
]

# Exposed list for CLI/help.
AVAILABLE_PRESETS: tuple[PresetName, ...] = (
    "general",
    "cloze",
    "concepts",
    "procedures",
    "programming",
)


def _sgr_generation(preset: PresetName) -> str:
    """Return SGR instructions for the generation phase by preset."""

    if preset == "cloze":
        return (
            "Follow Schema-Guided Reasoning (SGR):\n"
            "1. Inspect the JSON schema to understand required fields.\n"
            "2. Plan atomic cards where each question targets a single missing fact suitable for cloze-style phrasing.\n"
            "3. Ensure each answer is a short, specific noun phrase; avoid multi-part or compound answers.\n"
            "4. Avoid pronouns or ambiguous references in questions; include minimal context to be self-contained.\n"
            "5. Output only valid JSON that conforms to the schema—no commentary or markdown."
        )
    if preset == "concepts":
        return (
            "Follow Schema-Guided Reasoning (SGR):\n"
            "1. Inspect the JSON schema to understand required fields.\n"
            "2. Emphasize conceptual understanding: prioritize why/how questions over rote facts.\n"
            "3. Each card should test a single mechanism, principle, or causal relation.\n"
            "4. Keep answers concise but explanatory; avoid trivia and vague language.\n"
            "5. Output only valid JSON that conforms to the schema—no commentary or markdown."
        )
    if preset == "procedures":
        return (
            "Follow Schema-Guided Reasoning (SGR):\n"
            "1. Inspect the JSON schema to understand required fields.\n"
            "2. Focus on procedures: steps, order, preconditions, and outcomes.\n"
            "3. Ensure one procedure or step-sequence per card; test ordering where relevant.\n"
            "4. Answers should state steps succinctly in the correct order.\n"
            "5. Output only valid JSON that conforms to the schema—no commentary or markdown."
        )
    if preset == "programming":
        return (
            "Follow Schema-Guided Reasoning (SGR):\n"
            "1. Inspect the JSON schema to understand required fields.\n"
            "2. Target APIs, invariants, edge cases, complexity, and exact terminology.\n"
            "3. Use precise names/signatures; do not invent functions or behaviors not present in the text.\n"
            "4. Keep answers factual and minimal; include tiny code snippets only if necessary (no markdown fences).\n"
            "5. Output only valid JSON that conforms to the schema—no commentary or markdown."
        )
    # default: general
    return (
        "Follow Schema-Guided Reasoning (SGR):\n"
        "1. Inspect the JSON schema to understand required fields.\n"
        "2. Plan the content you will produce so it fits the schema.\n"
        "3. Cross-check that every field is complete and consistent with the source material.\n"
        "4. Output only valid JSON that conforms to the schema—no commentary or markdown."
    )


def _sgr_reflection(preset: PresetName) -> str:
    """Return SGR instructions for the reflection phase by preset."""

    if preset == "cloze":
        return (
            "Follow Schema-Guided Reasoning (SGR):\n"
            "1. Verify each card is atomic and cloze-suitable (one key deletion).\n"
            "2. Check for ambiguity, pronouns without referents, and multi-part answers.\n"
            "3. Identify missing high-yield facts and redundancies.\n"
            "4. Output only valid JSON that conforms to the feedback schema—no commentary or markdown."
        )
    if preset == "concepts":
        return (
            "Follow Schema-Guided Reasoning (SGR):\n"
            "1. Assess conceptual depth: do cards test mechanisms and causes, not trivia.\n"
            "2. Flag vagueness and suggest sharper prompts/answers.\n"
            "3. Identify coverage gaps for core ideas; remove low-yield detail.\n"
            "4. Output only valid JSON that conforms to the feedback schema—no commentary or markdown."
        )
    if preset == "procedures":
        return (
            "Follow Schema-Guided Reasoning (SGR):\n"
            "1. Verify steps are correct, ordered, and minimal per card.\n"
            "2. Note missing preconditions/postconditions and common pitfalls.\n"
            "3. Suggest splitting compound procedures into separate cards.\n"
            "4. Output only valid JSON that conforms to the feedback schema—no commentary or markdown."
        )
    if preset == "programming":
        return (
            "Follow Schema-Guided Reasoning (SGR):\n"
            "1. Validate correctness of terminology, API names, and behavior.\n"
            "2. Check for invented details or ambiguity; prefer precise phrasing.\n"
            "3. Recommend cards about guarantees, complexity, and edge cases.\n"
            "4. Output only valid JSON that conforms to the feedback schema—no commentary or markdown."
        )
    # default: general
    return (
        "Follow Schema-Guided Reasoning (SGR):\n"
        "1. Inspect the JSON schema to understand required fields.\n"
        "2. Evaluate completeness, clarity, and accuracy against the source.\n"
        "3. Identify strengths, weaknesses, and concrete improvements.\n"
        "4. Output only valid JSON that conforms to the feedback schema—no commentary or markdown."
    )


def _sgr_improvement(preset: PresetName) -> str:
    """Return SGR instructions for the improvement phase by preset."""

    if preset == "cloze":
        return (
            "Follow Schema-Guided Reasoning (SGR):\n"
            "1. Revise to cloze-ready, single-fact cards; remove ambiguity.\n"
            "2. Split compound items; ensure answers are short noun phrases.\n"
            "3. Keep one fact per card; ensure it is answerable from the prompt alone.\n"
            "4. Output only valid JSON that conforms to the schema—no commentary or markdown."
        )
    if preset == "concepts":
        return (
            "Follow Schema-Guided Reasoning (SGR):\n"
            "1. Refactor toward mechanism/why/how questions with concise but explanatory answers.\n"
            "2. Remove low-yield trivia; add missing core concepts.\n"
            "3. Ensure each card tests a single idea.\n"
            "4. Output only valid JSON that conforms to the schema—no commentary or markdown."
        )
    if preset == "procedures":
        return (
            "Follow Schema-Guided Reasoning (SGR):\n"
            "1. Rework cards to present correct step order and necessary conditions.\n"
            "2. Split multi-step compounds; keep each card focused.\n"
            "3. Use clear, imperative phrasing where appropriate.\n"
            "4. Output only valid JSON that conforms to the schema—no commentary or markdown."
        )
    if preset == "programming":
        return (
            "Follow Schema-Guided Reasoning (SGR):\n"
            "1. Correct terminology and ensure API signatures/behaviors reflect the source.\n"
            "2. Add high-value cards (guarantees, complexity, pitfalls); remove speculation.\n"
            "3. Include minimal code snippets only if essential (no markdown).\n"
            "4. Output only valid JSON that conforms to the schema—no commentary or markdown."
        )
    # default: general
    return (
        "Follow Schema-Guided Reasoning (SGR):\n"
        "1. Address feedback precisely while preserving faithfulness to the text.\n"
        "2. Improve clarity, atomicity, and coverage; remove redundancy.\n"
        "3. Ensure every field is complete and consistent.\n"
        "4. Output only valid JSON that conforms to the schema—no commentary or markdown."
    )


def get_system_prompts(preset: PresetName = "general") -> tuple[str, str, str]:
    """Return (generation, reflection, improvement) system prompts for a preset.

    The role lines remain stable; SGR varies by preset to specialize behavior.
    """

    gen = (
        "You are an expert at creating educational flashcards for spaced repetition.\n"
        f"{_sgr_generation(preset)}\n\n"
        "You must produce JSON matching this schema:\n"
        f"{FLASHCARD_SCHEMA}\n\n"
        "The flashcards should be clear, test key concepts, and stay faithful to the provided text."
    )

    ref = (
        "You are an expert evaluator of educational flashcards.\n"
        f"{_sgr_reflection(preset)}\n\n"
        "Provide constructive feedback that follows this schema:\n"
        f"{FEEDBACK_SCHEMA}\n\n"
        "Focus on completeness, clarity, factual accuracy, educational value, and coverage."
    )

    imp = (
        "You are an expert at improving educational flashcards.\n"
        f"{_sgr_improvement(preset)}\n\n"
        "Return improved flashcards that fit this schema:\n"
        f"{FLASHCARD_SCHEMA}\n\n"
        "Ensure the revised set addresses the review feedback while staying accurate."
    )

    return gen, ref, imp


def _format_flashcards_for_prompt(cards: Iterable[Flashcard]) -> str:
    """Return a formatted JSON block of flashcards for inclusion in prompts."""

    serialised = ensure_flashcards_serializable(cards)
    return json.dumps(serialised, indent=2, ensure_ascii=False)


def _format_feedback_for_prompt(feedback: FlashcardFeedback) -> str:
    """Return a formatted JSON block of feedback for inclusion in prompts."""

    serialised = ensure_feedback_serializable(feedback)
    return json.dumps(serialised, indent=2, ensure_ascii=False)


def create_user_prompt(text_content, learning_description, improvement_context=None):
    """Create a user prompt with the text content and learning description.

    Args:
        text_content: The text content to process.
        learning_description: Description of what to learn from the text.
        improvement_context: Optional dict with 'qa_pairs' (list[Flashcard]) and 'feedback' (FlashcardFeedback).

    Returns:
        str: Formatted user prompt.
    """
    if improvement_context:
        qa_pairs_json = _format_flashcards_for_prompt(improvement_context["qa_pairs"])
        feedback_json = _format_feedback_for_prompt(improvement_context["feedback"])
        prompt = f"""Learning objective: "{learning_description}"

You are improving existing flashcards based on structured feedback.

Original flashcards:
{qa_pairs_json}

Feedback summary:
{feedback_json}

Source text:
{text_content}

Revise the flashcards so they address the feedback while staying accurate to the text."""
    else:
        prompt = f"""Learning objective: "{learning_description}"

Source text:
{text_content}

Extract essential knowledge and express it as flashcards."""
    return prompt


def create_reflection_prompt(qa_pairs, text_content, learning_description):
    """Create a reflection prompt for reviewing Q&A pairs.

    Args:
        qa_pairs: List of Flashcard models previously generated.
        text_content: The original source text.
        learning_description: Description of what to learn from the text.

    Returns:
        str: Formatted reflection prompt.
    """
    qa_pairs_json = _format_flashcards_for_prompt(qa_pairs)
    prompt = f"""Learning objective: "{learning_description}"

Source text:
{text_content}

Generated flashcards:
{qa_pairs_json}

Assess the flashcards and describe how to improve them."""
    return prompt

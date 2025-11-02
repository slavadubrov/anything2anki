"""Prompt templates for generating structured Q&A pairs from text."""

from __future__ import annotations

import json
from typing import Iterable

from .schemas import (
    Flashcard,
    FlashcardFeedback,
    FlashcardList,
    dump_json_schema,
    ensure_feedback_serializable,
    ensure_flashcards_serializable,
)


SCHEMA_GUIDED_REASONING_INSTRUCTIONS = """Follow Schema-Guided Reasoning (SGR):
1. Inspect the JSON schema to understand required fields.
2. Plan the content you will produce so it fits the schema.
3. Cross-check that every field is complete and consistent with the source material.
4. Output only valid JSON that conforms to the schema—no commentary or markdown."""

FLASHCARD_SCHEMA = dump_json_schema(FlashcardList)
FEEDBACK_SCHEMA = dump_json_schema(FlashcardFeedback)

GENERATION_PROMPT = f"""You are an expert at creating educational flashcards for spaced repetition.
{SCHEMA_GUIDED_REASONING_INSTRUCTIONS}

You must produce JSON matching this schema:
{FLASHCARD_SCHEMA}

The flashcards should be clear, test key concepts, and stay faithful to the provided text."""

REFLECTION_PROMPT = f"""You are an expert evaluator of educational flashcards.
{SCHEMA_GUIDED_REASONING_INSTRUCTIONS}

Provide constructive feedback that follows this schema:
{FEEDBACK_SCHEMA}

Focus on completeness, clarity, factual accuracy, educational value, and coverage."""

IMPROVEMENT_PROMPT = f"""You are an expert at improving educational flashcards.
{SCHEMA_GUIDED_REASONING_INSTRUCTIONS}

Return improved flashcards that fit this schema:
{FLASHCARD_SCHEMA}

Ensure the revised set addresses the review feedback while staying accurate."""


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

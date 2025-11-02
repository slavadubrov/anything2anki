"""Main workflow for generating Anki cards from text files using AI."""

import os
from pathlib import Path
from typing import Sequence

import aisuite as ai
from genanki import Note, Package
from pydantic import ValidationError

from .anki_model import create_deck, create_qa_model
from .constants import DEFAULT_MODEL
from .prompts import (
    GENERATION_PROMPT,
    IMPROVEMENT_PROMPT,
    REFLECTION_PROMPT,
    create_reflection_prompt,
    create_user_prompt,
)
from .schemas import Flashcard, FlashcardFeedback, FlashcardList, FlashcardValidationError


def validate_input_file(file_path: str) -> None:
    """Validate that the input file exists and is a file.

    Args:
        file_path: Path to the input file.

    Raises:
        FileNotFoundError: If the input file doesn't exist.
        ValueError: If the path is not a file.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Input file not found: {file_path}")

    if not os.path.isfile(file_path):
        raise ValueError(f"Path is not a file: {file_path}")


def read_input_file(file_path: str) -> str:
    """Read and return the content of the input file.

    Args:
        file_path: Path to the input file.

    Returns:
        str: The file content.

    Raises:
        ValueError: If the file is empty.
        Exception: If there's an error reading the file.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            text_content = f.read()
    except Exception as e:
        raise Exception(f"Error reading file {file_path}: {e}")

    if not text_content.strip():
        raise ValueError(f"Input file is empty: {file_path}")

    return text_content


def call_ai_model(
    client: ai.Client, model: str, system_prompt: str, user_prompt: str
) -> str:
    """Call the AI model and return the response content.

    Args:
        client: The aisuite client instance.
        model: The AI model to use.
        system_prompt: The system prompt.
        user_prompt: The user prompt.

    Returns:
        str: The response content from the AI model.

    Raises:
        Exception: If there's an error calling the AI model.
    """
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
    except Exception as e:
        raise Exception(f"Error calling AI model: {e}")

    return response.choices[0].message.content.strip()


def parse_ai_response(response_content: str) -> list[Flashcard]:
    """Extract and parse flashcards from the AI response.

    Args:
        response_content: The raw response content from the AI model.

    Returns:
        list[Flashcard]: A list of validated flashcards.

    Raises:
        ValueError: If the response cannot be parsed as JSON or is invalid.
    """
    # Try to extract JSON from response (handle markdown code blocks)
    json_start = response_content.find("[")
    json_end = response_content.rfind("]") + 1

    if json_start == -1 or json_end == 0:
        raise ValueError(
            f"Could not find JSON array in response. Response: {response_content[:200]}"
        )

    json_str = response_content[json_start:json_end]

    try:
        qa_pairs = FlashcardList.model_validate_json(json_str)
    except ValidationError as err:
        formatted_error = FlashcardValidationError.from_validation_error(err)
        raise ValueError(
            f"Flashcard schema validation failed: {formatted_error}. Response: {response_content[:500]}"
        ) from err

    return qa_pairs.root


def parse_feedback_response(response_content: str) -> FlashcardFeedback:
    """Extract and parse structured feedback from the AI response.

    Args:
        response_content: The raw response content from the AI model.

    Returns:
        FlashcardFeedback: Structured feedback covering strengths, weaknesses, recommendations, and overall quality.

    Raises:
        ValueError: If the response cannot be parsed as JSON or is invalid.
    """
    # Try to extract JSON from response (handle markdown code blocks)
    json_start = response_content.find("{")
    json_end = response_content.rfind("}") + 1

    feedback = None
    if json_start != -1 and json_end != 0:
        json_str = response_content[json_start:json_end]
        target = json_str
    else:
        target = response_content

    try:
        feedback = FlashcardFeedback.model_validate_json(target)
    except ValidationError as err:
        formatted_error = FlashcardValidationError.from_validation_error(err)
        raise ValueError(
            f"Feedback schema validation failed: {formatted_error}. Response: {response_content[:500]}"
        ) from err

    return feedback


def generate_qa_pairs(
    client: ai.Client,
    model: str,
    text_content: str,
    learning_description: str,
    improvement_context: dict | None = None,
) -> list[Flashcard]:
    """Generate Q&A pairs from text content using AI.

    Args:
        client: The aisuite client instance.
        model: The AI model to use.
        text_content: The text content to process.
        learning_description: Description of what to learn from the text.
        improvement_context: Optional dict with 'qa_pairs' and 'feedback' for improvement.

    Returns:
        list[Flashcard]: A list of validated flashcards.

    Raises:
        Exception: If there's an error calling the AI model or parsing the response.
    """
    user_prompt = create_user_prompt(
        text_content, learning_description, improvement_context
    )
    # Use IMPROVEMENT_PROMPT when improving, otherwise use GENERATION_PROMPT
    system_prompt = IMPROVEMENT_PROMPT if improvement_context else GENERATION_PROMPT
    response_content = call_ai_model(client, model, system_prompt, user_prompt)
    return parse_ai_response(response_content)


def reflect_on_qa_pairs(
    client: ai.Client,
    model: str,
    qa_pairs: list[Flashcard],
    text_content: str,
    learning_description: str,
) -> FlashcardFeedback:
    """Review Q&A pairs and generate feedback for improvement.

    Args:
        client: The aisuite client instance.
        model: The AI model to use.
        qa_pairs: List of generated flashcards to review.
        text_content: The original source text.
        learning_description: Description of what to learn from the text.

    Returns:
        FlashcardFeedback: Structured feedback capturing strengths, weaknesses, recommendations, and overall quality.

    Raises:
        Exception: If there's an error calling the AI model or parsing the response.
    """
    reflection_prompt = create_reflection_prompt(
        qa_pairs, text_content, learning_description
    )
    response_content = call_ai_model(
        client, model, REFLECTION_PROMPT, reflection_prompt
    )
    return parse_feedback_response(response_content)


def improve_qa_pairs(
    client: ai.Client,
    model: str,
    qa_pairs: list[Flashcard],
    feedback: FlashcardFeedback,
    text_content: str,
    learning_description: str,
) -> list[Flashcard]:
    """Generate improved Q&A pairs based on feedback.

    Args:
        client: The aisuite client instance.
        model: The AI model to use.
        qa_pairs: Original list of flashcards.
        feedback: Structured feedback from the reflection step.
        text_content: The original source text.
        learning_description: Description of what to learn from the text.

    Returns:
        list[Flashcard]: Improved list of flashcards.

    Raises:
        Exception: If there's an error calling the AI model or parsing the response.
    """
    improvement_context = {"qa_pairs": qa_pairs, "feedback": feedback}
    return generate_qa_pairs(
        client, model, text_content, learning_description, improvement_context
    )


def build_anki_deck(qa_pairs: Sequence[Flashcard]) -> tuple:
    """Build an Anki deck from validated flashcards.

    Args:
        qa_pairs: Sequence of validated flashcards.

    Returns:
        tuple: A tuple containing (model, deck).

    Raises:
        ValueError: If no valid Q&A pairs are found.
    """
    cards = list(qa_pairs)
    if not cards:
        raise ValueError("No valid Q&A pairs found in the response")

    model = create_qa_model()
    deck = create_deck()

    for card in cards:
        note = Note(
            model=model,
            fields=[card.question, card.answer],
        )
        deck.add_note(note)

    if len(deck.notes) == 0:  # pragma: no cover - defensive guard
        raise ValueError("No valid Q&A pairs found in the response")

    return model, deck


def generate_md_report(qa_pairs: Sequence[Flashcard], output_path: str) -> str:
    """Generate a markdown report file showing the flashcards.

    Args:
        qa_pairs: Sequence of flashcards to document.
        output_path: Path where the .apkg file will be saved.

    Returns:
        str: Path to the generated markdown file.
    """
    cards = list(qa_pairs)
    md_path = str(Path(output_path).with_suffix(".md"))

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# Anki Cards Preview\n\n")
        f.write(f"Total cards: {len(cards)}\n\n")
        f.write("---\n\n")

        for idx, card in enumerate(cards, start=1):
            f.write(f"## Card {idx}\n\n")
            f.write(f"**Q:** {card.question}\n\n")
            f.write(f"**A:** {card.answer}\n\n")
            f.write("---\n\n")

    return md_path


def write_anki_package(deck, output_path: str) -> None:
    """Write the Anki deck to a .apkg file.

    Args:
        deck: The genanki Deck instance.
        output_path: Path where the .apkg file should be saved.

    Raises:
        Exception: If there's an error creating the package.
    """
    try:
        package = Package(deck)
        package.write_to_file(output_path)
    except Exception as e:
        raise Exception(f"Error creating Anki package: {e}")


def generate_anki_cards(
    file_path: str,
    learning_description: str,
    output_path: str,
    model: str = DEFAULT_MODEL,
    preview_only: bool = False,
    max_reflections: int = 1,
):
    """Generate Anki cards from a text file using AI with reflection pattern.

    Args:
        file_path: Path to the input text file.
        learning_description: Description of what to learn from the file.
        output_path: Path where the .apkg file should be saved.
        model: AI model to use (default: DEFAULT_MODEL).
        preview_only: If True, generate only the Markdown preview and skip .apkg creation.
        max_reflections: Maximum number of reflection-improvement cycles (default: 1).

    Raises:
        FileNotFoundError: If the input file doesn't exist.
        ValueError: If the LLM response cannot be parsed as JSON.
        Exception: For other errors during processing.
    """
    # Validate input file
    validate_input_file(file_path)

    # Read input file
    text_content = read_input_file(file_path)

    # Initialize aisuite client
    client = ai.Client()

    # Step 1: Initial generation
    print("Generating initial Q&A pairs...")
    qa_pairs = generate_qa_pairs(client, model, text_content, learning_description)
    print(f"Generated {len(qa_pairs)} initial Q&A pairs")

    # If no pairs were generated initially, bail out before reflection
    if not qa_pairs:
        raise ValueError("No valid Q&A pairs found")

    # If preview-only, generate the markdown now and return without reflection
    if preview_only:
        md_path = generate_md_report(qa_pairs, output_path)
        print(f"\nPreview report saved to: {md_path}")
        return

    # Step 2: Reflection and improvement loop (only when we have some pairs)
    for reflection_num in range(max_reflections):
        print(f"\nReflection cycle {reflection_num + 1}/{max_reflections}...")

        # Reflect on current Q&A pairs
        feedback = reflect_on_qa_pairs(
            client, model, qa_pairs, text_content, learning_description
        )
        print(
            f"Reflection complete. Overall quality: {feedback.get('overall_quality', 'unknown')}"
        )

        # Improve Q&A pairs based on feedback
        qa_pairs = improve_qa_pairs(
            client, model, qa_pairs, feedback, text_content, learning_description
        )
        print(f"Improved to {len(qa_pairs)} Q&A pairs")

    # Generate markdown report
    md_path = generate_md_report(qa_pairs, output_path)

    # Build Anki deck
    _, deck = build_anki_deck(qa_pairs)

    # Write Anki package
    write_anki_package(deck, output_path)

    print(f"\nSuccessfully generated {len(deck.notes)} Anki cards!")
    print(f"Saved to: {output_path}")
    print(f"Preview report saved to: {md_path}")

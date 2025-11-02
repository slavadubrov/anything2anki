"""Main workflow for generating Anki cards from text files using AI."""

import json
import os
from pathlib import Path

import aisuite as ai
from genanki import Note, Package

from .anki_model import create_deck, create_qa_model
from .constants import DEFAULT_MODEL
from .prompts import SYSTEM_PROMPT, create_user_prompt


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


def parse_ai_response(response_content: str) -> list[dict]:
    """Extract and parse JSON from the AI response.

    Args:
        response_content: The raw response content from the AI model.

    Returns:
        list[dict]: A list of Q&A pairs.

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

    # Parse JSON
    try:
        qa_pairs = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Could not parse JSON response: {e}. Response: {response_content[:500]}"
        )

    if not isinstance(qa_pairs, list):
        raise ValueError("JSON response is not a list")

    if len(qa_pairs) == 0:
        raise ValueError("No Q&A pairs generated from the text")

    return qa_pairs


def build_anki_deck(qa_pairs: list[dict]) -> tuple:
    """Build an Anki deck from Q&A pairs.

    Args:
        qa_pairs: List of dictionaries with "question" and "answer" keys.

    Returns:
        tuple: A tuple containing (model, deck).

    Raises:
        ValueError: If no valid Q&A pairs are found.
    """
    model = create_qa_model()
    deck = create_deck()

    # Add notes to deck
    for qa in qa_pairs:
        if not isinstance(qa, dict):
            continue

        question = qa.get("question", "")
        answer = qa.get("answer", "")

        if not question or not answer:
            continue

        note = Note(
            model=model,
            fields=[question, answer],
        )
        deck.add_note(note)

    if len(deck.notes) == 0:
        raise ValueError("No valid Q&A pairs found in the response")

    return model, deck


def generate_md_report(qa_pairs: list[dict], output_path: str) -> str:
    """Generate a markdown report file showing the Q&A pairs.

    Args:
        qa_pairs: List of dictionaries with "question" and "answer" keys.
        output_path: Path where the .apkg file will be saved.

    Returns:
        str: Path to the generated markdown file.
    """
    # Generate markdown file path by replacing .apkg extension with .md
    md_path = str(Path(output_path).with_suffix(".md"))

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# Anki Cards Preview\n\n")
        f.write(f"Total cards: {len(qa_pairs)}\n\n")
        f.write("---\n\n")

        for idx, qa in enumerate(qa_pairs, start=1):
            if not isinstance(qa, dict):
                continue

            question = qa.get("question", "")
            answer = qa.get("answer", "")

            if not question or not answer:
                continue

            f.write(f"## Card {idx}\n\n")
            f.write(f"**Q:** {question}\n\n")
            f.write(f"**A:** {answer}\n\n")
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
):
    """Generate Anki cards from a text file using AI.

    Args:
        file_path: Path to the input text file.
        learning_description: Description of what to learn from the file.
        output_path: Path where the .apkg file should be saved.
        model: AI model to use (default: DEFAULT_MODEL).
        preview_only: If True, generate only the Markdown preview and skip .apkg creation.

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

    # Create prompts
    user_prompt = create_user_prompt(text_content, learning_description)

    # Call AI model
    response_content = call_ai_model(client, model, SYSTEM_PROMPT, user_prompt)

    # Parse AI response
    qa_pairs = parse_ai_response(response_content)

    # Generate markdown report
    md_path = generate_md_report(qa_pairs, output_path)

    # If preview-only, skip building/writing the Anki package
    if preview_only:
        print(f"Preview report saved to: {md_path}")
        return

    # Build Anki deck
    _, deck = build_anki_deck(qa_pairs)

    # Write Anki package
    write_anki_package(deck, output_path)

    print(f"Successfully generated {len(deck.notes)} Anki cards!")
    print(f"Saved to: {output_path}")
    print(f"Preview report saved to: {md_path}")

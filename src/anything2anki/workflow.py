"""Main workflow for generating Anki cards from text files using AI."""

import json
import os
import aisuite as ai
from genanki import Note, Package

from .anki_model import create_qa_model, create_deck
from .prompts import SYSTEM_PROMPT, create_user_prompt


def generate_anki_cards(
    file_path: str,
    learning_description: str,
    output_path: str,
    model: str = "openai:gpt-4o",
):
    """Generate Anki cards from a text file using AI.

    Args:
        file_path: Path to the input text file.
        learning_description: Description of what to learn from the file.
        output_path: Path where the .apkg file should be saved.
        model: AI model to use (default: "openai:gpt-4o").

    Raises:
        FileNotFoundError: If the input file doesn't exist.
        ValueError: If the LLM response cannot be parsed as JSON.
        Exception: For other errors during processing.
    """
    # Validate input file
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Input file not found: {file_path}")

    if not os.path.isfile(file_path):
        raise ValueError(f"Path is not a file: {file_path}")

    # Read input file
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            text_content = f.read()
    except Exception as e:
        raise Exception(f"Error reading file {file_path}: {e}")

    if not text_content.strip():
        raise ValueError(f"Input file is empty: {file_path}")

    # Initialize aisuite client
    client = ai.Client()

    # Create prompts
    user_prompt = create_user_prompt(text_content, learning_description)

    # Call AI model
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )
    except Exception as e:
        raise Exception(f"Error calling AI model: {e}")

    # Extract response content
    response_content = response.choices[0].message.content.strip()

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

    # Create Anki deck
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

    # Create package and write to file
    try:
        package = Package(deck)
        package.write_to_file(output_path)
    except Exception as e:
        raise Exception(f"Error creating Anki package: {e}")

    print(f"Successfully generated {len(deck.notes)} Anki cards!")
    print(f"Saved to: {output_path}")

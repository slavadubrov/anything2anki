"""Command-line interface for anything2anki."""

import argparse
import sys
from pathlib import Path

from .constants import DEFAULT_MODEL
from .workflow import generate_anki_cards


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate Anki cards from text files using AI"
    )
    parser.add_argument(
        "file_path",
        type=str,
        help="Path to the input text file",
    )
    parser.add_argument(
        "learning_description",
        type=str,
        help="Description of what to learn from the file",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Output path for the .apkg file (default: <input_filename>.apkg)",
    )
    parser.add_argument(
        "--model",
        "-m",
        type=str,
        default=DEFAULT_MODEL,
        help=f'AI model to use (default: "{DEFAULT_MODEL}")',
    )
    parser.add_argument(
        "--preview-only",
        action="store_true",
        help="Only generate the Markdown preview report; skip creating the .apkg deck",
    )

    args = parser.parse_args()

    # Generate output path if not provided
    if args.output is None:
        input_path = Path(args.file_path)
        args.output = str(input_path.with_suffix(".apkg"))

    # Run workflow
    try:
        generate_anki_cards(
            file_path=args.file_path,
            learning_description=args.learning_description,
            output_path=args.output,
            model=args.model,
            preview_only=args.preview_only,
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

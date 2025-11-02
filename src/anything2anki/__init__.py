"""Anything2Anki - Generate Anki cards from text files using AI."""

from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

__version__ = "0.1.0"

from .workflow import generate_anki_cards

__all__ = ["generate_anki_cards"]

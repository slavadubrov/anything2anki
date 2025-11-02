"""Anki card model definition using genanki."""

import genanki

from .constants import (
    ANKI_AFMT,
    ANKI_DECK_ID,
    ANKI_MODEL_ID,
    ANKI_MODEL_NAME,
    ANKI_QFMT,
    ANKI_TEMPLATE_NAME,
    DEFAULT_DECK_NAME,
)


def create_qa_model():
    """Create a simple Q&A Anki model.

    Returns:
        genanki.Model: An Anki model with Question and Answer fields.
    """
    model = genanki.Model(
        model_id=ANKI_MODEL_ID,
        name=ANKI_MODEL_NAME,
        fields=[
            {"name": "Question"},
            {"name": "Answer"},
        ],
        templates=[
            {
                "name": ANKI_TEMPLATE_NAME,
                "qfmt": ANKI_QFMT,
                "afmt": ANKI_AFMT,
            },
        ],
    )
    return model


def create_deck(deck_name=DEFAULT_DECK_NAME):
    """Create an Anki deck.

    Args:
        deck_name: Name of the deck.

    Returns:
        genanki.Deck: An Anki deck instance.
    """
    deck = genanki.Deck(
        deck_id=ANKI_DECK_ID,
        name=deck_name,
    )
    return deck

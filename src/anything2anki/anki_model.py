"""Anki card model definition using genanki."""

import genanki


def create_qa_model():
    """Create a simple Q&A Anki model.

    Returns:
        genanki.Model: An Anki model with Question and Answer fields.
    """
    model = genanki.Model(
        model_id=1607392319,
        name="Simple Q&A Model",
        fields=[
            {"name": "Question"},
            {"name": "Answer"},
        ],
        templates=[
            {
                "name": "Card 1",
                "qfmt": "{{Question}}",
                "afmt": '{{FrontSide}}<hr id="answer">{{Answer}}',
            },
        ],
    )
    return model


def create_deck(deck_name="Generated Deck"):
    """Create an Anki deck.

    Args:
        deck_name: Name of the deck.

    Returns:
        genanki.Deck: An Anki deck instance.
    """
    deck = genanki.Deck(
        deck_id=2059400110,
        name=deck_name,
    )
    return deck

"""Pydantic models describing the Anything2Anki data structures."""

import json
from typing import Iterable, Sequence

from pydantic import (
    BaseModel,
    Field,
    RootModel,
    ValidationError,
    field_validator,
    model_validator,
)


class Flashcard(BaseModel):
    """Structured representation of a single flashcard."""

    question: str = Field(..., description="The prompt the learner should answer")
    answer: str = Field(..., description="The canonical answer for the prompt")

    @field_validator("question", "answer", mode="before")
    @classmethod
    def _ensure_trimmed(cls, value: str) -> str:
        if isinstance(value, str):
            value = value.strip()
        if not value:
            raise ValueError("Value must be a non-empty string")
        return value


class FlashcardList(RootModel[list[Flashcard]]):
    """Root model used to request/validate a list of flashcards."""

    root: list[Flashcard]

    @model_validator(mode="after")
    def _ensure_non_empty(cls, values: "FlashcardList") -> "FlashcardList":
        if not values.root:
            raise ValueError("At least one flashcard must be provided")
        return values

    def __iter__(self):  # pragma: no cover - behaviour provided for convenience
        return iter(self.root)

    def __len__(self):  # pragma: no cover
        return len(self.root)

    def to_dicts(self) -> list[dict[str, str]]:
        """Return the flashcards as primitive dictionaries."""

        return [card.model_dump() for card in self.root]


class FlashcardFeedback(BaseModel):
    """Structured feedback returned by the reflection step."""

    strengths: list[str] = Field(
        ..., description="Positive aspects of the flashcards", min_length=1
    )
    weaknesses: list[str] = Field(
        ..., description="Issues that need to be addressed", min_length=1
    )
    recommendations: list[str] = Field(
        ..., description="Actionable suggestions", min_length=1
    )
    overall_quality: str = Field(
        ..., description="Summary judgement of the flashcard set"
    )

    @field_validator("strengths", "weaknesses", "recommendations")
    @classmethod
    def _validate_non_empty_items(cls, values: Sequence[str]) -> Sequence[str]:
        cleaned: list[str] = []
        for item in values:
            item = item.strip()
            if item:
                cleaned.append(item)
        if not cleaned:
            raise ValueError("List must contain at least one non-empty item")
        return cleaned

    @field_validator("overall_quality", mode="before")
    @classmethod
    def _trim_quality(cls, value: str) -> str:
        if isinstance(value, str):
            value = value.strip()
        if not value:
            raise ValueError("overall_quality must be a non-empty string")
        return value


def dump_json_schema(model: type[BaseModel]) -> str:
    """Return the JSON schema for a Pydantic model formatted for prompting."""

    return json.dumps(model.model_json_schema(), indent=2, ensure_ascii=False)


def ensure_flashcards_serializable(
    cards: Iterable[Flashcard],
) -> list[dict[str, str]]:
    """Normalize flashcards into serialisable dictionaries for prompts.

    Accepts only validated Flashcard models.
    """

    return [card.model_dump() for card in cards]


def ensure_feedback_serializable(feedback: FlashcardFeedback) -> dict[str, object]:
    """Normalise feedback structures for prompt rendering.

    Accepts only validated FlashcardFeedback models.
    """

    return feedback.model_dump()


class FlashcardValidationError(ValueError):
    """Wrap pydantic validation errors to simplify upstream handling."""

    @classmethod
    def from_validation_error(cls, err: ValidationError) -> "FlashcardValidationError":
        return cls(str(err))


# JSON schema strings for prompting (defined alongside models)
FLASHCARD_SCHEMA = json.dumps(
    FlashcardList.model_json_schema(), indent=2, ensure_ascii=False
)
FEEDBACK_SCHEMA = json.dumps(
    FlashcardFeedback.model_json_schema(), indent=2, ensure_ascii=False
)

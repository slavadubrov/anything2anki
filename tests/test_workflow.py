"""Tests for workflow module."""

import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from anything2anki.workflow import (
    build_anki_deck,
    call_ai_model,
    generate_anki_cards,
    generate_md_report,
    generate_qa_pairs,
    improve_qa_pairs,
    parse_ai_response,
    parse_feedback_response,
    read_input_file,
    reflect_on_qa_pairs,
    validate_input_file,
    write_anki_package,
)


class TestValidateInputFile:
    """Tests for validate_input_file function."""

    def test_validate_input_file_exists(self, tmp_path):
        """Test validation passes for existing file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        validate_input_file(str(test_file))

    def test_validate_input_file_not_exists(self):
        """Test validation raises FileNotFoundError for non-existent file."""
        with pytest.raises(FileNotFoundError):
            validate_input_file("/nonexistent/file.txt")

    def test_validate_input_file_is_directory(self, tmp_path):
        """Test validation raises ValueError for directory."""
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()
        with pytest.raises(ValueError, match="Path is not a file"):
            validate_input_file(str(test_dir))


class TestReadInputFile:
    """Tests for read_input_file function."""

    def test_read_input_file_success(self, tmp_path):
        """Test successful file reading."""
        test_file = tmp_path / "test.txt"
        content = "test content"
        test_file.write_text(content, encoding="utf-8")
        result = read_input_file(str(test_file))
        assert result == content

    def test_read_input_file_empty(self, tmp_path):
        """Test reading empty file raises ValueError."""
        test_file = tmp_path / "empty.txt"
        test_file.write_text("")
        with pytest.raises(ValueError, match="Input file is empty"):
            read_input_file(str(test_file))

    def test_read_input_file_whitespace_only(self, tmp_path):
        """Test reading file with only whitespace raises ValueError."""
        test_file = tmp_path / "whitespace.txt"
        test_file.write_text("   \n\t  ")
        with pytest.raises(ValueError, match="Input file is empty"):
            read_input_file(str(test_file))

    def test_read_input_file_not_found(self):
        """Test reading non-existent file raises Exception."""
        with pytest.raises(Exception, match="Error reading file"):
            read_input_file("/nonexistent/file.txt")


class TestCallAiModel:
    """Tests for call_ai_model function."""

    def test_call_ai_model_success(self):
        """Test successful AI model call."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "test response"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response

        result = call_ai_model(
            mock_client, "test-model", "system prompt", "user prompt"
        )

        assert result == "test response"
        mock_client.chat.completions.create.assert_called_once_with(
            model="test-model",
            messages=[
                {"role": "system", "content": "system prompt"},
                {"role": "user", "content": "user prompt"},
            ],
        )

    def test_call_ai_model_error(self):
        """Test AI model call with error raises Exception."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API error")

        with pytest.raises(Exception, match="Error calling AI model"):
            call_ai_model(mock_client, "test-model", "system prompt", "user prompt")


class TestParseAiResponse:
    """Tests for parse_ai_response function."""

    def test_parse_ai_response_valid_json(self):
        """Test parsing valid JSON response."""
        qa_pairs = [
            {"question": "Q1", "answer": "A1"},
            {"question": "Q2", "answer": "A2"},
        ]
        response = json.dumps(qa_pairs)
        result = parse_ai_response(response)
        assert result == qa_pairs

    def test_parse_ai_response_with_markdown(self):
        """Test parsing JSON wrapped in markdown code blocks."""
        qa_pairs = [
            {"question": "Q1", "answer": "A1"},
            {"question": "Q2", "answer": "A2"},
        ]
        response = f"Here's the JSON:\n```json\n{json.dumps(qa_pairs)}\n```"
        result = parse_ai_response(response)
        assert result == qa_pairs

    def test_parse_ai_response_no_json_array(self):
        """Test parsing response without JSON array raises ValueError."""
        response = "This is not JSON"
        with pytest.raises(ValueError, match="Could not find JSON array"):
            parse_ai_response(response)

    def test_parse_ai_response_invalid_json(self):
        """Test parsing invalid JSON raises ValueError."""
        response = "[invalid json"
        with pytest.raises(ValueError, match="Could not find JSON array"):
            parse_ai_response(response)

    def test_parse_ai_response_not_list(self):
        """Test parsing JSON that's not a list raises ValueError."""
        response = '{"not": "a list"}'
        with pytest.raises(ValueError, match="Could not find JSON array"):
            parse_ai_response(response)

    def test_parse_ai_response_empty_list(self):
        """Test parsing empty list raises ValueError."""
        response = "[]"
        with pytest.raises(ValueError, match="No Q&A pairs generated"):
            parse_ai_response(response)


class TestBuildAnkiDeck:
    """Tests for build_anki_deck function."""

    def test_build_anki_deck_valid_pairs(self):
        """Test building deck with valid Q&A pairs."""
        qa_pairs = [
            {"question": "Q1", "answer": "A1"},
            {"question": "Q2", "answer": "A2"},
        ]
        model, deck = build_anki_deck(qa_pairs)
        assert model is not None
        assert deck is not None
        assert len(deck.notes) == 2

    def test_build_anki_deck_invalid_dict(self):
        """Test building deck skips invalid dictionaries."""
        qa_pairs = [
            {"question": "Q1", "answer": "A1"},
            "not a dict",
            {"question": "Q2", "answer": "A2"},
        ]
        model, deck = build_anki_deck(qa_pairs)
        assert len(deck.notes) == 2

    def test_build_anki_deck_missing_fields(self):
        """Test building deck skips pairs with missing fields."""
        qa_pairs = [
            {"question": "Q1", "answer": "A1"},
            {"question": "Q2"},  # missing answer
            {"answer": "A3"},  # missing question
            {"question": "", "answer": "A4"},  # empty question
            {"question": "Q5", "answer": ""},  # empty answer
        ]
        model, deck = build_anki_deck(qa_pairs)
        assert len(deck.notes) == 1

    def test_build_anki_deck_no_valid_pairs(self):
        """Test building deck with no valid pairs raises ValueError."""
        qa_pairs = [
            {"question": "", "answer": "A1"},
            {"question": "Q2"},
        ]
        with pytest.raises(ValueError, match="No valid Q&A pairs found"):
            build_anki_deck(qa_pairs)

    def test_build_anki_deck_empty_list(self):
        """Test building deck with empty list raises ValueError."""
        with pytest.raises(ValueError, match="No valid Q&A pairs found"):
            build_anki_deck([])


class TestGenerateMdReport:
    """Tests for generate_md_report function."""

    def test_generate_md_report_success(self, tmp_path):
        """Test successful MD report generation."""
        qa_pairs = [
            {"question": "Q1", "answer": "A1"},
            {"question": "Q2", "answer": "A2"},
        ]
        output_path = str(tmp_path / "deck.apkg")
        md_path = generate_md_report(qa_pairs, output_path)

        assert md_path == str(tmp_path / "deck.md")
        assert os.path.exists(md_path)

        content = Path(md_path).read_text(encoding="utf-8")
        assert "Total cards: 2" in content
        assert "## Card 1" in content
        assert "**Q:** Q1" in content
        assert "**A:** A1" in content
        assert "## Card 2" in content
        assert "**Q:** Q2" in content
        assert "**A:** A2" in content

    def test_generate_md_report_filters_invalid(self, tmp_path):
        """Test MD report generation filters invalid pairs."""
        qa_pairs = [
            {"question": "Q1", "answer": "A1"},
            {"question": "", "answer": "A2"},  # invalid
            "not a dict",  # invalid
            {"question": "Q3", "answer": "A3"},
        ]
        output_path = str(tmp_path / "deck.apkg")
        md_path = generate_md_report(qa_pairs, output_path)

        content = Path(md_path).read_text(encoding="utf-8")
        assert "Total cards: 4" in content  # Count includes all
        assert "## Card 1" in content
        assert "**Q:** Q1" in content
        assert "## Card 4" in content  # Card 4 is the 4th item in list (skips invalid)
        assert "**Q:** Q3" in content
        # Verify invalid pairs are not included
        assert "A2" not in content  # Invalid pair should not appear
        assert "Card 2" not in content
        assert "Card 3" not in content


class TestWriteAnkiPackage:
    """Tests for write_anki_package function."""

    def test_write_anki_package_success(self, tmp_path):
        """Test successful package writing."""
        mock_deck = MagicMock()
        output_path = str(tmp_path / "deck.apkg")

        with patch("anything2anki.workflow.Package") as mock_package_class:
            mock_package = MagicMock()
            mock_package_class.return_value = mock_package
            write_anki_package(mock_deck, output_path)

            mock_package_class.assert_called_once_with(mock_deck)
            mock_package.write_to_file.assert_called_once_with(output_path)

    def test_write_anki_package_error(self, tmp_path):
        """Test package writing with error raises Exception."""
        mock_deck = MagicMock()
        output_path = str(tmp_path / "deck.apkg")

        with patch("anything2anki.workflow.Package") as mock_package_class:
            mock_package = MagicMock()
            mock_package.write_to_file.side_effect = Exception("Write error")
            mock_package_class.return_value = mock_package

            with pytest.raises(Exception, match="Error creating Anki package"):
                write_anki_package(mock_deck, output_path)


class TestParseFeedbackResponse:
    """Tests for parse_feedback_response function."""

    def test_parse_feedback_response_valid_json(self):
        """Test parsing valid JSON feedback response."""
        feedback = {
            "strengths": ["Clear questions", "Concise answers"],
            "weaknesses": ["Missing key concept"],
            "recommendations": ["Add question about X"],
            "overall_quality": "good",
        }
        response = json.dumps(feedback)
        result = parse_feedback_response(response)
        assert result == feedback

    def test_parse_feedback_response_with_markdown(self):
        """Test parsing JSON wrapped in markdown code blocks."""
        feedback = {
            "strengths": ["Clear questions"],
            "weaknesses": ["Missing concept"],
            "recommendations": ["Add question"],
            "overall_quality": "needs improvement",
        }
        response = f"Here's the feedback:\n```json\n{json.dumps(feedback)}\n```"
        result = parse_feedback_response(response)
        assert result == feedback

    def test_parse_feedback_response_no_json_object(self):
        """Test parsing response without JSON object raises ValueError."""
        response = "This is not JSON"
        with pytest.raises(ValueError, match="Could not find JSON object"):
            parse_feedback_response(response)

    def test_parse_feedback_response_not_dict(self):
        """Test parsing JSON that's not a dict raises ValueError."""
        response = '["not", "a", "dict"]'
        with pytest.raises(
            ValueError, match="JSON feedback response is not a dictionary"
        ):
            parse_feedback_response(response)

    def test_parse_feedback_response_missing_fields(self):
        """Test parsing feedback with missing required fields raises ValueError."""
        feedback = {"strengths": ["Good"]}
        response = json.dumps(feedback)
        with pytest.raises(ValueError, match="Missing required field in feedback"):
            parse_feedback_response(response)


class TestGenerateQaPairs:
    """Tests for generate_qa_pairs function."""

    @patch("anything2anki.workflow.create_user_prompt")
    @patch("anything2anki.workflow.call_ai_model")
    @patch("anything2anki.workflow.parse_ai_response")
    def test_generate_qa_pairs_success(
        self, mock_parse, mock_call_ai, mock_create_prompt
    ):
        """Test successful Q&A pair generation."""
        mock_client = MagicMock()
        mock_create_prompt.return_value = "user prompt"
        mock_call_ai.return_value = "response content"
        qa_pairs = [{"question": "Q1", "answer": "A1"}]
        mock_parse.return_value = qa_pairs

        result = generate_qa_pairs(mock_client, "test-model", "text", "description")

        assert result == qa_pairs
        mock_create_prompt.assert_called_once_with("text", "description", None)
        mock_call_ai.assert_called_once()
        mock_parse.assert_called_once_with("response content")

    @patch("anything2anki.workflow.create_user_prompt")
    @patch("anything2anki.workflow.call_ai_model")
    @patch("anything2anki.workflow.parse_ai_response")
    def test_generate_qa_pairs_with_improvement_context(
        self, mock_parse, mock_call_ai, mock_create_prompt
    ):
        """Test Q&A pair generation with improvement context."""
        mock_client = MagicMock()
        improvement_context = {
            "qa_pairs": [{"question": "Q1", "answer": "A1"}],
            "feedback": {"overall_quality": "good"},
        }
        mock_create_prompt.return_value = "user prompt"
        mock_call_ai.return_value = "response content"
        qa_pairs = [{"question": "Q2", "answer": "A2"}]
        mock_parse.return_value = qa_pairs

        result = generate_qa_pairs(
            mock_client,
            "test-model",
            "text",
            "description",
            improvement_context,
        )

        assert result == qa_pairs
        mock_create_prompt.assert_called_once_with(
            "text", "description", improvement_context
        )


class TestReflectOnQaPairs:
    """Tests for reflect_on_qa_pairs function."""

    @patch("anything2anki.workflow.create_reflection_prompt")
    @patch("anything2anki.workflow.call_ai_model")
    @patch("anything2anki.workflow.parse_feedback_response")
    def test_reflect_on_qa_pairs_success(
        self, mock_parse, mock_call_ai, mock_create_prompt
    ):
        """Test successful reflection on Q&A pairs."""
        mock_client = MagicMock()
        qa_pairs = [{"question": "Q1", "answer": "A1"}]
        mock_create_prompt.return_value = "reflection prompt"
        mock_call_ai.return_value = "feedback response"
        feedback = {
            "strengths": ["Good"],
            "weaknesses": ["Missing concept"],
            "recommendations": ["Add question"],
            "overall_quality": "good",
        }
        mock_parse.return_value = feedback

        result = reflect_on_qa_pairs(
            mock_client, "test-model", qa_pairs, "text", "description"
        )

        assert result == feedback
        mock_create_prompt.assert_called_once_with(qa_pairs, "text", "description")
        mock_call_ai.assert_called_once()
        mock_parse.assert_called_once_with("feedback response")


class TestImproveQaPairs:
    """Tests for improve_qa_pairs function."""

    @patch("anything2anki.workflow.generate_qa_pairs")
    def test_improve_qa_pairs_success(self, mock_generate):
        """Test successful Q&A pair improvement."""
        mock_client = MagicMock()
        original_pairs = [{"question": "Q1", "answer": "A1"}]
        feedback = {
            "strengths": ["Good"],
            "weaknesses": ["Missing concept"],
            "recommendations": ["Add question"],
            "overall_quality": "good",
        }
        improved_pairs = [
            {"question": "Q1", "answer": "A1"},
            {"question": "Q2", "answer": "A2"},
        ]
        mock_generate.return_value = improved_pairs

        result = improve_qa_pairs(
            mock_client,
            "test-model",
            original_pairs,
            feedback,
            "text",
            "description",
        )

        assert result == improved_pairs
        mock_generate.assert_called_once_with(
            mock_client,
            "test-model",
            "text",
            "description",
            {"qa_pairs": original_pairs, "feedback": feedback},
        )


class TestGenerateAnkiCardsIntegration:
    """Integration tests for generate_anki_cards function."""

    @patch("anything2anki.workflow.ai.Client")
    @patch("anything2anki.workflow.write_anki_package")
    @patch("anything2anki.workflow.build_anki_deck")
    @patch("anything2anki.workflow.generate_md_report")
    @patch("anything2anki.workflow.improve_qa_pairs")
    @patch("anything2anki.workflow.reflect_on_qa_pairs")
    @patch("anything2anki.workflow.generate_qa_pairs")
    def test_generate_anki_cards_full_flow(
        self,
        mock_generate_qa,
        mock_reflect,
        mock_improve,
        mock_md_report,
        mock_build_deck,
        mock_write_pkg,
        mock_client_class,
        tmp_path,
    ):
        """Test full workflow integration with reflection pattern."""
        # Setup
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content", encoding="utf-8")

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        qa_pairs_v1 = [
            {"question": "Q1", "answer": "A1"},
            {"question": "Q2", "answer": "A2"},
        ]
        feedback = {
            "strengths": ["Clear questions"],
            "weaknesses": ["Could be more comprehensive"],
            "recommendations": ["Add more details"],
            "overall_quality": "good",
        }
        qa_pairs_v2 = [
            {"question": "Q1", "answer": "A1 improved"},
            {"question": "Q2", "answer": "A2 improved"},
        ]

        mock_generate_qa.return_value = qa_pairs_v1
        mock_reflect.return_value = feedback
        mock_improve.return_value = qa_pairs_v2

        mock_md_report.return_value = str(tmp_path / "deck.md")
        mock_deck = MagicMock()
        mock_deck.notes = [MagicMock(), MagicMock()]
        mock_build_deck.return_value = (MagicMock(), mock_deck)

        output_path = str(tmp_path / "deck.apkg")

        # Execute
        generate_anki_cards(
            str(test_file),
            "test description",
            output_path,
            "test-model",
            max_reflections=1,
        )

        # Verify
        mock_generate_qa.assert_called_once()
        mock_reflect.assert_called_once()
        mock_improve.assert_called_once()
        mock_md_report.assert_called_once_with(qa_pairs_v2, output_path)
        mock_build_deck.assert_called_once_with(qa_pairs_v2)
        mock_write_pkg.assert_called_once()

    @patch("anything2anki.workflow.ai.Client")
    @patch("anything2anki.workflow.write_anki_package")
    @patch("anything2anki.workflow.build_anki_deck")
    @patch("anything2anki.workflow.generate_md_report")
    @patch("anything2anki.workflow.generate_qa_pairs")
    def test_generate_anki_cards_no_reflections(
        self,
        mock_generate_qa,
        mock_md_report,
        mock_build_deck,
        mock_write_pkg,
        mock_client_class,
        tmp_path,
    ):
        """Test workflow with max_reflections=0 skips reflection."""
        # Setup
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content", encoding="utf-8")

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        qa_pairs = [
            {"question": "Q1", "answer": "A1"},
            {"question": "Q2", "answer": "A2"},
        ]
        mock_generate_qa.return_value = qa_pairs

        mock_md_report.return_value = str(tmp_path / "deck.md")
        mock_deck = MagicMock()
        mock_deck.notes = [MagicMock(), MagicMock()]
        mock_build_deck.return_value = (MagicMock(), mock_deck)

        output_path = str(tmp_path / "deck.apkg")

        # Execute with max_reflections=0
        generate_anki_cards(
            str(test_file),
            "test description",
            output_path,
            "test-model",
            max_reflections=0,
        )

        # Verify: no reflection or improvement calls
        mock_generate_qa.assert_called_once()
        mock_md_report.assert_called_once_with(qa_pairs, output_path)
        mock_build_deck.assert_called_once_with(qa_pairs)
        mock_write_pkg.assert_called_once()

    def test_generate_anki_cards_file_not_found(self):
        """Test workflow with non-existent file."""
        with pytest.raises(FileNotFoundError):
            generate_anki_cards(
                "/nonexistent/file.txt",
                "test description",
                "/tmp/output.apkg",
            )

    @patch("anything2anki.workflow.ai.Client")
    @patch("anything2anki.workflow.generate_qa_pairs")
    def test_generate_anki_cards_empty_response(
        self, mock_generate, mock_client_class, tmp_path
    ):
        """Test workflow with empty AI response."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content", encoding="utf-8")

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_generate.return_value = []

        with pytest.raises(ValueError, match="No valid Q&A pairs found"):
            generate_anki_cards(
                str(test_file),
                "test description",
                str(tmp_path / "output.apkg"),
            )

    @patch("anything2anki.workflow.ai.Client")
    @patch("anything2anki.workflow.write_anki_package")
    @patch("anything2anki.workflow.build_anki_deck")
    @patch("anything2anki.workflow.generate_md_report")
    @patch("anything2anki.workflow.generate_qa_pairs")
    def test_generate_anki_cards_preview_only_flow(
        self,
        mock_generate_qa,
        mock_md_report,
        mock_build_deck,
        mock_write_pkg,
        mock_client_class,
        tmp_path,
    ):
        """Preview-only should generate MD and skip .apkg creation and deck build."""
        # Setup
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content", encoding="utf-8")

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        qa_pairs = [
            {"question": "Q1", "answer": "A1"},
        ]
        mock_generate_qa.return_value = qa_pairs

        mock_md_report.return_value = str(tmp_path / "deck.md")

        output_path = str(tmp_path / "deck.apkg")

        # Execute with preview_only=True
        generate_anki_cards(
            str(test_file),
            "test description",
            output_path,
            "test-model",
            preview_only=True,
        )

        # Verify: MD generated, deck not built, package not written
        mock_generate_qa.assert_called_once()
        mock_md_report.assert_called_once()
        mock_build_deck.assert_not_called()
        mock_write_pkg.assert_not_called()

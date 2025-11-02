"""Prompt templates for generating structured Q&A pairs from text."""

SYSTEM_PROMPT = """You are an expert at creating educational flashcards. 
Your task is to extract key information from text and create question-answer pairs 
that are suitable for spaced repetition learning.

Generate questions and answers that:
- Are clear and concise
- Test understanding of key concepts
- Cover important information from the text
- Are appropriate for memorization

Return your response as a JSON array of objects, where each object has:
- "question": The question text
- "answer": The answer text

Example format:
[
  {"question": "What is X?", "answer": "X is Y because Z."},
  {"question": "How does A work?", "answer": "A works by B and C."}
]"""


def create_user_prompt(text_content, learning_description):
    """Create a user prompt with the text content and learning description.

    Args:
        text_content: The text content to process.
        learning_description: Description of what to learn from the text.

    Returns:
        str: Formatted user prompt.
    """
    prompt = f"""Based on the following learning objective: "{learning_description}"

Please analyze the following text and generate relevant question-answer pairs:

{text_content}

Return ONLY a valid JSON array of objects with "question" and "answer" fields. 
Do not include any explanation or additional text outside the JSON."""
    return prompt

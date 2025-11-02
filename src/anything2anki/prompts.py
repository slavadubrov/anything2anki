"""Prompt templates for generating structured Q&A pairs from text."""

import json

GENERATION_PROMPT = """You are an expert at creating educational flashcards. 
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

REFLECTION_PROMPT = """You are an expert evaluator of educational flashcards.
Your task is to review question-answer pairs and provide constructive feedback 
on how to improve them for spaced repetition learning.

Evaluate the Q&A pairs based on these criteria:
- Completeness: Do they cover key concepts from the source text?
- Clarity: Are questions clear and answers concise?
- Accuracy: Are answers factually correct based on the source text?
- Educational value: Are pairs suitable for spaced repetition learning?
- Coverage: Are important topics adequately represented?

Provide specific, actionable feedback that identifies:
1. What is working well
2. What needs improvement
3. Specific suggestions for enhancement

Return your response as a JSON object with:
- "strengths": List of what works well
- "weaknesses": List of specific issues found
- "recommendations": List of specific improvement suggestions
- "overall_quality": Assessment string (e.g., "good", "needs improvement", "excellent")

Example format:
{
  "strengths": ["Clear questions", "Concise answers"],
  "weaknesses": ["Missing key concept X", "Answer too vague for question Y"],
  "recommendations": ["Add question about X", "Clarify answer Y with more detail"],
  "overall_quality": "needs improvement"
}"""

IMPROVEMENT_PROMPT = """You are an expert at creating educational flashcards.
Your task is to improve existing question-answer pairs based on feedback 
from a quality review.

You will receive:
- Original Q&A pairs
- Feedback with specific improvement suggestions
- The original source text
- The learning objective

Your job is to generate improved Q&A pairs that address the feedback while:
- Maintaining or enhancing clarity and conciseness
- Ensuring factual accuracy based on the source text
- Improving educational value for spaced repetition
- Covering all important concepts

Return your response as a JSON array of objects, where each object has:
- "question": The improved question text
- "answer": The improved answer text

Example format:
[
  {"question": "What is X?", "answer": "X is Y because Z."},
  {"question": "How does A work?", "answer": "A works by B and C."}
]"""


def create_user_prompt(text_content, learning_description, improvement_context=None):
    """Create a user prompt with the text content and learning description.

    Args:
        text_content: The text content to process.
        learning_description: Description of what to learn from the text.
        improvement_context: Optional dict with 'qa_pairs' and 'feedback' for improvement.

    Returns:
        str: Formatted user prompt.
    """
    if improvement_context:
        qa_pairs_json = json.dumps(improvement_context["qa_pairs"], indent=2)
        feedback_json = json.dumps(improvement_context["feedback"], indent=2)
        prompt = f"""Based on the following learning objective: "{learning_description}"

You are improving existing Q&A pairs based on feedback.

Original Q&A pairs:
{qa_pairs_json}

Feedback from review:
{feedback_json}

Original source text:
{text_content}

Please generate improved Q&A pairs that address the feedback while maintaining accuracy 
based on the source text.

Return ONLY a valid JSON array of objects with "question" and "answer" fields. 
Do not include any explanation or additional text outside the JSON."""
    else:
        prompt = f"""Based on the following learning objective: "{learning_description}"

Please analyze the following text and generate relevant question-answer pairs:

{text_content}

Return ONLY a valid JSON array of objects with "question" and "answer" fields. 
Do not include any explanation or additional text outside the JSON."""
    return prompt


def create_reflection_prompt(qa_pairs, text_content, learning_description):
    """Create a reflection prompt for reviewing Q&A pairs.

    Args:
        qa_pairs: List of dictionaries with "question" and "answer" keys.
        text_content: The original source text.
        learning_description: Description of what to learn from the text.

    Returns:
        str: Formatted reflection prompt.
    """
    qa_pairs_json = json.dumps(qa_pairs, indent=2)
    prompt = f"""Based on the following learning objective: "{learning_description}"

Please review the following Q&A pairs generated from this source text:

Source text:
{text_content}

Generated Q&A pairs:
{qa_pairs_json}

Evaluate these Q&A pairs and provide feedback on how to improve them.

Return ONLY a valid JSON object with "strengths", "weaknesses", "recommendations", 
and "overall_quality" fields. Do not include any explanation or additional text outside the JSON."""
    return prompt

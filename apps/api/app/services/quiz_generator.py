"""Quiz generator.

Returns 5 deterministic multiple-choice questions per topic. Stub that mirrors
the structure an LLM call would produce, so frontend code and grading can be
built and tested without spending LLM tokens.
"""

from __future__ import annotations

import hashlib
from typing import TypedDict

from pydantic import BaseModel

from app.services.curriculum import CurriculumTopic


class _QuestionTemplate(TypedDict):
    prompt: str
    options: list[str]
    correct_index: int
    explanation: str


PASSING_SCORE = 0.7
QUESTIONS_PER_QUIZ = 5


class QuizQuestion(BaseModel):
    index: int
    prompt: str
    options: list[str]
    correct_index: int
    explanation: str


class QuizQuestionPublic(BaseModel):
    """Quiz question as sent to the client — correct answers stripped."""

    index: int
    prompt: str
    options: list[str]


class Quiz(BaseModel):
    slug: str
    title: str
    phase: int
    phase_title: str
    passing_score: float
    questions: list[QuizQuestion]


_QUESTION_TEMPLATES: list[_QuestionTemplate] = [
    {
        "prompt": "Which statement best describes {title}?",
        "options": [
            "A core concept in {phase_title} that engineers use day to day.",
            "An obsolete technique nobody uses anymore.",
            "A type of database engine.",
            "A JavaScript framework.",
        ],
        "correct_index": 0,
        "explanation": (
            "{title} sits inside the {phase_title} phase of the curriculum — "
            "knowing where it fits in the workflow is the first thing an "
            "interviewer will check."
        ),
    },
    {
        "prompt": "When learning {title}, which order is most effective?",
        "options": [
            "Read the original paper end-to-end with no implementation.",
            "Build intuition → worked example → hands-on exercise → quiz.",
            "Memorize all formulas before writing any code.",
            "Skip the basics and jump to the most advanced version.",
        ],
        "correct_index": 1,
        "explanation": (
            "Mastery-based progression: build intuition, then a worked "
            "example, then practice, then a check. This is exactly how this "
            "platform teaches {title}."
        ),
    },
    {
        "prompt": "If your project requires {title}, what's the right first step?",
        "options": [
            "Optimize for production before you have a working prototype.",
            "Pick the simplest implementation that could possibly work, then measure.",
            "Wait until you fully understand every edge case.",
            "Avoid measuring — vibes are enough.",
        ],
        "correct_index": 1,
        "explanation": (
            "AI engineering rewards a measure-first loop. Ship the simplest "
            "thing, measure, optimize what your numbers flag."
        ),
    },
    {
        "prompt": "Which is a real failure mode to expect with {title} in production?",
        "options": [
            "It works equally well on every input distribution forever.",
            "Inputs that differ from training data degrade output quality.",
            "It cannot be monitored or logged.",
            "It never has latency or cost trade-offs.",
        ],
        "correct_index": 1,
        "explanation": (
            "Distribution shift is the single most common production issue "
            "across every AI engineering topic, including {title}."
        ),
    },
    {
        "prompt": "Why is {title} covered in the {phase_title} phase?",
        "options": [
            "Because it has nothing to do with the rest of the phase.",
            "Because mastering it unlocks the projects that define {phase_title}.",
            "Because it's an off-topic deep dive.",
            "By accident.",
        ],
        "correct_index": 1,
        "explanation": (
            "Every topic in {phase_title} maps to a specific capability you "
            "need to ship that phase's project."
        ),
    },
]


def _rotate_options(options: list[str], correct_index: int, seed: int) -> tuple[list[str], int]:
    """Deterministically rotate the option list so the correct answer isn't always first.

    Returns the new options and the new correct_index.
    """
    n = len(options)
    shift = seed % n
    rotated = options[-shift:] + options[:-shift] if shift else list(options)
    new_correct = (correct_index + shift) % n
    return rotated, new_correct


def generate_quiz(topic: CurriculumTopic) -> Quiz:
    """Return a deterministic quiz for the topic."""
    seed = int(hashlib.sha1(topic.slug.encode("utf-8")).hexdigest(), 16)
    questions: list[QuizQuestion] = []
    for i, tmpl in enumerate(_QUESTION_TEMPLATES[:QUESTIONS_PER_QUIZ]):
        prompt = tmpl["prompt"].format(title=topic.title, phase_title=topic.phase_title)
        raw_options = [
            o.format(title=topic.title, phase_title=topic.phase_title) for o in tmpl["options"]
        ]
        options, correct_index = _rotate_options(raw_options, tmpl["correct_index"], seed + i)
        questions.append(
            QuizQuestion(
                index=i,
                prompt=prompt,
                options=options,
                correct_index=correct_index,
                explanation=tmpl["explanation"].format(
                    title=topic.title, phase_title=topic.phase_title
                ),
            )
        )
    return Quiz(
        slug=topic.slug,
        title=topic.title,
        phase=topic.phase,
        phase_title=topic.phase_title,
        passing_score=PASSING_SCORE,
        questions=questions,
    )

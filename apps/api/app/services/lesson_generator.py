"""Lesson content generator.

Returns deterministic lesson content (beginner + advanced explanations, worked
example, key points) for any topic in the curriculum. This is the stub the AI
Tutor agent will replace once LLM calls are wired in; the function signature
stays the same so the swap-in is a one-line change.
"""

from __future__ import annotations

from pydantic import BaseModel

from app.services.curriculum import CurriculumTopic


class Lesson(BaseModel):
    slug: str
    title: str
    phase: int
    phase_title: str
    beginner_explanation: str
    advanced_explanation: str
    worked_example: str
    key_points: list[str]
    estimated_minutes: int


_BEGINNER_TEMPLATE = (
    "{title} is a core concept in {phase_title}. Think of it as a building "
    "block: small enough to learn in one sitting, important enough that "
    "you'll use it on every AI engineering project. In this lesson we'll "
    "build intuition first, then look at a worked example, then test "
    "understanding with a short quiz."
)

_ADVANCED_TEMPLATE = (
    "At a deeper level, {title} ties into the broader {phase_title} workflow: "
    "where it sits in the data/model pipeline, what its asymptotic / numerical "
    "properties are, and what failure modes you should expect in production. "
    "The 'Key points' section captures the engineering-level facts you should "
    "be able to recall in an interview."
)

_EXAMPLE_TEMPLATE = (
    "Worked example: imagine you're building a system that requires {title}. "
    "Step 1 — define the input/output shape. Step 2 — pick the simplest "
    "implementation that could possibly work. Step 3 — measure (latency, "
    "accuracy, cost). Step 4 — only optimize what your measurements flag. "
    "This same loop applies to every {phase_title} task."
)


def _key_points_for(topic: CurriculumTopic) -> list[str]:
    return [
        f"{topic.title} is part of the {topic.phase_title} phase of the AI Engineer curriculum.",
        f"You should be able to explain {topic.title} to a junior teammate in under 90 seconds.",
        (
            f"Common interview question: 'When would you reach for {topic.title} "
            "and when wouldn't you?'"
        ),
        "Hands-on practice matters more than reading — the quiz checks the engineering details.",
    ]


def generate_lesson(topic: CurriculumTopic) -> Lesson:
    """Return a deterministic lesson for the topic.

    Replace the bodies of this function with an LLM call (LangChain / OpenAI)
    once you're ready to spend tokens. The return shape stays the same.
    """
    return Lesson(
        slug=topic.slug,
        title=topic.title,
        phase=topic.phase,
        phase_title=topic.phase_title,
        beginner_explanation=_BEGINNER_TEMPLATE.format(
            title=topic.title, phase_title=topic.phase_title
        ),
        advanced_explanation=_ADVANCED_TEMPLATE.format(
            title=topic.title, phase_title=topic.phase_title
        ),
        worked_example=_EXAMPLE_TEMPLATE.format(
            title=topic.title, phase_title=topic.phase_title
        ),
        key_points=_key_points_for(topic),
        estimated_minutes=45,
    )

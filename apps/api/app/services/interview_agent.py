"""Interview Agent — viva-style mock interview per topic.

State lives on the ``interviews`` row as a JSON ``transcript`` list. Each turn
is one of three kinds:

* ``question`` — assistant prompts a question (with a 1-based ``index``).
* ``answer`` — user replies.
* ``feedback`` — assistant scores the answer (0–100) + writes a one-line
  reflection.

The agent itself is stateless: every method takes the current transcript and
returns the next turn(s). Persistence lives in the router.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Literal, TypedDict

from app.services.curriculum import CurriculumTopic
from app.services.llm import LLMClient, msg

logger = logging.getLogger(__name__)

TOTAL_QUESTIONS = 4
PASS_THRESHOLD = 70.0


TurnRole = Literal["assistant", "user"]
TurnKind = Literal["question", "answer", "feedback", "final"]


class Turn(TypedDict, total=False):
    role: TurnRole
    kind: TurnKind
    content: str
    index: int
    score: float


def _system_prompt(topic: CurriculumTopic) -> str:
    return (
        "You are a senior AI engineering interviewer running a short viva on the "
        f"topic '{topic.title}' (curriculum phase: {topic.phase_title}). Be concise, "
        "ask one clear question at a time, and stay focused on this topic. Do NOT "
        "ask the candidate to write code — this is a verbal interview."
    )


def _question_count(transcript: list[Turn]) -> int:
    return sum(1 for t in transcript if t.get("kind") == "question")


def _answer_count(transcript: list[Turn]) -> int:
    return sum(1 for t in transcript if t.get("kind") == "answer")


def generate_opening_question(llm: LLMClient, topic: CurriculumTopic) -> Turn:
    """Ask the LLM for an opening interview question."""
    prompt = (
        "[INTERVIEW_QUESTION]\n"
        f"<topic>{topic.title}</topic>\n"
        f"<index>1</index>\n"
        f"<phase>{topic.phase_title}</phase>\n"
        "Write a single opening interview question (1–2 sentences). Do not number it. "
        "Do not greet the candidate."
    )
    text = llm.chat(
        [msg("system", _system_prompt(topic)), msg("user", prompt)],
        temperature=0.6,
    )
    return {
        "role": "assistant",
        "kind": "question",
        "content": _clean(text),
        "index": 1,
    }


def grade_answer(
    llm: LLMClient,
    topic: CurriculumTopic,
    question: str,
    answer: str,
    question_index: int,
) -> Turn:
    """Score an answer 0–100 and write a one-sentence reflection."""
    prompt = (
        "[INTERVIEW_GRADE]\n"
        f"<topic>{topic.title}</topic>\n"
        f"<question>{question}</question>\n"
        f"<answer>{answer}</answer>\n"
        "Score the candidate's answer 0–100 against the question, considering correctness, "
        "depth, and production grounding. Reply with ONLY a JSON object of the form "
        '{"score": <int 0-100>, "feedback": "<one short sentence>"}.'
    )
    text = llm.chat(
        [msg("system", _system_prompt(topic)), msg("user", prompt)],
        json_mode=True,
        temperature=0.2,
    )
    score, feedback = _parse_score_json(text)
    return {
        "role": "assistant",
        "kind": "feedback",
        "content": feedback,
        "index": question_index,
        "score": score,
    }


def generate_followup_question(
    llm: LLMClient,
    topic: CurriculumTopic,
    transcript: list[Turn],
    next_index: int,
) -> Turn:
    """Generate the next interview question, taking the running transcript into account."""
    history = _format_history(transcript)
    prompt = (
        "[INTERVIEW_QUESTION]\n"
        f"<topic>{topic.title}</topic>\n"
        f"<index>{next_index}</index>\n"
        f"<phase>{topic.phase_title}</phase>\n"
        f"<history>{history}</history>\n"
        f"Write the next interview question (question {next_index} of {TOTAL_QUESTIONS}). "
        "Build on the candidate's previous answer if useful; otherwise pivot to a different "
        "angle of the topic. Reply with the question only — no numbering, no preamble."
    )
    text = llm.chat(
        [msg("system", _system_prompt(topic)), msg("user", prompt)],
        temperature=0.7,
    )
    return {
        "role": "assistant",
        "kind": "question",
        "content": _clean(text),
        "index": next_index,
    }


def finalize_interview(
    llm: LLMClient,
    topic: CurriculumTopic,
    transcript: list[Turn],
) -> tuple[float, str]:
    """Compute the final score (average of per-turn scores) and feedback summary."""
    per_turn = [float(t["score"]) for t in transcript if t.get("kind") == "feedback"]
    avg = round(sum(per_turn) / len(per_turn), 1) if per_turn else 0.0

    history = _format_history(transcript)
    prompt = (
        "[INTERVIEW_FINAL]\n"
        f"<topic>{topic.title}</topic>\n"
        f"<history>{history}</history>\n"
        f"<average_score>{avg}</average_score>\n"
        "Write a short paragraph (2–3 sentences) of overall feedback for the candidate. "
        "Reply with ONLY a JSON object of the form "
        '{"score": <int 0-100>, "feedback": "<paragraph>"}. '
        "The score field MUST equal the average_score above."
    )
    text = llm.chat(
        [msg("system", _system_prompt(topic)), msg("user", prompt)],
        json_mode=True,
        temperature=0.3,
    )
    _, feedback = _parse_score_json(text)
    return avg, feedback


def _format_history(transcript: list[Turn]) -> str:
    lines: list[str] = []
    for turn in transcript:
        kind = turn.get("kind")
        if kind == "question":
            lines.append(f"Q{turn.get('index')}: {turn.get('content', '')}")
        elif kind == "answer":
            lines.append(f"A{turn.get('index')}: {turn.get('content', '')}")
        elif kind == "feedback":
            lines.append(
                f"Grade Q{turn.get('index')}: "
                f"score={int(turn.get('score', 0))} — {turn.get('content', '')}"
            )
    return "\n".join(lines)


_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


def _parse_score_json(text: str) -> tuple[float, str]:
    """Extract ``score`` and ``feedback`` from the LLM's JSON response.

    Falls back to a regex sweep if the model returned malformed JSON.
    """
    stripped = _FENCE_RE.sub("", text).strip()
    try:
        data = json.loads(stripped)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", stripped, re.DOTALL)
        if match is None:
            logger.warning("LLM grade response had no JSON: %r", text)
            return 50.0, "Could not parse the grader output; defaulting to a neutral score."
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError:
            logger.warning("LLM grade response had invalid JSON: %r", text)
            return 50.0, "Could not parse the grader output; defaulting to a neutral score."

    score_raw = data.get("score", 0)
    try:
        score = float(score_raw)
    except (TypeError, ValueError):
        score = 0.0
    # Normalize: some models return 0–1 instead of 0–100.
    if 0 < score <= 1.0:
        score *= 100
    score = max(0.0, min(100.0, score))
    feedback_raw = data.get("feedback", "")
    feedback = str(feedback_raw).strip() or "No feedback returned."
    return round(score, 1), feedback


def _clean(text: str) -> str:
    """Trim whitespace and strip stray code fences."""
    return _FENCE_RE.sub("", text).strip()

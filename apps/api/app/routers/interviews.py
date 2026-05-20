"""Interview Agent endpoints — start a viva, post answers, fetch transcripts."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.models import Interview, InterviewKind, Topic, User
from app.routers.topics import _ensure_topic_row
from app.schemas import (
    InterviewAnswerIn,
    InterviewListEntry,
    InterviewListOut,
    InterviewOut,
    InterviewStartIn,
    InterviewTurnOut,
)
from app.services.curriculum import CurriculumTopic, get_topic
from app.services.interview_agent import (
    PASS_THRESHOLD,
    TOTAL_QUESTIONS,
    Turn,
    finalize_interview,
    generate_followup_question,
    generate_opening_question,
    grade_answer,
)
from app.services.llm import LLMClient, get_llm_client

router = APIRouter(prefix="/interviews", tags=["interviews"])


def _curriculum_for_interview(interview: Interview, topic_row: Topic | None) -> CurriculumTopic:
    """Resolve the curriculum topic that an interview was started on.

    Topic rows can technically be removed (cascade SET NULL); we fall back to
    the slug captured on the interview's transcript if needed.
    """
    if topic_row is not None:
        topic = get_topic(topic_row.slug)
        if topic is not None:
            return topic
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Topic for this interview is no longer in the curriculum.",
    )


def _transcript_as_turns(raw: list[dict[str, object]] | None) -> list[Turn]:
    return [Turn(**t) for t in (raw or [])]  # type: ignore[typeddict-item]


def _turns_as_json(turns: list[Turn]) -> list[dict[str, object]]:
    return [dict(t) for t in turns]


def _interview_state(interview: Interview, topic: CurriculumTopic) -> InterviewOut:
    transcript = _transcript_as_turns(interview.transcript)
    last_question = next(
        (t for t in reversed(transcript) if t.get("kind") == "question"), None
    )
    question_index = int(last_question.get("index", 0)) if last_question else 0
    finished = bool(any(t.get("kind") == "final" for t in transcript))

    return InterviewOut(
        id=interview.id,
        slug=topic.slug,
        title=topic.title,
        phase=topic.phase,
        phase_title=topic.phase_title,
        transcript=[
            InterviewTurnOut(
                role=t.get("role", "assistant"),
                kind=t.get("kind", "question"),
                content=str(t.get("content", "")),
                index=int(t.get("index", 0) or 0),
                score=(
                    float(t["score"])
                    if isinstance(t.get("score"), int | float)
                    else None
                ),
            )
            for t in transcript
        ],
        question_index=question_index,
        total_questions=TOTAL_QUESTIONS,
        finished=finished,
        score=interview.score,
        ai_feedback=interview.ai_feedback,
        passing_score=PASS_THRESHOLD,
        created_at=interview.created_at,
    )


@router.post("/start", response_model=InterviewOut, status_code=status.HTTP_201_CREATED)
def start_interview(
    body: InterviewStartIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    llm: LLMClient = Depends(get_llm_client),
) -> InterviewOut:
    """Create a fresh interview for the topic + ask the opening question."""
    topic = get_topic(body.slug)
    if topic is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown topic slug.")
    topic_row = _ensure_topic_row(db, topic)

    opening = generate_opening_question(llm, topic)
    interview = Interview(
        user_id=current_user.id,
        topic_id=topic_row.id,
        kind=InterviewKind.VIVA,
        transcript=_turns_as_json([opening]),
        score=None,
        ai_feedback=None,
    )
    db.add(interview)
    db.commit()
    db.refresh(interview)
    return _interview_state(interview, topic)


@router.post("/{interview_id}/answer", response_model=InterviewOut)
def post_answer(
    interview_id: uuid.UUID,
    body: InterviewAnswerIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    llm: LLMClient = Depends(get_llm_client),
) -> InterviewOut:
    interview = (
        db.query(Interview)
        .filter(Interview.id == interview_id, Interview.user_id == current_user.id)
        .first()
    )
    if interview is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found.")

    topic_row = db.query(Topic).filter(Topic.id == interview.topic_id).first()
    topic = _curriculum_for_interview(interview, topic_row)

    transcript = _transcript_as_turns(interview.transcript)
    if any(t.get("kind") == "final" for t in transcript):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Interview already finished.",
        )

    open_question = next(
        (t for t in reversed(transcript) if t.get("kind") == "question"), None
    )
    if open_question is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No open question to answer.",
        )
    # Disallow double-answering the same question.
    last_after_q = transcript[transcript.index(open_question) + 1 :]
    if any(t.get("kind") == "answer" for t in last_after_q):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Already answered the current question; wait for the next prompt.",
        )

    question_index = int(open_question.get("index", 1))
    answer_turn: Turn = {
        "role": "user",
        "kind": "answer",
        "content": body.answer,
        "index": question_index,
    }
    feedback_turn = grade_answer(
        llm,
        topic,
        str(open_question.get("content", "")),
        body.answer,
        question_index,
    )
    transcript.extend([answer_turn, feedback_turn])

    if question_index >= TOTAL_QUESTIONS:
        final_score, final_feedback = finalize_interview(llm, topic, transcript)
        final_turn: Turn = {
            "role": "assistant",
            "kind": "final",
            "content": final_feedback,
            "index": question_index,
            "score": final_score,
        }
        transcript.append(final_turn)
        interview.score = final_score
        interview.ai_feedback = final_feedback
    else:
        next_question = generate_followup_question(llm, topic, transcript, question_index + 1)
        transcript.append(next_question)

    interview.transcript = _turns_as_json(transcript)
    db.commit()
    db.refresh(interview)
    return _interview_state(interview, topic)


@router.get("/me", response_model=InterviewListOut)
def list_my_interviews(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> InterviewListOut:
    rows = (
        db.query(Interview)
        .filter(Interview.user_id == current_user.id)
        .order_by(Interview.created_at.desc())
        .all()
    )
    entries: list[InterviewListEntry] = []
    for interview in rows:
        topic_row = db.query(Topic).filter(Topic.id == interview.topic_id).first()
        if topic_row is None:
            continue
        topic = get_topic(topic_row.slug)
        if topic is None:
            continue
        finished = any(
            t.get("kind") == "final" for t in _transcript_as_turns(interview.transcript)
        )
        entries.append(
            InterviewListEntry(
                id=interview.id,
                slug=topic.slug,
                title=topic.title,
                phase=topic.phase,
                phase_title=topic.phase_title,
                finished=finished,
                score=interview.score,
                created_at=interview.created_at,
            )
        )
    return InterviewListOut(entries=entries)


@router.get("/{interview_id}", response_model=InterviewOut)
def get_interview(
    interview_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> InterviewOut:
    interview = (
        db.query(Interview)
        .filter(Interview.id == interview_id, Interview.user_id == current_user.id)
        .first()
    )
    if interview is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found.")
    topic_row = db.query(Topic).filter(Topic.id == interview.topic_id).first()
    topic = _curriculum_for_interview(interview, topic_row)
    return _interview_state(interview, topic)

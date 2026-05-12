"""Quiz endpoints."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.models import Topic, User, UserProgress
from app.routers.topics import _ensure_topic_row
from app.schemas import (
    QuizOut,
    QuizQuestionOut,
    QuizQuestionResult,
    QuizResult,
    QuizSubmitIn,
)
from app.services.curriculum import get_topic
from app.services.quiz_generator import generate_quiz

router = APIRouter(prefix="/quizzes", tags=["quizzes"])


@router.get("/{slug}", response_model=QuizOut)
def get_quiz(slug: str) -> QuizOut:
    """Return the quiz for a topic with correct answers stripped."""
    topic = get_topic(slug)
    if topic is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown topic slug.")
    quiz = generate_quiz(topic)
    return QuizOut(
        slug=quiz.slug,
        title=quiz.title,
        phase=quiz.phase,
        phase_title=quiz.phase_title,
        passing_score=quiz.passing_score,
        questions=[
            QuizQuestionOut(index=q.index, prompt=q.prompt, options=q.options)
            for q in quiz.questions
        ],
    )


@router.post("/{slug}/submit", response_model=QuizResult)
def submit_quiz(
    slug: str,
    body: QuizSubmitIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> QuizResult:
    topic = get_topic(slug)
    if topic is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown topic slug.")
    quiz = generate_quiz(topic)
    if len(body.answers) != len(quiz.questions):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Expected {len(quiz.questions)} answers, got {len(body.answers)}.",
        )

    per_question: list[QuizQuestionResult] = []
    correct = 0
    for q, picked in zip(quiz.questions, body.answers, strict=False):
        is_correct = picked == q.correct_index
        if is_correct:
            correct += 1
        per_question.append(
            QuizQuestionResult(
                index=q.index,
                correct=is_correct,
                correct_index=q.correct_index,
                explanation=q.explanation,
            )
        )
    score = correct / len(quiz.questions)
    passed = score >= quiz.passing_score

    topic_row: Topic = _ensure_topic_row(db, topic)
    progress = (
        db.query(UserProgress)
        .filter(UserProgress.user_id == current_user.id, UserProgress.topic_id == topic_row.id)
        .first()
    )
    if progress is None:
        progress = UserProgress(
            user_id=current_user.id,
            topic_id=topic_row.id,
            mastery_score=score,
            attempts=1,
            completed=passed,
            last_reviewed=datetime.now(UTC),
        )
        db.add(progress)
    else:
        progress.mastery_score = max(progress.mastery_score, score)
        progress.attempts += 1
        progress.last_reviewed = datetime.now(UTC)
        if passed:
            progress.completed = True
    db.commit()
    db.refresh(progress)

    return QuizResult(
        slug=slug,
        score=score,
        passed=passed,
        passing_score=quiz.passing_score,
        mastery_score=progress.mastery_score,
        attempts=progress.attempts,
        per_question=per_question,
    )

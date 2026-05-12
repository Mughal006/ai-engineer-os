"""Topic + lesson endpoints.

Topics live in the curriculum module (deterministic). The `topics` SQL table is
populated lazily on first reference, so we never have to maintain a parallel
seed script.
"""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.models import Topic, User, UserProgress
from app.schemas import CurriculumTopicOut, LessonCompleteOut, LessonOut
from app.services.curriculum import CurriculumTopic, get_topic, topics_index
from app.services.lesson_generator import generate_lesson

router = APIRouter(prefix="/topics", tags=["topics"])


def _ensure_topic_row(db: Session, curriculum_topic: CurriculumTopic) -> Topic:
    """Lazily create a `topics` row for the given curriculum topic and return it."""
    topic_row = db.query(Topic).filter(Topic.slug == curriculum_topic.slug).first()
    if topic_row is not None:
        return topic_row
    topic_row = Topic(
        slug=curriculum_topic.slug,
        title=curriculum_topic.title,
        phase=curriculum_topic.phase,
        prerequisites=[],
        summary=f"{curriculum_topic.title} — part of {curriculum_topic.phase_title}.",
    )
    db.add(topic_row)
    db.flush()
    return topic_row


@router.get("", response_model=list[CurriculumTopicOut])
def list_topics() -> list[CurriculumTopicOut]:
    """Return every curriculum topic across all phases."""
    return [
        CurriculumTopicOut(slug=t.slug, title=t.title, phase=t.phase, phase_title=t.phase_title)
        for t in topics_index().values()
    ]


@router.get("/{slug}", response_model=CurriculumTopicOut)
def get_topic_meta(slug: str) -> CurriculumTopicOut:
    topic = get_topic(slug)
    if topic is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown topic slug.")
    return CurriculumTopicOut(
        slug=topic.slug, title=topic.title, phase=topic.phase, phase_title=topic.phase_title
    )


@router.get("/{slug}/lesson", response_model=LessonOut)
def get_lesson(slug: str) -> LessonOut:
    topic = get_topic(slug)
    if topic is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown topic slug.")
    lesson = generate_lesson(topic)
    return LessonOut(**lesson.model_dump())


@router.post("/{slug}/complete", response_model=LessonCompleteOut)
def mark_lesson_complete(
    slug: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LessonCompleteOut:
    """Mark the topic as 'lesson read' for the current user.

    Does not affect mastery_score — that's owned by the quiz endpoint. Setting
    completed=True here is the equivalent of clicking 'Mark as read'.
    """
    topic = get_topic(slug)
    if topic is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown topic slug.")
    topic_row = _ensure_topic_row(db, topic)

    progress = (
        db.query(UserProgress)
        .filter(UserProgress.user_id == current_user.id, UserProgress.topic_id == topic_row.id)
        .first()
    )
    if progress is None:
        progress = UserProgress(
            user_id=current_user.id,
            topic_id=topic_row.id,
            mastery_score=0.0,
            attempts=0,
            completed=True,
            last_reviewed=datetime.now(UTC),
        )
        db.add(progress)
    else:
        progress.completed = True
        progress.last_reviewed = datetime.now(UTC)
    db.commit()
    db.refresh(progress)
    return LessonCompleteOut(
        slug=slug,
        completed=progress.completed,
        mastery_score=progress.mastery_score,
        attempts=progress.attempts,
    )

"""Progress endpoints — what topics the current user has completed."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.models import Topic, User, UserProgress
from app.schemas import ProgressEntry, ProgressOut
from app.services.curriculum import get_topic, topics_index

router = APIRouter(prefix="/progress", tags=["progress"])


@router.get("/me", response_model=ProgressOut)
def get_my_progress(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProgressOut:
    """Return the current user's progress across the entire curriculum."""
    rows = (
        db.query(UserProgress, Topic)
        .join(Topic, Topic.id == UserProgress.topic_id)
        .filter(UserProgress.user_id == current_user.id)
        .all()
    )
    entries: list[ProgressEntry] = []
    completed = 0
    for progress, topic_row in rows:
        curriculum_topic = get_topic(topic_row.slug)
        if curriculum_topic is None:
            continue
        if progress.completed:
            completed += 1
        entries.append(
            ProgressEntry(
                slug=topic_row.slug,
                title=curriculum_topic.title,
                phase=curriculum_topic.phase,
                phase_title=curriculum_topic.phase_title,
                completed=progress.completed,
                mastery_score=progress.mastery_score,
                attempts=progress.attempts,
                last_reviewed=progress.last_reviewed,
            )
        )
    total = len(topics_index())
    pct = (completed / total) * 100.0 if total else 0.0
    return ProgressOut(
        entries=entries,
        total_topics=total,
        completed_topics=completed,
        completion_percentage=pct,
    )
